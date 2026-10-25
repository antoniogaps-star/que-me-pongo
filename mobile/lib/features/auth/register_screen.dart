import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import 'auth_errors.dart';
import 'login_screen.dart';
import 'simple_account.dart';

/// Registro sencillo: solo un nombre de usuario y la fecha de nacimiento (que hace de
/// contraseña). Sin empresa, sin correo. Ver [simple_account.dart] para cómo se
/// traduce a la cuenta que espera el servidor.
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _username = TextEditingController();
  DateTime? _birthDate;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = _username.text.trim();

    // Validación amigable antes de llamar al servidor.
    if (usernameSlug(username).length < 2) {
      setState(() => _error = 'Escribe tu nombre de usuario (al menos 2 letras o números).');
      return;
    }
    final birthDate = _birthDate;
    if (birthDate == null) {
      setState(() => _error = 'Elige tu fecha de nacimiento (día, mes y año).');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    final store = ref.read(secureStoreProvider);
    final email = internalEmail(username);
    try {
      await ref.read(authControllerProvider.notifier).register(
            companyName: username,
            companySlug: usernameSlug(username),
            email: email,
            password: birthPassword(birthDate),
          );
      // Éxito: la sesión ya es real. Se recuerda el usuario para el próximo ingreso
      // (pantalla "Entrar") y el AuthGate mostrará la app.
      await store.saveLastLogin(username, email);
      ref.invalidate(savedAccountProvider);
      // Si esta pantalla se abrió empujada (desde "Entrar"), no se cierra sola cuando el
      // AuthGate cambia a la app por debajo; se quita para dejar a la vista el clóset.
      // Si es la pantalla inicial (raíz), popUntil no hace nada: seguro en ambos casos.
      if (mounted) Navigator.of(context).popUntil((route) => route.isFirst);
    } catch (e) {
      if (mounted) setState(() => _error = authErrorMessage(e, isRegister: true, simple: true));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Crear cuenta')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              '¿Qué me pongo?',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            const Text(
              'Solo dos datos y listo.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _username,
              enabled: !_loading,
              maxLength: usernameMaxLength,
              textCapitalization: TextCapitalization.words,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'Nombre de usuario',
                hintText: 'Ej: Toño Pérez',
                counterText: '',
              ),
            ),
            const SizedBox(height: 16),
            BirthDateField(
              enabled: !_loading,
              onChanged: (date) => setState(() => _birthDate = date),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tu fecha de nacimiento será tu contraseña para entrar.',
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEE2E2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(_error!, style: const TextStyle(color: Color(0xFFB91C1C))),
              ),
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _loading ? null : _submit,
              child: Text(_loading ? 'Creando…' : 'Crear cuenta'),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: _loading
                  ? null
                  : () => Navigator.of(context).push(
                        MaterialPageRoute<void>(builder: (_) => const LoginScreen()),
                      ),
              child: const Text('¿Ya tienes cuenta? Entrar'),
            ),
            const SizedBox(height: 4),
            const Text(
              'La primera vez puede tardar hasta ~1 minuto mientras el servidor despierta.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
