import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';

/// Un conjunto propuesto por el asesor.
class Sugerencia {
  const Sugerencia({
    required this.garmentIds,
    required this.explicacion,
    required this.imagenProyectada,
  });

  final List<String> garmentIds;
  final String explicacion;
  final String imagenProyectada;
}

/// La respuesta completa: los conjuntos y de dónde salieron.
class Recomendacion {
  const Recomendacion({required this.outfits, required this.fuente});

  final List<Sugerencia> outfits;

  /// "claude" cuando lo armó la IA; "reglas" cuando fue el motor local (sin internet
  /// o sin cupo). La pantalla lo usa para ser honesta con el usuario.
  final String fuente;

  bool get vieneDeIA => fuente == 'claude';
}

/// La ficha que la IA leyó de la foto de una prenda.
class FichaPrenda {
  const FichaPrenda({
    required this.categoria,
    required this.nombre,
    required this.color,
    required this.estilos,
    required this.formalidad,
    required this.temporada,
  });

  final String categoria;
  final String nombre;
  final String color;
  final List<String> estilos;
  final int formalidad;
  final String temporada;
}

/// No se pudo leer la foto (sin internet, sin cupo de IA o sin llave configurada).
class SinAsesorException implements Exception {
  const SinAsesorException(this.mensaje);
  final String mensaje;
  @override
  String toString() => mensaje;
}

/// Habla con el asesor del servidor.
class AdvisorApi {
  AdvisorApi(this._dio);

  final Dio _dio;

  /// Manda la foto de una prenda y devuelve su ficha para que el usuario la confirme.
  Future<FichaPrenda> clasificar(File foto) async {
    try {
      final bytes = await foto.readAsBytes();
      final response = await _dio.post<Map<String, dynamic>>(
        '/advisor/classify',
        data: {
          'image_base64': base64Encode(bytes),
          'media_type': 'image/jpeg',
        },
      );
      final d = response.data!;
      return FichaPrenda(
        categoria: d['category'] as String,
        nombre: d['name'] as String,
        color: d['color'] as String? ?? '',
        estilos: (d['styles'] as List? ?? []).cast<String>(),
        formalidad: d['formality'] as int? ?? 5,
        temporada: d['season'] as String? ?? 'todo',
      );
    } on DioException catch (e) {
      throw SinAsesorException(_mensajeDeError(e));
    }
  }

  /// El botón estrella. Devuelve los conjuntos con su explicación.
  Future<Recomendacion> recomendar({
    String ocasion = 'dia normal',
    String proyeccion = '',
    double? temperaturaC,
    String? conPrendaId,
    bool sorpresa = false,
    int cuantos = 1,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/advisor/recommend',
      data: {
        'occasion': ocasion,
        'projection': proyeccion,
        if (temperaturaC != null) 'temperature_c': temperaturaC,
        if (conPrendaId != null) 'with_garment_id': conPrendaId,
        'surprise': sorpresa,
        'count': cuantos,
      },
    );
    final d = response.data!;
    return Recomendacion(
      fuente: d['source'] as String? ?? 'reglas',
      outfits: [
        for (final o in (d['outfits'] as List? ?? []).cast<Map<String, dynamic>>())
          Sugerencia(
            garmentIds: (o['garment_ids'] as List? ?? []).cast<String>(),
            explicacion: o['explanation'] as String? ?? '',
            imagenProyectada: o['projected_image'] as String? ?? '',
          ),
      ],
    );
  }

  String _mensajeDeError(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['error'] is Map) {
      final msg = data['error']['message'];
      if (msg is String && msg.isNotEmpty) return msg;
    }
    return 'No pude analizar la foto ahora. Captura los datos a mano y sigue adelante.';
  }
}
