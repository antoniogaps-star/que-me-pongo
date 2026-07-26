import 'dart:io';

import 'package:drift/drift.dart';
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';

import '../../data/local/database.dart';

/// Las categorías del clóset, con su nombre bonito y su ícono.
const categorias = <String, String>{
  'arriba': 'Parte de arriba',
  'abajo': 'Parte de abajo',
  'abrigo': 'Abrigo',
  'calzado': 'Calzado',
  'accesorio': 'Accesorio',
  'completo': 'Conjunto completo',
};

/// Los 10 estilos del PRD.
const estilos = <String>[
  'casual',
  'moderno',
  'clasico',
  'rockero',
  'deportivo',
  'elegante',
  'streetwear',
  'ranchero',
  'ejecutivo',
  'minimalista',
];

const temporadas = <String, String>{
  'todo': 'Todo el año',
  'calor': 'Para calor',
  'frio': 'Para frío',
};

/// El clóset: prendas guardadas en la base local cifrada. La foto vive como archivo
/// aparte en la carpeta de la app; en la base solo se guarda su ruta.
class ClosetRepository {
  ClosetRepository(this._db, this._tenantId);

  final AppDatabase _db;
  final Future<String?> _tenantId;
  static const _uuid = Uuid();

  Stream<List<Garment>> watch() => _db.watchGarments();

  Future<List<Garment>> list() => _db.activeGarments();

  Future<Garment?> byId(String id) => _db.garmentById(id);

  /// Copia la foto tomada a la carpeta permanente de la app.
  ///
  /// La cámara deja el archivo en una carpeta temporal que el sistema puede vaciar
  /// cuando quiera; si guardáramos esa ruta, las fotos del clóset desaparecerían solas.
  Future<String> guardarFoto(File original, String garmentId) async {
    final dir = await getApplicationDocumentsDirectory();
    final destino = Directory('${dir.path}/prendas');
    if (!destino.existsSync()) destino.createSync(recursive: true);
    final archivo = File('${destino.path}/$garmentId.jpg');
    await original.copy(archivo.path);
    return archivo.path;
  }

  Future<String> add({
    required String category,
    required String name,
    String? color,
    List<String> styles = const [],
    int formality = 5,
    String season = 'todo',
    File? foto,
  }) async {
    final id = _uuid.v7();
    final tenant = await _tenantId ?? '';
    final ruta = foto == null ? null : await guardarFoto(foto, id);

    await _db.into(_db.garments).insert(
          GarmentsCompanion.insert(
            id: id,
            tenantId: tenant,
            category: category,
            name: name,
            color: Value(color),
            styles: Value(styles.join(',')),
            formality: Value(formality),
            season: Value(season),
            photoPath: Value(ruta),
          ),
        );
    return id;
  }

  /// Borrado suave: se marca como eliminada para que el borrado viaje al servidor.
  /// La foto sí se borra de una vez — ocupa espacio y ya no sirve de nada.
  Future<void> remove(String id) async {
    final prenda = await _db.garmentById(id);
    if (prenda?.photoPath != null) {
      final archivo = File(prenda!.photoPath!);
      if (archivo.existsSync()) {
        try {
          await archivo.delete();
        } on FileSystemException {
          // Si el archivo está bloqueado, no vale la pena romper el borrado.
        }
      }
    }
    await (_db.update(_db.garments)..where((g) => g.id.equals(id))).write(
      GarmentsCompanion(
        isDeleted: const Value(true),
        isDirty: const Value(true),
        photoPath: const Value(null),
        updatedAt: Value(DateTime.now()),
        version: Value((prenda?.version ?? 1) + 1),
      ),
    );
  }
}
