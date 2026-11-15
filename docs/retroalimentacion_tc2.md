# Retroalimentación de la Tarea 2

El grupo no recibió comentarios específicos sobre la Tarea 2. Se asume que lo
marcado fue la forma de mostrar y explicar las ecuaciones (3)-(4).

## Revisión del modelo contra las sugerencias del enunciado

| Sugerencia | Estado | Evidencia |
|---|---|---|
| No forzar (3)-(4) para clientes sin demanda ese día | Ya cumplido | Se imponen solo para (j,t) ∈ O (`for j in pedidos[t]`, `convrp.py` líneas 117-123); los arcos del día t solo incluyen clientes con q_it > 0 |
| Tamaño mínimo (15 clientes, 3 días, 3 rutas) | Cumplido | inst1: 15/3/3; inst2: 16/3/3 |
| Estructura multi-día real | Cumplido | Cada cliente pide con probabilidad 0,85 por día (inst1: 42 de 45 pedidos posibles; inst2: 41 de 48) |
| Formulación algebraica | Corregido en la presentación | (3)-(4) se escriben explícitamente con ∀(j,t)∈O, donde O = {(i,t) : q_it > 0}; se definen también los Big-M |

## Corrección aplicada

- (3): Σ_{i:(i,j,t)∈A} X^r_ijt = Z^r_j, ∀(j,t)∈O, ∀r∈R
- (4): Σ_{j:(i,j,t)∈A} X^r_ijt = Z^r_i, ∀(i,t)∈O, ∀r∈R

Las instancias y el modelo no cambian; por eso se esperan los mismos valores
que en la Tarea 2 (z_LP = 494 / 446, z_MILP = 676 / 812).
