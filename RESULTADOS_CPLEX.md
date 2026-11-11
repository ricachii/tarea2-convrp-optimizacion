# Resultados de CPLEX

Este archivo documenta únicamente las corridas realizadas con CPLEX mediante
`convrp_cplex.py`. Se utilizó el motor de CPLEX Studio 22.2 configurado en el
entorno local y las instancias compartidas en `instancias/`.

## Resultados

| Instancia | Modelo | Estado | Objetivo | Cota | Gap final | Tiempo (s) | Nodos |
|---|---|---|---:|---:|---:|---:|---:|
| inst1 | Relajación continua | Óptimo | 494 | — | — | 0,078 | 0 |
| inst1 | Entero | Óptimo | 676 | 676 | 0 % | 239,938 | 96.780 |
| inst2 | Relajación continua | Óptimo | 446 | — | — | 0,031 | 0 |
| inst2 | Entero | Óptimo | 812 | 812 | 0 % | 220,391 | 95.176 |

El gap y la cota se informan para los modelos enteros. La relajación se resolvió
como un LP continuo, por lo que el CSV deja esos campos vacíos.

## Interpretación

El modelo entero alcanzó óptimo en ambas instancias y confirmó los objetivos
enteros previamente obtenidos con Gurobi. Los objetivos LP de CPLEX también
coinciden con los registrados por Gurobi: 494 para inst1 y 446 para inst2.

## Reproducibilidad y salidas

El script construye la misma formulación y lee directamente los JSON de
`instancias/`. No modifica los resultados Gurobi. Los CSV y logs de estas
corridas están separados en `resultados_cplex/`.

Comandos de ejemplo:

```powershell
python convrp_cplex.py run .\instancias\inst1.json all --timelimit 600
python convrp_cplex.py run .\instancias\inst2.json all --timelimit 600
```

En estas corridas CPLEX se ejecutó con sus parámetros predeterminados y con
límite de tiempo de 600 s por modelo. No se fijó explícitamente el número de
hilos. Esto debe tenerse en cuenta al interpretar la comparación de tiempos y
nodos con Gurobi, cuyo código fija `Threads=1`.

