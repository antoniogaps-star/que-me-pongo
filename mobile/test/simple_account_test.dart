import 'package:flutter_test/flutter_test.dart';
import 'package:quemepongo_mobile/features/auth/simple_account.dart';

void main() {
  test('la fecha de nacimiento se vuelve una contraseña de 8 dígitos', () {
    expect(birthPassword(DateTime(1990, 3, 5)), '05031990');
    expect(birthPassword(DateTime(2001, 12, 31)), '31122001');
  });

  test('el usuario se traduce igual al registrarse y al entrar', () {
    expect(usernameSlug('Toño Pérez'), 'tono-perez');
    expect(internalEmail('  Toño Pérez '), 'tono-perez@usuarios.quemepongo.app');
    expect(isSimpleAccount(internalEmail('Toño')), isTrue);
    expect(isSimpleAccount('tono@gmail.com'), isFalse);
  });

  test('una fecha que no existe no se acepta', () {
    expect(buildBirthDate(31, 2, 1990), isNull);
    expect(buildBirthDate(29, 2, 2000), DateTime(2000, 2, 29));
    expect(buildBirthDate(null, 2, 2000), isNull);
  });

  test('el usuario más largo cabe en el correo interno', () {
    final largo = 'a' * usernameMaxLength;
    expect(internalEmail(largo).split('@').first.length, lessThanOrEqualTo(64));
  });
}
