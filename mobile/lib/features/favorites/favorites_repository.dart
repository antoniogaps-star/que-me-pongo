import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../../data/local/database.dart';

/// Los outfits que el usuario marcó con ⭐. Sirven para dos cosas: volver a verlos, y
/// que el modo sorpresa sepa qué combinaciones ya usa para proponerle algo distinto.
class FavoritesRepository {
  FavoritesRepository(this._db, this._tenantId);

  final AppDatabase _db;
  final Future<String?> _tenantId;
  static const _uuid = Uuid();

  Stream<List<Outfit>> watch() => _db.watchOutfits();

  Future<void> guardar({
    required List<String> garmentIds,
    required String ocasion,
    required String proyeccion,
    required String explicacion,
  }) async {
    final tenant = await _tenantId ?? '';
    await _db.into(_db.outfits).insert(
          OutfitsCompanion.insert(
            id: _uuid.v7(),
            tenantId: tenant,
            garmentIds: Value(garmentIds.join(',')),
            occasion: Value(ocasion),
            projection: Value(proyeccion),
            explanation: Value(explicacion),
          ),
        );
  }

  Future<void> quitar(String id) async {
    final actual = await (_db.select(_db.outfits)..where((o) => o.id.equals(id)))
        .getSingleOrNull();
    await (_db.update(_db.outfits)..where((o) => o.id.equals(id))).write(
      OutfitsCompanion(
        isDeleted: const Value(true),
        isDirty: const Value(true),
        updatedAt: Value(DateTime.now()),
        version: Value((actual?.version ?? 1) + 1),
      ),
    );
  }
}
