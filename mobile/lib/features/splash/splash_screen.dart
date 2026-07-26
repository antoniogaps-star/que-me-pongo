import 'package:flutter/material.dart';

import '../../core/theme.dart';

/// Pantalla de bienvenida: el gancho-interrogante en oro sobre negro, con el nombre y
/// el eslogan. Se muestra un instante al abrir y luego cede el paso al AuthGate.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    return Scaffold(
      backgroundColor: Marca.negro,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'assets/branding/logo_mark.png',
              width: width * 0.34,
              fit: BoxFit.contain,
            ),
            const SizedBox(height: 26),
            const Text(
              '¿Qué me pongo?',
              style: TextStyle(
                fontFamily: Marca.serif,
                color: Marca.oroClaro,
                fontSize: 34,
              ),
            ),
            const SizedBox(height: 16),
            const FileteOro(),
            const SizedBox(height: 16),
            const Text(
              'TU CLÓSET · TU ESTILO · TU MEJOR VERSIÓN',
              style: TextStyle(
                color: Marca.textoSuave,
                fontSize: 11,
                letterSpacing: 2.2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
