import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sqlcipher_flutter_libs/sqlcipher_flutter_libs.dart';
import 'package:sqlite3/open.dart';

import '../../core/secure_store.dart';

part 'database.g.dart';

/// Columnas de sincronización comunes: tombstone, versión, timestamp y el flag local
/// isDirty (cola outbox).
mixin _SyncColumns on Table {
  BoolColumn get isDeleted => boolean().withDefault(const Constant(false))();
  IntColumn get version => integer().withDefault(const Constant(1))();
  DateTimeColumn get updatedAt => dateTime().withDefault(currentDateAndTime)();
  BoolColumn get isDirty => boolean().withDefault(const Constant(true))();
}

/// Una prenda del clóset: ropa, calzado o accesorio.
///
/// La FOTO se queda en el teléfono (`photoPath`): al servidor solo viaja la ficha.
/// Así el clóset es privado y la app funciona sin depender de subir imágenes.
class Garments extends Table with _SyncColumns {
  TextColumn get id => text()(); // UUIDv7 de cliente
  TextColumn get tenantId => text()();

  /// arriba | abajo | abrigo | calzado | accesorio | completo
  TextColumn get category => text()();
  TextColumn get name => text()();
  TextColumn get color => text().nullable()();

  /// Estilos separados por coma: "casual,moderno".
  TextColumn get styles => text().withDefault(const Constant(''))();

  /// Qué tan formal es, del 1 al 10. Es lo que evita ponerte tenis en una boda.
  IntColumn get formality => integer().withDefault(const Constant(5))();

  /// todo | calor | frio
  TextColumn get season => text().withDefault(const Constant('todo'))();

  /// Ruta del archivo de la foto EN ESTE TELÉFONO. La ruta no se sincroniza (no
  /// significaría nada en otro aparato); los bytes sí se respaldan aparte.
  TextColumn get photoPath => text().nullable()();

  /// ¿La foto ya está respaldada en el servidor?
  ///
  /// Se sube aparte de la ficha y en su propio momento: una imagen pesa mil veces más
  /// que los datos de la prenda, y en una red mala no puede detener la sincronización
  /// de todo lo demás.
  BoolColumn get photoSynced => boolean().withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {id};
}

/// Un outfit guardado como favorito, con la explicación que dio el asesor.
class Outfits extends Table with _SyncColumns {
  TextColumn get id => text()();
  TextColumn get tenantId => text()();

  /// IDs de las prendas, separados por coma y en el orden del conjunto.
  TextColumn get garmentIds => text().withDefault(const Constant(''))();
  TextColumn get occasion => text().withDefault(const Constant(''))();
  TextColumn get projection => text().withDefault(const Constant(''))();
  TextColumn get explanation => text().withDefault(const Constant(''))();

  @override
  Set<Column> get primaryKey => {id};
}

@DriftDatabase(tables: [Garments, Outfits])
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? executor]) : super(executor ?? NativeDatabase.memory());
  AppDatabase.encrypted(SecureStore store) : super(_openEncrypted(store));

  @override
  int get schemaVersion => 2;

  /// Actualización de la base LOCAL en teléfonos que ya tienen la app instalada.
  ///
  /// Sin esto, al abrir la versión nueva Drift encuentra la tabla sin la columna y
  /// revienta: el usuario perdería el acceso a su clóset.
  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) => m.createAll(),
        onUpgrade: (m, from, to) async {
          if (from < 2) {
            await m.addColumn(garments, garments.photoSynced);
          }
        },
      );

  // ── Clóset ─────────────────────────────────────────────────
  /// Prendas con foto en el teléfono que todavía no está respaldada.
  Future<List<Garment>> garmentsWithPendingPhoto() => (select(garments)
        ..where((g) => g.photoPath.isNotNull() & g.photoSynced.equals(false)))
      .get();

  /// Prendas SIN foto local: candidatas a bajarla del respaldo.
  Future<List<Garment>> garmentsWithoutPhoto() => (select(garments)
        ..where((g) => g.photoPath.isNull() & g.isDeleted.equals(false)))
      .get();

  Future<void> setGarmentPhoto(String id, String? ruta, {required bool synced}) =>
      (update(garments)..where((g) => g.id.equals(id))).write(
        GarmentsCompanion(photoPath: Value(ruta), photoSynced: Value(synced)),
      );
  Future<List<Garment>> activeGarments() => (select(garments)
        ..where((g) => g.isDeleted.equals(false))
        ..orderBy([(g) => OrderingTerm(expression: g.name)]))
      .get();

  /// El clóset en vivo: la cuadrícula se actualiza sola al agregar o borrar.
  Stream<List<Garment>> watchGarments() => (select(garments)
        ..where((g) => g.isDeleted.equals(false))
        ..orderBy([(g) => OrderingTerm(expression: g.name)]))
      .watch();

  Future<Garment?> garmentById(String id) =>
      (select(garments)..where((g) => g.id.equals(id))).getSingleOrNull();

  // ── Favoritos ──────────────────────────────────────────────
  Stream<List<Outfit>> watchOutfits() => (select(outfits)
        ..where((o) => o.isDeleted.equals(false))
        ..orderBy([(o) => OrderingTerm(expression: o.updatedAt, mode: OrderingMode.desc)]))
      .watch();

  Future<List<Outfit>> activeOutfits() => (select(outfits)
        ..where((o) => o.isDeleted.equals(false))
        ..orderBy([(o) => OrderingTerm(expression: o.updatedAt, mode: OrderingMode.desc)]))
      .get();

  // ── Cola outbox (pendientes de subir) ──────────────────────
  Future<List<Garment>> dirtyGarments() =>
      (select(garments)..where((g) => g.isDirty.equals(true))).get();
  Future<List<Outfit>> dirtyOutfits() =>
      (select(outfits)..where((o) => o.isDirty.equals(true))).get();

  Future<void> markGarmentSynced(String id) =>
      (update(garments)..where((g) => g.id.equals(id)))
          .write(const GarmentsCompanion(isDirty: Value(false)));
  Future<void> markOutfitSynced(String id) =>
      (update(outfits)..where((o) => o.id.equals(id)))
          .write(const OutfitsCompanion(isDirty: Value(false)));
}

/// Abre la base local CIFRADA con SQLCipher. La llave se aplica con `PRAGMA key`
/// antes de cualquier otra sentencia, en el isolate de background.
QueryExecutor _openEncrypted(SecureStore store) {
  return LazyDatabase(() async {
    if (Platform.isAndroid) {
      await applyWorkaroundToOpenSqlCipherOnOldAndroidVersions();
      open.overrideFor(OperatingSystem.android, openCipherOnAndroid);
    }

    final key = await store.databaseKey();
    final dir = await getApplicationDocumentsDirectory();
    final file = File('${dir.path}/quemepongo.sqlite');

    return NativeDatabase.createInBackground(
      file,
      isolateSetup: () async {
        if (Platform.isAndroid) {
          open.overrideFor(OperatingSystem.android, openCipherOnAndroid);
        }
      },
      setup: (db) {
        final cipher = db.select('PRAGMA cipher_version;');
        if (cipher.isEmpty) {
          throw StateError('SQLCipher no disponible: la base no quedaría cifrada');
        }
        final escaped = key.replaceAll("'", "''");
        db.execute("PRAGMA key = '$escaped';");
      },
    );
  });
}
