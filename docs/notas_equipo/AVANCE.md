# Avance: lo hecho hasta ahora

Fecha: 2026-10-15. Estado: **parte inicial** (modelo, instancias y código listos; experimentos completos pendientes).

## Archivos creados
| Archivo | Contenido |
|---|---|
| `convrp.py` | Generador de instancias, modelo gurobipy y una función por experimento |
| `instancias/inst1.json` | n=15, 3 días, 3 rutas, 60% clientes con ventana de 60 min, Q = 1.10·demanda_máx_día/R (seed 11) |
| `instancias/inst2.json` | n=16, 3 días, 3 rutas, 75% con ventana de 45 min, Q = 1.05·demanda_máx_día/R (seed 22) |
| `resultados/inst1_configs.csv` | Corrida de prueba con TimeLimit=60 |

## Uso
```
python convrp.py gen
python convrp.py run instancias/inst1.json relax|configs|tune|sens|all --timelimit 600
```
Cada experimento escribe un CSV en `resultados/`.

## Modelo implementado
Restricciones (numeración del paper): (1), (2), (3)–(4), (5), (7), (8), (9)–(10), (11)–(12), (14), (16).

Decisiones de modelado:
- **(3)–(4) por día:** cada nodo con pedido el día t se visita una vez en su ruta asignada (la suma sobre t del paper se interpreta por día).
- **Big-M ajustado por arco:** M_ij = max(0, ub_i + st_i + tt_ij − lb_j), con cotas de W derivadas de ventana y horario del depósito.
- **(8) como cotas de W:** equivalente a la restricción; para nodos sin ventana se usa el horario del depósito.
- **Preproceso de arcos:** se eliminan arcos (i,j,t) infactibles por ventanas y arcos de clientes sin pedido ese día.
- **Sin ruptura de simetría** entre rutas (como en el paper).
- Parámetros fijos: `Threads=1`, `Seed=0`, `TimeLimit` configurable.

## Resultados preliminares (inst1, TimeLimit=60 s)
| Config | Estado | Obj | Gap | Tiempo |
|---|---|---|---|---|
| baseline | óptimo | 676 | 0% | 22.6 s |
| Heuristics=0 | óptimo | 676 | 0% | 20.3 s |
| MIPFocus=3 | óptimo | 676 | 0% | 58.0 s |
| MIPFocus=1 | límite | 676 | 4.9% | 60 s |
| Presolve=0 | límite | 676 | 8.7% | 60 s |
| Cuts=0 | límite | 676 | 9.5% | 60 s |

Las configuraciones producen diferencias claras; inst1 parece no trivial.

## Pendiente
- [ ] Probar inst2 (factibilidad y dificultad); ajustar parámetros si es trivial o infactible.
- [ ] Correr todos los experimentos con `TimeLimit=600` en ambas instancias.
- [ ] Relajación continua y brecha de integralidad.
- [ ] `model.tune()` y comparación contra baseline y mejor manual.
- [ ] Sensibilidad de Q. Ojo: con `Model.fixed()` el `Pi` de la capacidad probablemente sea 0 (Z fijo); interpretar `SARHSLow`/`SARHSUp` como rango de factibilidad y, opcionalmente, re-optimizar con Q±δ.
- [ ] Pitch PDF (máx. 5 min) con modelo en LaTeX, instancias, resultados y discusión.
- [ ] Redactar discusión (el *por qué* de cada efecto) y definir la organización del equipo (5 integrantes).
- [ ] Armar el .zip (PDF, código, instancias) y subir a Canvas antes del 20-oct 23:59.
