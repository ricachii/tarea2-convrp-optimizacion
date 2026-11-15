# Resultados de Gurobi

Este archivo documenta únicamente las corridas realizadas con Gurobi usando
`convrp.py`. Las instancias son las mismas que se usan en la comparación con
CPLEX y se encuentran en `instancias/`.

## Resultados del modelo entero

Los valores corresponden a `baseline` en los archivos
`resultados/inst1_configs.csv` y `resultados/inst2_configs.csv`.

| Instancia | Estado | Objetivo | Cota | Gap final | Tiempo (s) | Nodos |
|---|---:|---:|---:|---:|---:|---:|
| inst1 | Óptimo | 676 | 676 | 0 % | 19,89 | 13.066 |
| inst2 | Óptimo | 812 | 812 | 0 % | 47,93 | 24.569 |

La corrida `Cuts=0` de inst2 alcanzó el límite de 600 s con incumbente 812,
cota 781 y gap reportado de 3,818 %. El resto de las configuraciones guardadas
en los CSV alcanzó óptimo.

## Relajación continua y brecha de integralidad

| Instancia | Objetivo LP | Objetivo entero | Brecha de integralidad |
|---|---:|---:|---:|
| inst1 | 494 | 676 | 26,92 % |
| inst2 | 446 | 812 | 45,07 % |

La brecha se calcula como
`100 × (objetivo entero − objetivo LP) / objetivo entero`.
Los CSV de relajación no registran el tiempo de resolución LP; por ello ese
tiempo no se incluye aquí.

## Comparación de configuraciones

| Instancia | Configuración | Tiempo (s) | Objetivo | Gap final | Nodos | Estado |
|---|---|---:|---:|---:|---:|---|
| inst1 | baseline | 19,89 | 676 | 0 % | 13.066 | Óptimo |
| inst1 | Cuts=0 | 140,29 | 676 | 0 % | 181.318 | Óptimo |
| inst1 | Presolve=0 | 145,55 | 676 | 0 % | 62.304 | Óptimo |
| inst1 | MIPFocus=1 | 137,74 | 676 | 0 % | 193.007 | Óptimo |
| inst1 | MIPFocus=3 | 49,98 | 676 | 0 % | 4.870 | Óptimo |
| inst1 | Heuristics=0 | 17,69 | 676 | 0 % | 11.985 | Óptimo |
| inst2 | baseline | 47,93 | 812 | 0 % | 24.569 | Óptimo |
| inst2 | Cuts=0 | 600,00 | 812 | 3,818 % | 1.220.695 | Límite de tiempo |
| inst2 | Presolve=0 | 87,52 | 812 | 0 % | 48.964 | Óptimo |
| inst2 | MIPFocus=1 | 205,08 | 812 | 0 % | 230.396 | Óptimo |
| inst2 | MIPFocus=3 | 86,50 | 812 | 0 % | 10.803 | Óptimo |
| inst2 | Heuristics=0 | 53,51 | 812 | 0 % | 28.752 | Óptimo |

## Configuración y archivos fuente

El código establece `Threads=1`, `Seed=0` y el límite de tiempo solicitado en
la línea de comandos. Las opciones de configuración se ejecutan por separado.
Los resultados originales están en `resultados/`; este documento no modifica
esos CSV.

Comando de ejemplo:

```powershell
python convrp.py run .\instancias\inst1.json all --timelimit 600
```

