import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../data/local/database.dart';
import '../advisor/advisor_screen.dart';
import 'add_garment_screen.dart';
import 'closet_repository.dart';
import 'respaldo.dart';

/// Mi clóset: la cuadrícula de prendas con su foto. Desde aquí se agrega una prenda
/// nueva y se pregunta "¿con qué combino esto?".
class ClosetTab extends ConsumerWidget {
  const ClosetTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prendas = ref.watch(closetStreamProvider);

    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Marca.oro,
        foregroundColor: Marca.negro,
        onPressed: () => Navigator.of(context).push(
          MaterialPageRoute<bool>(builder: (_) => const AddGarmentScreen()),
        ),
        icon: const Icon(Icons.add_a_photo),
        label: const Text('Agregar prenda'),
      ),
      body: prendas.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (lista) => lista.isEmpty
            ? const _ClosetVacio()
            : GridView.builder(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 14,
                  crossAxisSpacing: 14,
                  childAspectRatio: 0.78,
                ),
                itemCount: lista.length,
                itemBuilder: (_, i) => _TarjetaPrenda(prenda: lista[i]),
              ),
      ),
    );
  }
}

class _ClosetVacio extends StatelessWidget {
  const _ClosetVacio();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(36),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset('assets/branding/logo_mark.png', width: 96),
            const SizedBox(height: 26),
            const Text(
              'Tu clóset está vacío',
              style: TextStyle(
                fontFamily: Marca.serif,
                color: Marca.oroClaro,
                fontSize: 23,
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Toma una foto de cada prenda. Con tres o cuatro ya puedo vestirte.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Marca.textoSuave, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }
}

class _TarjetaPrenda extends ConsumerWidget {
  const _TarjetaPrenda({required this.prenda});

  final Garment prenda;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return GestureDetector(
      onTap: () => _abrirOpciones(context, ref),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: FotoPrenda(prenda: prenda)),
          const SizedBox(height: 8),
          Text(
            prenda.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: Marca.texto, fontSize: 14),
          ),
          const SizedBox(height: 2),
          Text(
            categorias[prenda.category] ?? prenda.category,
            style: const TextStyle(color: Marca.textoSuave, fontSize: 11.5),
          ),
        ],
      ),
    );
  }

  void _abrirOpciones(BuildContext context, WidgetRef ref) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: Marca.carbon,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      ),
      builder: (hoja) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 22),
              child: Row(
                children: [
                  SizedBox(
                    width: 58,
                    height: 58,
                    child: FotoPrenda(prenda: prenda, radio: 10),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          prenda.name,
                          style: const TextStyle(color: Marca.texto, fontSize: 17),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          _detalle(prenda),
                          style: const TextStyle(
                            color: Marca.textoSuave,
                            fontSize: 12.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            const Divider(height: 22, color: Color(0xFF2A2620)),
            ListTile(
              leading: const Icon(Icons.auto_awesome, color: Marca.oro),
              title: const Text(
                '¿Con qué combino esto?',
                style: TextStyle(color: Marca.texto),
              ),
              onTap: () {
                Navigator.of(hoja).pop();
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => AdvisorScreen(conPrenda: prenda),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined, color: Marca.oro),
              title: Text(
                prenda.photoPath == null ? 'Ponerle foto' : 'Cambiar foto',
                style: const TextStyle(color: Marca.texto),
              ),
              onTap: () {
                Navigator.of(hoja).pop();
                _cambiarFoto(context, ref);
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete_outline, color: Marca.textoSuave),
              title: const Text(
                'Quitar del clóset',
                style: TextStyle(color: Marca.textoSuave),
              ),
              onTap: () async {
                Navigator.of(hoja).pop();
                await ref.read(closetRepositoryProvider).remove(prenda.id);
              },
            ),
            const SizedBox(height: 10),
          ],
        ),
      ),
    );
  }

  /// Cámara o galería, y la foto queda puesta y respaldada en el servidor.
  Future<void> _cambiarFoto(BuildContext context, WidgetRef ref) async {
    final messenger = ScaffoldMessenger.of(context);
    final origen = await showModalBottomSheet<ImageSource>(
      context: context,
      backgroundColor: Marca.carbon,
      builder: (hoja) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined, color: Marca.oro),
              title: const Text('Tomar foto', style: TextStyle(color: Marca.texto)),
              onTap: () => Navigator.of(hoja).pop(ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined, color: Marca.oro),
              title: const Text('Elegir de la galería', style: TextStyle(color: Marca.texto)),
              onTap: () => Navigator.of(hoja).pop(ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (origen == null) return;

    final XFile? elegida;
    try {
      // Mismo tamaño y calidad que al agregar una prenda.
      elegida = await ImagePicker().pickImage(source: origen, maxWidth: 1400, imageQuality: 85);
    } catch (_) {
      messenger.showSnackBar(const SnackBar(
        content: Text('Tu teléfono no dejó abrir la cámara o la galería. Revisa los '
            'permisos de la app en los ajustes de Android.'),
      ));
      return;
    }
    if (elegida == null) return;

    await ref.read(closetRepositoryProvider).cambiarFoto(prenda, File(elegida.path));
    unawaited(respaldarAhora(ref));
  }

  static String _detalle(Garment g) {
    final partes = <String>[categorias[g.category] ?? g.category];
    if (g.color != null && g.color!.isNotEmpty) partes.add(g.color!);
    if (g.styles.isNotEmpty) partes.add(g.styles.split(',').join(' · '));
    return partes.join(' · ');
  }
}
