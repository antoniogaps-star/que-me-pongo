import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:quemepongo_mobile/data/local/database.dart';
import 'package:quemepongo_mobile/features/closet/closet_repository.dart';
import 'package:quemepongo_mobile/features/favorites/favorites_repository.dart';

void main() {
  late AppDatabase db;
  late ClosetRepository closet;
  late FavoritesRepository favoritos;

  setUp(() {
    db = AppDatabase(NativeDatabase.memory());
    closet = ClosetRepository(db, Future.value('tenant-1'));
    favoritos = FavoritesRepository(db, Future.value('tenant-1'));
  });

  tearDown(() => db.close());

  test('una prenda guardada aparece en el clóset', () async {
    await closet.add(
      category: 'arriba',
      name: 'Camisa blanca',
      color: 'blanco',
      styles: ['elegante', 'ejecutivo'],
      formality: 8,
    );

    final lista = await closet.list();
    expect(lista, hasLength(1));
    expect(lista.first.name, 'Camisa blanca');
    expect(lista.first.formality, 8);
    // Los estilos viajan como CSV para que el servidor los reciba tal cual.
    expect(lista.first.styles, 'elegante,ejecutivo');
  });

  test('una prenda nueva queda pendiente de subir (outbox)', () async {
    await closet.add(category: 'calzado', name: 'Tenis');
    final pendientes = await db.dirtyGarments();
    expect(pendientes, hasLength(1));
    expect(pendientes.first.isDirty, isTrue);
  });

  test('quitar una prenda la oculta pero deja el borrado listo para sincronizar', () async {
    final id = await closet.add(category: 'abajo', name: 'Jeans');
    await db.markGarmentSynced(id);

    await closet.remove(id);

    // Ya no se ve en el clóset...
    expect(await closet.list(), isEmpty);
    // ...pero el borrado sí tiene que viajar al servidor (tombstone).
    final pendientes = await db.dirtyGarments();
    expect(pendientes, hasLength(1));
    expect(pendientes.first.isDeleted, isTrue);
    expect(pendientes.first.version, greaterThan(1));
  });

  test('el clóset en vivo avisa cuando entra una prenda', () async {
    expect(await closet.watch().first, isEmpty);
    await closet.add(category: 'abrigo', name: 'Chamarra');
    expect(await closet.watch().first, hasLength(1));
  });

  test('un favorito guarda las prendas, la ocasión y la explicación', () async {
    await favoritos.guardar(
      garmentIds: ['a', 'b', 'c'],
      ocasion: 'evento formal',
      proyeccion: 'Elegante',
      explicacion: 'Combinación sobria que proyecta seguridad.',
    );

    final lista = await db.activeOutfits();
    expect(lista, hasLength(1));
    expect(lista.first.garmentIds, 'a,b,c');
    expect(lista.first.projection, 'Elegante');
    expect(lista.first.explanation, contains('seguridad'));
  });

  test('quitar un favorito lo oculta y deja el borrado por sincronizar', () async {
    await favoritos.guardar(
      garmentIds: ['a'],
      ocasion: 'cita',
      proyeccion: 'Atractivo',
      explicacion: '',
    );
    final guardado = (await db.activeOutfits()).first;

    await favoritos.quitar(guardado.id);

    expect(await db.activeOutfits(), isEmpty);
    final pendientes = await db.dirtyOutfits();
    expect(pendientes.single.isDeleted, isTrue);
  });
}
