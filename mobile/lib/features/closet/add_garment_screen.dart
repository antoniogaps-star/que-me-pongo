import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/providers.dart';
import '../../core/theme.dart';
import '../advisor/advisor_api.dart';
import 'closet_repository.dart';

/// Agregar una prenda: tomas la foto, la IA la clasifica y tú solo confirmas.
///
/// Si la IA no está disponible, NO se bloquea el flujo: la foto se conserva y el
/// usuario captura los datos a mano. Guardar una prenda nunca debe depender de internet.
class AddGarmentScreen extends ConsumerStatefulWidget {
  const AddGarmentScreen({super.key});

  @override
  ConsumerState<AddGarmentScreen> createState() => _AddGarmentScreenState();
}

class _AddGarmentScreenState extends ConsumerState<AddGarmentScreen> {
  final _nombre = TextEditingController();
  final _color = TextEditingController();

  File? _foto;
  String _categoria = 'arriba';
  String _temporada = 'todo';
  int _formalidad = 5;
  final Set<String> _estilos = {};

  bool _analizando = false;
  String? _avisoIA;
  bool _guardando = false;

  @override
  void dispose() {
    _nombre.dispose();
    _color.dispose();
    super.dispose();
  }

  Future<void> _tomarFoto(ImageSource origen) async {
    final elegida = await ImagePicker().pickImage(
      source: origen,
      // Suficiente para que la IA la reconozca sin llenar el teléfono de fotos pesadas.
      maxWidth: 1400,
      imageQuality: 85,
    );
    if (elegida == null) return;
    setState(() {
      _foto = File(elegida.path);
      _avisoIA = null;
    });
    await _analizar();
  }

  Future<void> _analizar() async {
    if (_foto == null) return;
    setState(() => _analizando = true);
    try {
      final ficha = await ref.read(advisorApiProvider).clasificar(_foto!);
      if (!mounted) return;
      setState(() {
        _categoria = ficha.categoria;
        _nombre.text = ficha.nombre;
        _color.text = ficha.color;
        _formalidad = ficha.formalidad;
        _temporada = ficha.temporada;
        _estilos
          ..clear()
          ..addAll(ficha.estilos.where(estilos.contains));
      });
    } on SinAsesorException catch (e) {
      if (mounted) setState(() => _avisoIA = e.mensaje);
    } catch (_) {
      if (mounted) {
        setState(() => _avisoIA =
            'No pude analizar la foto. Captura los datos a mano y sigue adelante.');
      }
    } finally {
      if (mounted) setState(() => _analizando = false);
    }
  }

  Future<void> _guardar() async {
    if (_nombre.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ponle un nombre a la prenda')),
      );
      return;
    }
    setState(() => _guardando = true);
    final navigator = Navigator.of(context);
    await ref.read(closetRepositoryProvider).add(
          category: _categoria,
          name: _nombre.text.trim(),
          color: _color.text.trim().isEmpty ? null : _color.text.trim(),
          styles: _estilos.toList(),
          formality: _formalidad,
          season: _temporada,
          foto: _foto,
        );
    if (mounted) navigator.pop(true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Agregar prenda')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        children: [
          _ZonaFoto(
            foto: _foto,
            analizando: _analizando,
            onCamara: () => _tomarFoto(ImageSource.camera),
            onGaleria: () => _tomarFoto(ImageSource.gallery),
          ),
          if (_avisoIA != null) ...[
            const SizedBox(height: 14),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: Marca.oroHondo, size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _avisoIA!,
                        style: const TextStyle(color: Marca.textoSuave, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),
          TextField(
            controller: _nombre,
            decoration: const InputDecoration(labelText: 'Nombre de la prenda'),
            textCapitalization: TextCapitalization.sentences,
          ),
          const SizedBox(height: 14),
          TextField(
            controller: _color,
            decoration: const InputDecoration(labelText: 'Color'),
            textCapitalization: TextCapitalization.sentences,
          ),
          const SizedBox(height: 24),
          const _Etiqueta('¿Qué es?'),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final e in categorias.entries)
                ChoiceChip(
                  label: Text(e.value),
                  selected: _categoria == e.key,
                  onSelected: (_) => setState(() => _categoria = e.key),
                ),
            ],
          ),
          const SizedBox(height: 24),
          const _Etiqueta('Estilos que le quedan'),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final e in estilos)
                FilterChip(
                  label: Text(e[0].toUpperCase() + e.substring(1)),
                  selected: _estilos.contains(e),
                  onSelected: (sel) => setState(
                    () => sel ? _estilos.add(e) : _estilos.remove(e),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 24),
          const _Etiqueta('¿Qué tan formal es?'),
          const SizedBox(height: 4),
          Text(
            _describeFormalidad(_formalidad),
            style: const TextStyle(color: Marca.textoSuave, fontSize: 13),
          ),
          Slider(
            value: _formalidad.toDouble(),
            min: 1,
            max: 10,
            divisions: 9,
            label: '$_formalidad',
            onChanged: (v) => setState(() => _formalidad = v.round()),
          ),
          const SizedBox(height: 12),
          const _Etiqueta('¿Para qué clima?'),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: [
              for (final e in temporadas.entries)
                ChoiceChip(
                  label: Text(e.value),
                  selected: _temporada == e.key,
                  onSelected: (_) => setState(() => _temporada = e.key),
                ),
            ],
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: _guardando ? null : _guardar,
            icon: const Icon(Icons.check),
            label: Text(_guardando ? 'Guardando…' : 'Guardar en mi clóset'),
          ),
        ],
      ),
    );
  }

  /// Traduce el número a algo que una persona entienda de inmediato.
  static String _describeFormalidad(int v) => switch (v) {
        <= 2 => 'Para andar en casa',
        <= 4 => 'Informal, del diario',
        <= 6 => 'Arreglado sin exagerar',
        <= 8 => 'Formal: oficina, reunión',
        _ => 'De etiqueta',
      };
}

class _ZonaFoto extends StatelessWidget {
  const _ZonaFoto({
    required this.foto,
    required this.analizando,
    required this.onCamara,
    required this.onGaleria,
  });

  final File? foto;
  final bool analizando;
  final VoidCallback onCamara;
  final VoidCallback onGaleria;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AspectRatio(
          aspectRatio: 1,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(18),
            child: Container(
              color: Marca.carbon,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if (foto != null)
                    Image.file(foto!, fit: BoxFit.cover)
                  else
                    const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.photo_camera_outlined,
                              size: 46, color: Marca.oroHondo),
                          SizedBox(height: 12),
                          Text(
                            'Toma la foto de una prenda',
                            style: TextStyle(color: Marca.textoSuave),
                          ),
                        ],
                      ),
                    ),
                  if (analizando)
                    Container(
                      color: Marca.negro.withValues(alpha: 0.72),
                      child: const Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            CircularProgressIndicator(color: Marca.oro),
                            SizedBox(height: 16),
                            Text(
                              'Viendo tu prenda…',
                              style: TextStyle(color: Marca.oroClaro),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 14),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: analizando ? null : onCamara,
                icon: const Icon(Icons.photo_camera),
                label: const Text('Cámara'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: analizando ? null : onGaleria,
                icon: const Icon(Icons.photo_library),
                label: const Text('Galería'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _Etiqueta extends StatelessWidget {
  const _Etiqueta(this.texto);
  final String texto;

  @override
  Widget build(BuildContext context) => Text(
        texto,
        style: const TextStyle(
          fontFamily: Marca.serif,
          color: Marca.oroClaro,
          fontSize: 17,
        ),
      );
}
