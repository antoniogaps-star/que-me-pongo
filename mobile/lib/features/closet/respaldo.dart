import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';

/// Respalda en el servidor, en segundo plano, la ficha y la foto de lo recién guardado.
///
/// Antes la foto solo subía al tocar "sincronizar": si la persona reinstalaba la app
/// sin hacerlo, la foto se perdía. Primero va la ficha (la foto necesita que la prenda
/// ya exista en el servidor) y luego la foto. Nunca lanza: sin red, se reintenta en la
/// siguiente sincronización.
Future<void> respaldarAhora(WidgetRef ref) async {
  final sync = ref.read(syncServiceProvider);
  final fotos = ref.read(photoSyncProvider);
  try {
    await sync.push();
    await fotos.subirPendientes();
  } catch (_) {
    // Sin conexión o servidor dormido: queda pendiente para la próxima vez.
  }
}
