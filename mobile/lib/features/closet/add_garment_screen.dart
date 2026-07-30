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

  /// Cuenta cada intento de análisis. Si el usuario toma otra foto o decide llenar los
  /// datos a mano, la respuesta que venía en camino ya no debe pisar lo que él escribió.
  int _intento = 0;

  @override
  void dispose() {
    _nombre.dispose();
    _color.dispose();
    super.dispose();
  }

  Future<void> _tomarFoto(ImageSource origen) async {
    final XFile? elegida;
    try {
      elegida = await ImagePicker().pickImage(
        source: origen,
        // Suficiente para que la IA la reconozca sin llenar el teléfono de fotos pesadas.
        maxWidth: 1400,
        imageQuality: 85,
      );
    } catch (e) {
      // Si el teléfono niega la cámara o la galería, el usuario tiene que ENTERARSE.
      // Sin este aviso el botón simplemente no hacía nada y parecía que la app estaba
      // rota, sin ninguna pista de por qué.
      if (mounted) {
        setState(() => _avisoIA = origen == ImageSource.camera
            ? 'Tu teléfono no dejó abrir la cámara. Prueba con "Galería", o revisa '
                'los permisos de la app en los ajustes de Android.'
            : 'Tu teléfono no dejó abrir la galería. Revisa los permisos de la app '
                'en los ajustes de Android.');
      }
      return;
    }

    if (elegida == null) return; // el usuario se arrepintió
    setState(() {
      _foto = File(elegida!.path);
      _avisoIA = null;
    });
    await _analizar();
  }

  /// Deja de esperar a la IA y devuelve el control al usuario.
  ///
  /// El servidor gratis tarda hasta ~50 s en despertar. Nadie tiene que quedarse viendo
  /// una rueda girar: la foto ya está tomada y los datos se pueden escribir a mano.
  void _llenarAMano() {
    _intento++; // lo que venga en camino ya no aplica
    setState(() {
      _analizando = false;
      _avisoIA = 'Listo, escribe los datos tú. La foto ya quedó guardada.';
    });
  }

  Future<void> _analizar() async {
    if (_foto == null) return;
    final mio = ++_intento;
    setState(() => _analizando = true);
    try {
      final ficha = await ref.read(advisorApiProvider).clasificar(_foto!);
      // Si mientras tanto tomó otra foto o se cansó de esperar, no le pisamos nada.
      if (!mounted || mio != _intento) return;
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
      if (mounted && mio == _intento) setState(() => _avisoIA = e.mensaje);
    } catch (_) {
      if (mounted && mio == _intento) {
        setState(() => _avisoIA =
            'No pude analizar la foto. Captura los datos a mano y sigue adelante.');
      }
    } finally {
      if (mounted && mio == _intento) setState(() => _analizando = false);
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
            onLlenarAMano: _llenarAMano,
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
    required this.onLlenarAMano,
  });

  final File? foto;
  final bool analizando;
  final VoidCallback onCamara;
  final VoidCallback onGaleria;
  final VoidCallback onLlenarAMano;

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
                  // El aviso va en una franja ABAJO, no como velo encima: la foto tiene
                  // que verse siempre. Antes la tapaba por completo y, como el servidor
                  // gratis tarda hasta ~50 s en despertar, parecía que la app se había
                  // trabado y que la foto nunca entró.
                  if (analizando)
                    Positioned(
                      left: 0,
                      right: 0,
                      bottom: 0,
                      child: Container(
                        color: Marca.negro.withValues(alpha: 0.78),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 12,
                        ),
                        child: const Row(
                          children: [
                            SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                color: Marca.oro,
                                strokeWidth: 2,
                              ),
                            ),
                            SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Viendo tu prenda… puede tardar hasta un minuto la '
                                'primera vez del día.',
                                style: TextStyle(
                                  color: Marca.oroClaro,
                                  fontSize: 12,
                                ),
                              ),
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
        // Los botones NO se desactivan mientras la IA piensa: la foto ya está tomada y
        // el usuario tiene que poder repetirla o seguir sin esperar a nadie.
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: onCamara,
                icon: const Icon(Icons.photo_camera),
                label: const Text('Cámara'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: onGaleria,
                icon: const Icon(Icons.photo_library),
                label: const Text('Galería'),
              ),
            ),
          ],
        ),
        if (analizando)
          TextButton(
            onPressed: onLlenarAMano,
            child: const Text('No esperar: lleno los datos yo'),
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
