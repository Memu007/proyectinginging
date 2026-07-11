# PentestGPT-NG

Framework modular de pentesting asistido por IA, orientado exclusivamente a entornos y objetivos autorizados.

## Estado

Proyecto en inicialización. La primera etapa construirá un núcleo verificable con:

- proveedores LLM intercambiables;
- sesiones persistentes;
- separación Planner–Executor;
- manifiesto de alcance obligatorio;
- auditoría de decisiones y resultados;
- estados explícitos para impedir reportar como verificado lo que no fue probado.

## Principios

1. No ejecutar acciones fuera del alcance autorizado.
2. No aceptar comandos de shell libres generados por una LLM.
3. No marcar hallazgos como confirmados sin evidencia reproducible.
4. Mantener herramientas, conocimiento y orquestación como capas separadas.
5. Incorporar capacidades de forma secuencial y con pruebas de regresión.

## Desarrollo

El trabajo se realizará mediante ramas `agent/*` y pull requests borrador. El código ofensivo y las integraciones con herramientas se incorporarán después de completar el núcleo, el control de alcance y el sandbox.
