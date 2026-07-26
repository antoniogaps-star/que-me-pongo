import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/local/database.dart';
import '../data/sync/sync_service.dart';
import '../features/advisor/advisor_api.dart';
import '../features/auth/auth_repository.dart';
import '../features/closet/closet_repository.dart';
import '../features/favorites/favorites_repository.dart';
import 'api_client.dart';
import 'secure_store.dart';

/// Tipo de sesión activa: ninguna (mostrar login) o real.
enum SessionKind { none, real }

/// Inyección de dependencias con Riverpod.
final secureStoreProvider = Provider<SecureStore>((_) => const SecureStore());

final dioProvider = Provider<Dio>(
  (ref) => createDio(ref.watch(secureStoreProvider)),
);

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(dioProvider), ref.watch(secureStoreProvider)),
);

final databaseProvider = Provider<AppDatabase>((ref) {
  final db = AppDatabase.encrypted(ref.watch(secureStoreProvider));
  ref.onDispose(db.close);
  return db;
});

final syncServiceProvider = Provider<SyncService>(
  (ref) => SyncService(ref.watch(databaseProvider), ref.watch(dioProvider)),
);

// ── El asesor de imagen ──────────────────────────────────────
final advisorApiProvider = Provider<AdvisorApi>(
  (ref) => AdvisorApi(ref.watch(dioProvider)),
);

// ── Clóset ───────────────────────────────────────────────────
final closetRepositoryProvider = Provider<ClosetRepository>(
  (ref) => ClosetRepository(
    ref.watch(databaseProvider),
    ref.watch(authRepositoryProvider).currentTenantId(),
  ),
);

/// El clóset en vivo: al agregar o quitar una prenda, la cuadrícula se actualiza sola.
final closetStreamProvider = StreamProvider<List<Garment>>(
  (ref) => ref.watch(closetRepositoryProvider).watch(),
);

// ── Favoritos ────────────────────────────────────────────────
final favoritesRepositoryProvider = Provider<FavoritesRepository>(
  (ref) => FavoritesRepository(
    ref.watch(databaseProvider),
    ref.watch(authRepositoryProvider).currentTenantId(),
  ),
);

final favoritesStreamProvider = StreamProvider<List<Outfit>>(
  (ref) => ref.watch(favoritesRepositoryProvider).watch(),
);

/// Cuenta recordada en este equipo. Si existe, al abrir la app se muestra la pantalla
/// de "Entrar" (solo pide contraseña); si no, "Crear cuenta".
final savedAccountProvider = FutureProvider<(String company, String email)?>((ref) async {
  final store = ref.watch(secureStoreProvider);
  final company = await store.lastCompany;
  final email = await store.lastEmail;
  if (company == null || email == null || company.isEmpty || email.isEmpty) return null;
  return (company, email);
});

/// Estado de sesión: real (token guardado) o ninguna.
class AuthController extends AsyncNotifier<SessionKind> {
  AuthRepository get _repo => ref.read(authRepositoryProvider);

  @override
  Future<SessionKind> build() async {
    return (await _repo.hasSession()) ? SessionKind.real : SessionKind.none;
  }

  /// Inicia sesión. NO usa AsyncLoading para no reemplazar la pantalla de login
  /// mientras se procesa; lanza la excepción si falla y la pantalla la muestra.
  Future<void> login({
    required String companySlug,
    required String email,
    required String password,
  }) async {
    await _repo.login(companySlug: companySlug, email: email, password: password);
    state = const AsyncData(SessionKind.real);
  }

  Future<void> register({
    required String companyName,
    required String companySlug,
    required String email,
    required String password,
  }) async {
    await _repo.register(
      companyName: companyName,
      companySlug: companySlug,
      email: email,
      password: password,
    );
    state = const AsyncData(SessionKind.real);
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AsyncData(SessionKind.none);
  }
}

final authControllerProvider =
    AsyncNotifierProvider<AuthController, SessionKind>(AuthController.new);
