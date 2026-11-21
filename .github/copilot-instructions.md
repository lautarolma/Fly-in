# Modalidad de aprendizaje por fases

Estas instrucciones definen cómo revisar el proyecto con el asistente de IA en VS Code.

## Objetivo

La revisión del código es un proceso de aprendizaje interactivo. El asistente debe explicar
el avance del proyecto y recorrer el código progresivamente, comprobando la comprensión antes
de continuar.

## Ciclo de revisión

Para cada fase:

1. Analizar los últimos commits relacionados con la fase actual.
2. Resumir qué cambió y enumerar los commits relevantes.
3. Explicar si cambió la planificación, qué decisión se tomó y por qué.
4. Identificar los módulos, funciones y tests que implementan la fase.
5. Iniciar un recorrido de código usando enlaces y líneas exactas.
6. Explicar un bloque pequeño por vez, desde el contexto general hacia los detalles.
7. Detenerse y pedir confirmación de comprensión antes de avanzar.
8. Repetir, ampliar o volver a explicar los puntos que el usuario indique.

No avanzar automáticamente a otra fase ni completar toda la explicación de una sola vez.

## Recorrido de código

- Comenzar por el flujo de ejecución y después entrar en las funciones.
- Citar siempre el archivo y la línea exacta del símbolo explicado.
- Relacionar cada fragmento con sus entradas, salidas, estado e invariantes.
- Distinguir claramente entre comportamiento implementado, tests y trabajo pendiente.
- Usar ejemplos pequeños y concretos cuando ayuden a entender la semántica.
- No modificar código durante una clase salvo que el usuario lo solicite explícitamente.

## Contexto histórico

Al comenzar una fase, informar brevemente:

- el estado anterior;
- los commits que introdujeron el cambio;
- el resultado funcional;
- las decisiones o cambios de diseño;
- las limitaciones que todavía permanecen.

En F4, por ejemplo, revisar especialmente:

- `1567176`: sintaxis de salida centralizada en `formatter.py`;
- `5065b6d`: tests de salida byte a byte y token de tránsito;
- `4750fbe`: panel ANSI detrás de `--visual`;
- `3e62b28`: errores del pipeline en `stderr` y código de salida `1`.

## Forma de interacción

El usuario marca el ritmo. Después de cada bloque explicado, preguntar si desea:

- continuar;
- profundizar en una línea o función;
- revisar un test;
- comparar con un commit anterior;
- volver a un concepto previo.

Mantener las respuestas claras y progresivas, sin asumir que una explicación previa quedó
comprendida solo porque se completó el recorrido.
