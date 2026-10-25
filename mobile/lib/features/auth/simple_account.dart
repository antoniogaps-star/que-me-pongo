import 'package:flutter/material.dart';

import '../../core/slug.dart';

/// Cuenta sencilla: la persona solo da un NOMBRE DE USUARIO y su FECHA DE NACIMIENTO.
///
/// El servidor sigue siendo multiempresa, así que la app traduce esos dos datos a lo
/// que él espera: cada usuario es su propia "empresa" (su clóset privado), con un
/// correo interno que nadie ve y la fecha como contraseña (DDMMAAAA, 8 dígitos: cumple
/// el mínimo de 8 del servidor). Así no hace falta tocar el backend.
const _internalDomain = 'usuarios.quemepongo.app';

/// Largo máximo del nombre de usuario: el correo interno no admite más de 64
/// caracteres antes de la @.
const usernameMaxLength = 30;

/// Identificador interno del usuario (ver [slugify]): 'Toño Pérez' -> 'tono-perez'.
String usernameSlug(String username) => slugify(username);

/// Correo interno con el que el servidor identifica al usuario.
String internalEmail(String username) => '${usernameSlug(username)}@$_internalDomain';

/// True si la cuenta guardada es de las sencillas (y no una de empresa con correo real).
bool isSimpleAccount(String email) => email.endsWith('@$_internalDomain');

/// La fecha de nacimiento convertida en contraseña: 15/03/1990 -> '15031990'.
String birthPassword(DateTime date) {
  String two(int n) => n.toString().padLeft(2, '0');
  return '${two(date.day)}${two(date.month)}${date.year}';
}

/// Fecha armada con día, mes y año, o null si falta algo o no existe (31 de febrero).
DateTime? buildBirthDate(int? day, int? month, int? year) {
  if (day == null || month == null || year == null) return null;
  final date = DateTime(year, month, day);
  return date.day == day ? date : null;
}

const _months = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

/// Fecha de nacimiento con tres listas (día, mes, año) en español: no hay nada que
/// teclear ni formato que adivinar. Avisa con [onChanged] la fecha válida o null.
class BirthDateField extends StatefulWidget {
  const BirthDateField({super.key, required this.onChanged, this.enabled = true});

  final ValueChanged<DateTime?> onChanged;
  final bool enabled;

  @override
  State<BirthDateField> createState() => _BirthDateFieldState();
}

class _BirthDateFieldState extends State<BirthDateField> {
  int? _day;
  int? _month;
  int? _year;

  void _update() => widget.onChanged(buildBirthDate(_day, _month, _year));

  @override
  Widget build(BuildContext context) {
    final thisYear = DateTime.now().year;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Fecha de nacimiento', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(
              flex: 2,
              child: DropdownButtonFormField<int>(
                decoration: const InputDecoration(labelText: 'Día'),
                items: [
                  for (var d = 1; d <= 31; d++)
                    DropdownMenuItem(value: d, child: Text('$d')),
                ],
                onChanged: widget.enabled
                    ? (v) {
                        _day = v;
                        _update();
                      }
                    : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 4,
              child: DropdownButtonFormField<int>(
                decoration: const InputDecoration(labelText: 'Mes'),
                items: [
                  for (var m = 1; m <= 12; m++)
                    DropdownMenuItem(value: m, child: Text(_months[m - 1])),
                ],
                onChanged: widget.enabled
                    ? (v) {
                        _month = v;
                        _update();
                      }
                    : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: DropdownButtonFormField<int>(
                decoration: const InputDecoration(labelText: 'Año'),
                items: [
                  for (var y = thisYear; y >= thisYear - 100; y--)
                    DropdownMenuItem(value: y, child: Text('$y')),
                ],
                onChanged: widget.enabled
                    ? (v) {
                        _year = v;
                        _update();
                      }
                    : null,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
