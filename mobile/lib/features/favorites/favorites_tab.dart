import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../data/local/database.dart';
import '../advisor/advisor_screen.dart';

/// Los outfits que marcaste con ⭐, con la explicación que dio el asesor.
class FavoritesTab extends ConsumerWidget {
  const FavoritesTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favoritos = ref.watch(favoritesStreamProvider);
    final prendas = ref.watch(closetStreamProvider);

    return favoritos.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (lista) {
        if (lista.isEmpty) return const _SinFavoritos();
        final porId = {for (final g in prendas.valueOrNull ?? <Garment>[]) g.id: g};
        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          itemCount: lista.length,
          itemBuilder: (_, i) => _TarjetaFavorito(
            outfit: lista[i],
            prendas: [
              for (final id in lista[i].garmentIds.split(','))
                if (porId[id] != null) porId[id]!,
            ],
          ),
        );
      },
    );
  }
}

class _SinFavoritos extends StatelessWidget {
  const _SinFavoritos();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(36),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.star_border, size: 54, color: Marca.oroHondo),
            SizedBox(height: 20),
            Text(
              'Sin favoritos todavía',
              style: TextStyle(
                fontFamily: Marca.serif,
                color: Marca.oroClaro,
                fontSize: 21,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Cuando un conjunto te guste, tócale la estrella y lo guardo aquí.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Marca.textoSuave, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }
}

class _TarjetaFavorito extends ConsumerWidget {
  const _TarjetaFavorito({required this.outfit, required this.prendas});

  final Outfit outfit;
  final List<Garment> prendas;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 108,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: prendas.length,
                separatorBuilder: (_, __) => const SizedBox(width: 10),
                itemBuilder: (_, i) => SizedBox(
                  width: 80,
                  child: FotoPrenda(prenda: prendas[i], radio: 11),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Text(
                    outfit.projection.isEmpty ? outfit.occasion : outfit.projection,
                    style: const TextStyle(
                      fontFamily: Marca.serif,
                      color: Marca.oroClaro,
                      fontSize: 18,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.star, color: Marca.oro),
                  tooltip: 'Quitar de favoritos',
                  onPressed: () =>
                      ref.read(favoritesRepositoryProvider).quitar(outfit.id),
                ),
              ],
            ),
            if (outfit.explanation.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                outfit.explanation,
                style: const TextStyle(
                  color: Marca.texto,
                  fontSize: 14,
                  height: 1.45,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
