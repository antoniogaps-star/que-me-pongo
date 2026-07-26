import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../data/local/database.dart';
import 'advisor_api.dart';

/// Las ocasiones del PRD. El texto que se manda al asesor va en minúsculas sin acentos
/// para que empate con las reglas locales de respaldo.
const _ocasiones = <String, String>{
  'Día normal': 'dia normal',
  'Trabajo': 'trabajo',
  'Cita': 'cita',
  'Fiesta': 'fiesta',
  'Reunión': 'reunion',
  'Escuela': 'escuela',
  'Evento formal': 'evento formal',
  'Salida casual': 'salida casual',
  'Viaje': 'viaje',
};

/// Qué imagen quiere dar el usuario. Es lo que convierte la app en asesor de imagen
/// y no en un simple combinador de colores.
const _proyecciones = <String>[
  'Elegante',
  'Seguro',
  'Atractivo',
  'Moderno',
  'Relajado',
  'Profesional',
  'Poderoso',
];

/// La pantalla estrella: eliges ocasión y qué quieres proyectar, y el asesor te arma
/// el conjunto con TUS prendas y te explica por qué funciona.
class AdvisorScreen extends ConsumerStatefulWidget {
  const AdvisorScreen({super.key, this.conPrenda, this.sorpresa = false});

  /// Si viene, el conjunto DEBE incluir esta prenda ("¿con qué combino esto?").
  final Garment? conPrenda;

  /// Modo sorpresa: propone algo distinto a lo que ya usas.
  final bool sorpresa;

  @override
  ConsumerState<AdvisorScreen> createState() => _AdvisorScreenState();
}

class _AdvisorScreenState extends ConsumerState<AdvisorScreen> {
  String _ocasion = 'dia normal';
  String _proyeccion = '';
  bool _cargando = false;
  String? _error;
  Recomendacion? _resultado;

  Future<void> _pedirRecomendacion() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final api = ref.read(advisorApiProvider);
      final r = await api.recomendar(
        ocasion: _ocasion,
        proyeccion: _proyeccion,
        conPrendaId: widget.conPrenda?.id,
        sorpresa: widget.sorpresa,
      );
      if (mounted) setState(() => _resultado = r);
    } catch (e) {
      if (mounted) setState(() => _error = _mensaje(e));
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  String _mensaje(Object e) {
    final texto = e.toString();
    if (texto.contains('EMPTY_CLOSET') || texto.contains('clóset está vacío')) {
      return 'Tu clóset está vacío. Toma una foto de tu primera prenda para empezar.';
    }
    if (texto.contains('NOT_ENOUGH_GARMENTS') || texto.contains('suficientes prendas')) {
      return 'Aún faltan prendas. Agrega al menos una de arriba, una de abajo y un calzado.';
    }
    return 'No pude armar el conjunto. Revisa tu conexión e inténtalo de nuevo.';
  }

  @override
  Widget build(BuildContext context) {
    final titulo = widget.sorpresa
        ? 'Sorpréndeme'
        : widget.conPrenda != null
            ? '¿Con qué combino esto?'
            : '¿Qué me pongo?';

    return Scaffold(
      appBar: AppBar(title: Text(titulo)),
      body: _resultado != null
          ? _Resultado(
              recomendacion: _resultado!,
              ocasion: _ocasion,
              proyeccion: _proyeccion,
              onOtro: () {
                setState(() => _resultado = null);
                _pedirRecomendacion();
              },
              onCambiar: () => setState(() => _resultado = null),
            )
          : _Preguntas(
              ocasion: _ocasion,
              proyeccion: _proyeccion,
              conPrenda: widget.conPrenda,
              cargando: _cargando,
              error: _error,
              onOcasion: (v) => setState(() => _ocasion = v),
              onProyeccion: (v) => setState(() => _proyeccion = v),
              onListo: _pedirRecomendacion,
            ),
    );
  }
}

/// Paso 1: ¿para qué ocasión y qué quieres proyectar?
class _Preguntas extends StatelessWidget {
  const _Preguntas({
    required this.ocasion,
    required this.proyeccion,
    required this.conPrenda,
    required this.cargando,
    required this.error,
    required this.onOcasion,
    required this.onProyeccion,
    required this.onListo,
  });

  final String ocasion;
  final String proyeccion;
  final Garment? conPrenda;
  final bool cargando;
  final String? error;
  final ValueChanged<String> onOcasion;
  final ValueChanged<String> onProyeccion;
  final VoidCallback onListo;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
      children: [
        if (conPrenda != null) ...[
          _PrendaAncla(prenda: conPrenda!),
          const SizedBox(height: 24),
        ],
        const _Titulo('¿Para qué ocasión?'),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final e in _ocasiones.entries)
              ChoiceChip(
                label: Text(e.key),
                selected: ocasion == e.value,
                onSelected: (_) => onOcasion(e.value),
              ),
          ],
        ),
        const SizedBox(height: 28),
        const _Titulo('¿Qué quieres proyectar?'),
        const SizedBox(height: 6),
        const Text(
          'Opcional — si lo dejas en blanco, yo lo decido por la ocasión.',
          style: TextStyle(color: Marca.textoSuave, fontSize: 12.5),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final p in _proyecciones)
              ChoiceChip(
                label: Text(p),
                selected: proyeccion == p,
                // Volver a tocar el mismo quita la selección.
                onSelected: (_) => onProyeccion(proyeccion == p ? '' : p),
              ),
          ],
        ),
        const SizedBox(height: 34),
        if (error != null) ...[
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(error!, style: const TextStyle(color: Marca.texto)),
            ),
          ),
          const SizedBox(height: 16),
        ],
        ElevatedButton.icon(
          onPressed: cargando ? null : onListo,
          icon: cargando
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Marca.negro),
                )
              : const Icon(Icons.auto_awesome),
          label: Text(cargando ? 'Pensando…' : 'Vísteme'),
        ),
      ],
    );
  }
}

/// Paso 2: el conjunto, con la explicación y la imagen que proyecta.
class _Resultado extends ConsumerWidget {
  const _Resultado({
    required this.recomendacion,
    required this.ocasion,
    required this.proyeccion,
    required this.onOtro,
    required this.onCambiar,
  });

  final Recomendacion recomendacion;
  final String ocasion;
  final String proyeccion;
  final VoidCallback onOtro;
  final VoidCallback onCambiar;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prendas = ref.watch(closetStreamProvider);

    return prendas.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (todas) {
        final porId = {for (final g in todas) g.id: g};
        return ListView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          children: [
            for (final sugerencia in recomendacion.outfits)
              _TarjetaOutfit(
                sugerencia: sugerencia,
                prendas: [
                  for (final id in sugerencia.garmentIds)
                    if (porId[id] != null) porId[id]!,
                ],
                ocasion: ocasion,
                proyeccion: proyeccion,
              ),
            const SizedBox(height: 22),
            OutlinedButton.icon(
              onPressed: onOtro,
              icon: const Icon(Icons.refresh),
              label: const Text('Proponme otro'),
            ),
            const SizedBox(height: 10),
            TextButton(
              onPressed: onCambiar,
              child: const Text(
                'Cambiar ocasión',
                style: TextStyle(color: Marca.textoSuave),
              ),
            ),
            if (!recomendacion.vieneDeIA) ...[
              const SizedBox(height: 18),
              const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.cloud_off, size: 15, color: Marca.textoSuave),
                  SizedBox(width: 7),
                  Flexible(
                    child: Text(
                      'Sin conexión al asesor: combinación básica',
                      style: TextStyle(color: Marca.textoSuave, fontSize: 12),
                    ),
                  ),
                ],
              ),
            ],
          ],
        );
      },
    );
  }
}

class _TarjetaOutfit extends ConsumerStatefulWidget {
  const _TarjetaOutfit({
    required this.sugerencia,
    required this.prendas,
    required this.ocasion,
    required this.proyeccion,
  });

  final Sugerencia sugerencia;
  final List<Garment> prendas;
  final String ocasion;
  final String proyeccion;

  @override
  ConsumerState<_TarjetaOutfit> createState() => _TarjetaOutfitState();
}

class _TarjetaOutfitState extends ConsumerState<_TarjetaOutfit> {
  bool _guardado = false;

  Future<void> _guardar() async {
    await ref.read(favoritesRepositoryProvider).guardar(
          garmentIds: widget.sugerencia.garmentIds,
          ocasion: widget.ocasion,
          proyeccion: widget.sugerencia.imagenProyectada,
          explicacion: widget.sugerencia.explicacion,
        );
    if (mounted) {
      setState(() => _guardado = true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Guardado en tus favoritos')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 18),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Las prendas del conjunto, en fila.
            SizedBox(
              height: 132,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: widget.prendas.length,
                separatorBuilder: (_, __) => const SizedBox(width: 12),
                itemBuilder: (_, i) => _MiniPrenda(prenda: widget.prendas[i]),
              ),
            ),
            const SizedBox(height: 20),
            if (widget.sugerencia.imagenProyectada.isNotEmpty) ...[
              const Text(
                'IMAGEN QUE PROYECTAS',
                style: TextStyle(
                  color: Marca.textoSuave,
                  fontSize: 10.5,
                  letterSpacing: 1.6,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                widget.sugerencia.imagenProyectada,
                style: const TextStyle(
                  fontFamily: Marca.serif,
                  color: Marca.oroClaro,
                  fontSize: 20,
                ),
              ),
              const SizedBox(height: 16),
            ],
            Text(
              widget.sugerencia.explicacion,
              style: const TextStyle(color: Marca.texto, fontSize: 15, height: 1.45),
            ),
            const SizedBox(height: 14),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: _guardado ? null : _guardar,
                icon: Icon(_guardado ? Icons.star : Icons.star_border, color: Marca.oro),
                label: Text(
                  _guardado ? 'Guardado' : 'Me gusta',
                  style: const TextStyle(color: Marca.oro),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MiniPrenda extends StatelessWidget {
  const _MiniPrenda({required this.prenda});

  final Garment prenda;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 96,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: FotoPrenda(prenda: prenda, radio: 12)),
          const SizedBox(height: 6),
          Text(
            prenda.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: Marca.textoSuave, fontSize: 11.5),
          ),
        ],
      ),
    );
  }
}

class _PrendaAncla extends StatelessWidget {
  const _PrendaAncla({required this.prenda});

  final Garment prenda;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            SizedBox(width: 68, height: 68, child: FotoPrenda(prenda: prenda, radio: 10)),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'ARMANDO ALREDEDOR DE',
                    style: TextStyle(
                      color: Marca.textoSuave,
                      fontSize: 10,
                      letterSpacing: 1.4,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    prenda.name,
                    style: const TextStyle(color: Marca.texto, fontSize: 16),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// La foto de una prenda; si no hay foto, un ícono según su categoría.
class FotoPrenda extends StatelessWidget {
  const FotoPrenda({super.key, required this.prenda, this.radio = 14});

  final Garment prenda;
  final double radio;

  static const _iconos = <String, IconData>{
    'arriba': Icons.checkroom,
    'abajo': Icons.dry_cleaning,
    'abrigo': Icons.ac_unit,
    'calzado': Icons.hiking,
    'accesorio': Icons.watch,
    'completo': Icons.style,
  };

  @override
  Widget build(BuildContext context) {
    final ruta = prenda.photoPath;
    final tieneFoto = ruta != null && File(ruta).existsSync();
    return ClipRRect(
      borderRadius: BorderRadius.circular(radio),
      child: Container(
        color: Marca.carbon,
        child: tieneFoto
            ? Image.file(File(ruta), fit: BoxFit.cover, width: double.infinity)
            : Center(
                child: Icon(
                  _iconos[prenda.category] ?? Icons.checkroom,
                  color: Marca.oroHondo,
                  size: 30,
                ),
              ),
      ),
    );
  }
}

class _Titulo extends StatelessWidget {
  const _Titulo(this.texto);
  final String texto;

  @override
  Widget build(BuildContext context) => Text(
        texto,
        style: const TextStyle(
          fontFamily: Marca.serif,
          color: Marca.oroClaro,
          fontSize: 22,
        ),
      );
}
