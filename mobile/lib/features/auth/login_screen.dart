import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../billing/pricing_screen.dart';
import 'auth_errors.dart';
import 'register_screen.dart';
import 'simple_account.dart';

/// Entrar con nombre de usuario + fecha de nacimiento (ver [simple_account.dart]).
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _username = TextEditingController();
  DateTime? _birthDate;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    // Prellena el usuario de la última vez, para que no haya que reteclearlo.
    _prefill();
  }

  Future<void> _prefill() async {
    final store = ref.read(secureStoreProvider);
    final username = await store.lastCompany;
    final email = await store.lastEmail;
    if (!mounted || username == null || email == null || !isSimpleAccount(email)) return;
    if (_username.text.isEmpty) setState(() => _username.text = username);
  }

  @override
  void dispose() {
    _username.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = _username.text.trim();
    final birthDate = _birthDate;
    if (usernameSlug(username).length < 2 || birthDate == null) {
      setState(() => _error = 'Escribe tu usuario y elige tu fecha de nacimiento.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    final store = ref.read(secureStoreProvider);
    final email = internalEmail(username);
    try {
      await ref.read(authControllerProvider.notifier).login(
            companySlug: usernameSlug(username),
            email: email,
            password: birthPassword(birthDate),
          );
      await store.saveLastLogin(username, email);
      ref.invalidate(savedAccountProvider);
      // Esta pantalla se abre con Navigator.push (desde la entrada rápida o el registro),
      // así que no se cierra sola cuando el AuthGate cambia a la app por debajo: hay que
      // quitarla para que quede a la vista el clóset.
      if (mounted) Navigator.of(context).popUntil((route) => route.isFirst);
    } catch (error) {
      if (mounted) {
        setState(() => _error = authErrorMessage(error, isRegister: false, simple: true));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Entrar')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 8),
            const Text(
              '¿Qué me pongo?',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            const Text(
              'Tu clóset. Tu estilo. Tu mejor versión.',
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
                counterText: '',
              ),
            ),
            const SizedBox(height: 16),
            BirthDateField(
              enabled: !_loading,
              onChanged: (date) => setState(() => _birthDate = date),
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
                child: Text(
                  _error!,
                  style: const TextStyle(color: Color(0xFFB91C1C)),
                ),
              ),
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _loading ? null : _submit,
              child: Text(_loading ? 'Entrando…' : 'Entrar'),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: _loading
                  ? null
                  : () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => const RegisterScreen(),
                        ),
                      ),
              child: const Text('¿No tienes cuenta? Crear una'),
            ),
            const SizedBox(height: 12),
            TextButton.icon(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(builder: (_) => const PricingScreen()),
              ),
              icon: const Icon(Icons.sell_outlined),
              label: const Text('Ver planes y precios'),
            ),
          ],
        ),
      ),
    );
  }
}
