import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../core/theme.dart';
import '../advisor/advisor_screen.dart';
import '../closet/add_garment_screen.dart';

/// La portada. Un solo botón manda: **¿QUÉ ME PONGO?**
///
/// Todo lo demás (sorpréndeme, agregar prenda) va debajo y en segundo plano: si el
/// usuario abre la app y ve tres botones del mismo tamaño, ya perdimos la magia.
class TodayTab extends ConsumerWidget {
  const TodayTab({super.key, required this.onIrAlCloset});

  final VoidCallback onIrAlCloset;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prendas = ref.watch(closetStreamProvider);
    final cuantas = prendas.valueOrNull?.length ?? 0;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 26),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset('assets/branding/logo_mark.png', width: 88),
            const SizedBox(height: 22),
            const Text(
              '¿Qué me pongo?',
              style: TextStyle(
                fontFamily: Marca.serif,
                color: Marca.oroClaro,
                fontSize: 32,
              ),
            ),
            const SizedBox(height: 14),
            const FileteOro(),
            const SizedBox(height: 34),

            // El botón estrella.
            SizedBox(
              height: 64,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute<void>(builder: (_) => const AdvisorScreen()),
                ),
                icon: const Icon(Icons.auto_awesome, size: 26),
                label: const Text(
                  'VÍSTEME HOY',
                  style: TextStyle(fontSize: 18, letterSpacing: 1.4),
                ),
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => const AdvisorScreen(sorpresa: true),
                ),
              ),
              icon: const Icon(Icons.casino_outlined),
              label: const Text('Sorpréndeme'),
            ),

            const SizedBox(height: 40),
            if (cuantas == 0)
              _Aviso(
                texto: 'Tu clóset está vacío. Toma la foto de tu primera prenda.',
                accion: 'Agregar prenda',
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute<bool>(builder: (_) => const AddGarmentScreen()),
                ),
              )
            else
              TextButton(
                onPressed: onIrAlCloset,
                child: Text(
                  '$cuantas ${cuantas == 1 ? 'prenda' : 'prendas'} en tu clóset',
                  style: const TextStyle(color: Marca.textoSuave),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Aviso extends StatelessWidget {
  const _Aviso({required this.texto, required this.accion, required this.onTap});

  final String texto;
  final String accion;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          texto,
          textAlign: TextAlign.center,
          style: const TextStyle(color: Marca.textoSuave, height: 1.5),
        ),
        const SizedBox(height: 10),
        TextButton.icon(
          onPressed: onTap,
          icon: const Icon(Icons.add_a_photo, color: Marca.oro, size: 19),
          label: Text(accion, style: const TextStyle(color: Marca.oro)),
        ),
      ],
    );
  }
}
