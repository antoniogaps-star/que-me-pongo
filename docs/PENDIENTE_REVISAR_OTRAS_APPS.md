# Pendiente: revisar el aislamiento en Ágora y Sonrisa

**Estado: AGENDADO. Se corrigen en cuanto "¿Qué me pongo?" quede terminada**
(decisión de Toño, 26 jul 2026). No se ha tocado nada de esas dos apps todavía.

## Qué pasó aquí

En "¿Qué me pongo?", ya desplegada, se detectó que **una cuenta veía el clóset de otra**.

El aislamiento entre usuarios estaba confiado por completo a las políticas RLS de
Postgres. En local el rol de la base es limitado y las políticas aplican — por eso las
pruebas pasaban. En Neon el rol tiene privilegios elevados y **las ignora**, así que en
producción no filtraba nada.

Arreglado el 26 jul 2026 (commit `7c92e8c`): toda consulta filtra por `tenant_id` en el
código, además de RLS. Hay prueba de regresión que reproduce el escenario de Neon.

## Por qué esto salpica a las otras dos

Las tres apps se construyeron con el mismo esqueleto: Ágora → Sonrisa → ¿Qué me pongo?.
El patrón defectuoso se copió junto con lo demás. Las carpetas y los despliegues están
separados; lo que se comparte es el **plano**, no los datos.

Consultas que confían solo en RLS (encontradas al leer, sin modificar nada):

- **Ágora** — `backend/app/modules/accounting/service.py:31`, entre otras
- **Sonrisa** — `backend/app/modules/appointments/service.py:36`,
  `backend/app/modules/accounting/service.py:31`, entre otras

## El riesgo, en claro

Si esas apps corren en Neon con la misma configuración, **un cliente podría ver los datos
de otro cliente**: ventas y caja en Ágora; pacientes, citas y cobros en Sonrisa.

No está confirmado — haría falta comprobarlo con dos cuentas de prueba en cada una.

## Cuando se retome

1. **Verificar primero, sin cambiar nada:** crear dos cuentas de prueba y ver si una
   alcanza los datos de la otra.
2. **Si se confirma**, aplicar el mismo arreglo que aquí, cada app en su carpeta y con su
   propio despliegue: filtro por `tenant_id` en cada consulta + la prueba de regresión
   (`tests/integration/test_aislamiento_sin_rls.py` sirve de plantilla).
3. **Endurecer la base** (opcional pero recomendable): crear en Neon un rol de aplicación
   sin privilegios elevados, para que RLS vuelva a ser una segunda cerradura real.

## Además: corregir la skill

La skill `app-negocio` enseña el patrón con el fallo. Al retomar esto, actualizar
`references/backend.md` y `references/lecciones-aprendidas.md` para que la próxima app no
nazca con el mismo problema.
