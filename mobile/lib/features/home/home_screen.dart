import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../data/sync/sync_service.dart';
import '../billing/pricing_screen.dart';
import '../closet/closet_tab.dart';
import '../favorites/favorites_tab.dart';
import 'today_tab.dart';

/// Shell principal tras iniciar sesión: Hoy (la pantalla estrella), Mi clóset y
/// Favoritos, con sincronización y cierre de sesión arriba.
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _tab = 0;

  Future<void> _sync() async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final sync = ref.read(syncServiceProvider);
      await sync.push();
      await sync.pull();
      messenger.showSnackBar(const SnackBar(content: Text('Sincronización completa')));
    } on SubscriptionExpiredException catch (e) {
      messenger.showSnackBar(
        SnackBar(
          content: Text(e.message),
          duration: const Duration(seconds: 6),
          action: SnackBarAction(
            label: 'Renovar',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(builder: (_) => const PricingScreen()),
            ),
          ),
        ),
      );
    } catch (_) {
      messenger.showSnackBar(
        const SnackBar(content: Text('Sin conexión: se sincronizará luego')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(switch (_tab) {
          0 => '',
          1 => 'Mi clóset',
          _ => 'Favoritos',
        }),
        actions: [
          IconButton(
            icon: const Icon(Icons.workspace_premium),
            tooltip: 'Planes y activación',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(builder: (_) => const PricingScreen()),
            ),
          ),
          IconButton(icon: const Icon(Icons.sync), tooltip: 'Sincronizar', onPressed: _sync),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: IndexedStack(
        index: _tab,
        children: [
          TodayTab(onIrAlCloset: () => setState(() => _tab = 1)),
          const ClosetTab(),
          const FavoritesTab(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.auto_awesome_outlined), label: 'Hoy'),
          NavigationDestination(icon: Icon(Icons.checkroom_outlined), label: 'Mi clóset'),
          NavigationDestination(icon: Icon(Icons.star_border), label: 'Favoritos'),
        ],
      ),
    );
  }
}
