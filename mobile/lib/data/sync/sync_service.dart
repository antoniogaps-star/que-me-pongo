import 'package:dio/dio.dart';
import 'package:drift/drift.dart';

import '../local/database.dart';

/// El servidor rechazó la subida (HTTP 402) porque la prueba gratis o el plan venció.
/// Los cambios locales quedan intactos y se subirán al reactivar. La UI la distingue de
/// un fallo de red para mostrar "renueva tu plan" en vez de "sin conexión".
class SubscriptionExpiredException implements Exception {
  const SubscriptionExpiredException(this.message);
  final String message;
  @override
  String toString() => message;
}

/// Motor de sincronización (patrón outbox): sube los cambios locales pendientes del
/// clóset y de los favoritos, y aplica los del servidor.
///
/// Las FOTOS no viajan: `photoPath` apunta a un archivo de este teléfono. Al respaldar
/// solo la ficha, el clóset se recupera al reinstalar aunque las fotos haya que
/// volver a tomarlas.
class SyncService {
  SyncService(this._db, this._dio);

  final AppDatabase _db;
  final Dio _dio;

  Future<void> push() async {
    final garments = await _db.dirtyGarments();
    final outfits = await _db.dirtyOutfits();

    final changes = <Map<String, dynamic>>[
      for (final g in garments)
        {
          'entity': 'garment',
          'id': g.id,
          'op': g.isDeleted ? 'delete' : 'upsert',
          'version': g.version,
          'updated_at': g.updatedAt.toUtc().toIso8601String(),
          'data': {
            'category': g.category,
            'name': g.name,
            'color': g.color,
            'styles': g.styles,
            'formality': g.formality,
            'season': g.season,
          },
        },
      for (final o in outfits)
        {
          'entity': 'outfit',
          'id': o.id,
          'op': o.isDeleted ? 'delete' : 'upsert',
          'version': o.version,
          'updated_at': o.updatedAt.toUtc().toIso8601String(),
          'data': {
            'garment_ids': o.garmentIds,
            'occasion': o.occasion,
            'projection': o.projection,
            'explanation': o.explanation,
          },
        },
    ];

    if (changes.isEmpty) return;

    final Response<dynamic> response;
    try {
      response = await _dio.post('/sync/push', data: {'changes': changes});
    } on DioException catch (e) {
      if (e.response?.statusCode == 402) {
        final data = e.response?.data;
        final msg = data is Map
            ? (data['error'] is Map ? data['error']['message'] as String? : null)
            : null;
        throw SubscriptionExpiredException(
          msg ?? 'Tu prueba o plan venció. Renueva para volver a sincronizar.',
        );
      }
      rethrow;
    }
    final results = (response.data['results'] as List).cast<Map<String, dynamic>>();

    for (final r in results) {
      if (r['status'] != 'applied') continue;
      final id = r['id'] as String;
      switch (r['entity']) {
        case 'garment':
          await _db.markGarmentSynced(id);
        case 'outfit':
          await _db.markOutfitSynced(id);
      }
    }
  }

  Future<void> pull() async {
    final response = await _dio.get('/sync/pull');
    final changes = (response.data['changes'] as List).cast<Map<String, dynamic>>();
    for (final change in changes) {
      await _applyRemote(change);
    }
  }

  Future<void> _applyRemote(Map<String, dynamic> change) async {
    final id = change['id'] as String;
    final data = (change['data'] as Map?)?.cast<String, dynamic>() ?? {};
    final tenantId = change['tenant_id'] as String? ?? '';
    final deleted = change['op'] == 'delete';
    switch (change['entity']) {
      case 'garment':
        // La foto local NO se toca: el servidor no la conoce y sobrescribirla con
        // null borraría la imagen que el usuario ya tiene en su teléfono.
        final existing = await _db.garmentById(id);
        await _db.into(_db.garments).insertOnConflictUpdate(
              GarmentsCompanion.insert(
                id: id,
                tenantId: tenantId,
                category: data['category'] as String? ?? 'arriba',
                name: data['name'] as String? ?? '',
                color: Value(data['color'] as String?),
                styles: Value(data['styles'] as String? ?? ''),
                formality: Value(data['formality'] as int? ?? 5),
                season: Value(data['season'] as String? ?? 'todo'),
                photoPath: Value(existing?.photoPath),
                isDeleted: Value(deleted),
                isDirty: const Value(false),
              ),
            );
      case 'outfit':
        await _db.into(_db.outfits).insertOnConflictUpdate(
              OutfitsCompanion.insert(
                id: id,
                tenantId: tenantId,
                garmentIds: Value(data['garment_ids'] as String? ?? ''),
                occasion: Value(data['occasion'] as String? ?? ''),
                projection: Value(data['projection'] as String? ?? ''),
                explanation: Value(data['explanation'] as String? ?? ''),
                isDeleted: Value(deleted),
                isDirty: const Value(false),
              ),
            );
    }
  }
}
