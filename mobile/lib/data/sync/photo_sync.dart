import 'dart:io';

import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

import '../local/database.dart';

/// Respaldo de las fotos del clóset: las sube y las recupera.
///
/// Va **aparte** del motor de sincronización normal a propósito. Una foto pesa mil veces
/// más que la ficha de una prenda: si viajaran juntas, en una red mala la imagen
/// detendría la sincronización de todo lo demás. Aquí, si una foto falla, el resto del
/// clóset ya se guardó y esa foto se reintenta la próxima vez.
class PhotoSync {
  PhotoSync(this._db, this._dio);

  final AppDatabase _db;
  final Dio _dio;

  /// Sube lo que falte y baja lo que no esté en este teléfono.
  ///
  /// Nunca lanza excepción: es un extra. Si no hay internet, las fotos siguen en el
  /// celular y se respaldan después.
  Future<void> sincronizar() async {
    try {
      await subirPendientes();
      await bajarFaltantes();
    } catch (_) {
      // Sin red o servidor dormido: se reintenta en la próxima sincronización.
    }
  }

  /// Sube las fotos que están en el teléfono y aún no en el servidor.
  Future<void> subirPendientes() async {
    for (final prenda in await _db.garmentsWithPendingPhoto()) {
      final archivo = File(prenda.photoPath!);
      // Si el usuario borró el archivo por fuera, no tiene caso reintentar por siempre.
      if (!archivo.existsSync()) {
        await _db.setGarmentPhoto(prenda.id, null, synced: false);
        continue;
      }
      try {
        final datos = FormData.fromMap({
          'archivo': await MultipartFile.fromFile(
            archivo.path,
            filename: '${prenda.id}.jpg',
            contentType: DioMediaType('image', 'jpeg'),
          ),
        });
        await _dio.put('/garments/${prenda.id}/foto', data: datos);
        await _db.setGarmentPhoto(prenda.id, prenda.photoPath, synced: true);
      } on DioException catch (e) {
        // 404 = la prenda todavía no llegó al servidor; se sube en la próxima vuelta.
        // 413/415 = esa imagen nunca va a ser aceptada: no insistir eternamente.
        final codigo = e.response?.statusCode;
        if (codigo == 413 || codigo == 415) {
          await _db.setGarmentPhoto(prenda.id, prenda.photoPath, synced: true);
        }
      }
    }
  }

  /// Baja las fotos de las prendas que en este teléfono no tienen imagen.
  ///
  /// Es lo que hace que al cambiar de celular el clóset se recupere COMPLETO, y no una
  /// lista de nombres sin rostro.
  Future<void> bajarFaltantes() async {
    final sinFoto = await _db.garmentsWithoutPhoto();
    if (sinFoto.isEmpty) return;

    // Una sola petición para saber qué hay respaldado, en vez de una por prenda.
    final respuesta = await _dio.get('/garments/fotos');
    final respaldadas = (respuesta.data as List).cast<String>().toSet();

    final dir = await getApplicationDocumentsDirectory();
    final destino = Directory('${dir.path}/prendas');
    if (!destino.existsSync()) destino.createSync(recursive: true);

    for (final prenda in sinFoto) {
      if (!respaldadas.contains(prenda.id)) continue;
      try {
        final imagen = await _dio.get<List<int>>(
          '/garments/${prenda.id}/foto',
          options: Options(responseType: ResponseType.bytes),
        );
        final archivo = File('${destino.path}/${prenda.id}.jpg');
        await archivo.writeAsBytes(imagen.data ?? const []);
        await _db.setGarmentPhoto(prenda.id, archivo.path, synced: true);
      } on DioException {
        // Esa foto se baja la próxima vez; las demás siguen su camino.
        continue;
      }
    }
  }
}
