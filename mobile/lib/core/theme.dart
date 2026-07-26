import 'package:flutter/material.dart';

/// La identidad de "¿Qué me pongo?": oro sobre negro. Elegante, aspiracional — la app
/// tiene que sentirse como un asesor de imagen caro, no como una lista de pendientes.
abstract final class Marca {
  static const Color oro = Color(0xFFD4B483);
  static const Color oroClaro = Color(0xFFE8CFA0);
  static const Color oroHondo = Color(0xFFB8935C);
  static const Color negro = Color(0xFF0B0B0C);
  static const Color carbon = Color(0xFF17161A);
  static const Color texto = Color(0xFFEDE6DA);
  static const Color textoSuave = Color(0xFFB9AE9C);

  /// Familia serif: le da el aire editorial del logo.
  static const String serif = 'serif';

  static ThemeData get tema {
    const esquema = ColorScheme.dark(
      primary: oro,
      onPrimary: negro,
      secondary: oroClaro,
      onSecondary: negro,
      surface: carbon,
      onSurface: texto,
      error: Color(0xFFE08A7A),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: esquema,
      scaffoldBackgroundColor: negro,
      appBarTheme: const AppBarTheme(
        backgroundColor: negro,
        foregroundColor: oro,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          fontFamily: serif,
          color: oroClaro,
          fontSize: 21,
          letterSpacing: 0.6,
        ),
      ),
      cardTheme: CardThemeData(
        color: carbon,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFF2A2620)),
        ),
      ),
      chipTheme: const ChipThemeData(
        backgroundColor: carbon,
        selectedColor: oro,
        side: BorderSide(color: Color(0xFF3A342B)),
        labelStyle: TextStyle(color: texto),
        secondaryLabelStyle: TextStyle(color: negro, fontWeight: FontWeight.w600),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: oro,
          foregroundColor: negro,
          minimumSize: const Size.fromHeight(54),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: oro,
          minimumSize: const Size.fromHeight(50),
          side: const BorderSide(color: oroHondo),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: carbon,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF3A342B)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF3A342B)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: oro),
        ),
        labelStyle: const TextStyle(color: textoSuave),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: carbon,
        indicatorColor: oro.withValues(alpha: 0.22),
        labelTextStyle: WidgetStateProperty.all(
          const TextStyle(color: textoSuave, fontSize: 12),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected) ? oro : textoSuave,
          ),
        ),
      ),
      snackBarTheme: const SnackBarThemeData(
        backgroundColor: carbon,
        contentTextStyle: TextStyle(color: texto),
      ),
    );
  }
}

/// El filete ornamental del logo: dos líneas y un rombo. Se usa bajo los títulos.
class FileteOro extends StatelessWidget {
  const FileteOro({super.key, this.ancho = 110});

  final double ancho;

  @override
  Widget build(BuildContext context) {
    Widget linea() => Container(width: ancho / 2, height: 1, color: Marca.oro);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        linea(),
        const SizedBox(width: 10),
        Transform.rotate(
          angle: 0.785398, // 45°
          child: Container(width: 7, height: 7, color: Marca.oro),
        ),
        const SizedBox(width: 10),
        linea(),
      ],
    );
  }
}
