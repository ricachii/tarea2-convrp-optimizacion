# Comparación Gurobi vs. CPLEX

Se resolvió el mismo modelo con los mismos archivos de instancia:
`instancias/inst1.json` e `instancias/inst2.json`. Los resultados por solver se
documentan por separado en [RESULTADOS_GUROBI.md](./RESULTADOS_GUROBI.md) y
[RESULTADOS_CPLEX.md](./RESULTADOS_CPLEX.md).

## Relajación continua

| Instancia | Objetivo Gurobi | Objetivo CPLEX | Diferencia absoluta |
|---|---:|---:|---:|
| inst1 | 494 | 494 | 0 |
| inst2 | 446 | 446 | 0 |

Los valores objetivos coinciden exactamente en las dos instancias, lo que
apoya que ambos solvers resuelven la misma relajación. Los CSV existentes no
guardan el tiempo de la relajación Gurobi, así que no es posible comparar sus
tiempos LP con los tiempos CPLEX de 0,078 s y 0,031 s.

## Modelo entero

| Instancia | Solver | Objetivo | Estado | Gap final | Tiempo (s) | Nodos |
|---|---|---:|---|---:|---:|---:|
| inst1 | Gurobi baseline | 676 | Óptimo | 0 % | 19,89 | 13.066 |
| inst1 | CPLEX | 676 | Óptimo | 0 % | 239,938 | 96.780 |
| inst2 | Gurobi baseline | 812 | Óptimo | 0 % | 47,93 | 24.569 |
| inst2 | CPLEX | 812 | Óptimo | 0 % | 220,391 | 95.176 |

Los dos solvers certificaron el mismo objetivo entero en ambas instancias. En
estas corridas, CPLEX reportó más tiempo y nodos que Gurobi baseline. No se debe
concluir que la diferencia se debe únicamente al solver: Gurobi usó
`Threads=1` y `Seed=0`, mientras que CPLEX se ejecutó con parámetros
predeterminados, sin fijar explícitamente el número de hilos. Además, los nodos
de búsqueda no necesariamente son comparables entre implementaciones.

## Conclusión y cautelas

- **Consistencia de la solución:** igualdad de objetivos LP e enteros en las
  dos instancias.
- **Desempeño medido:** Gurobi baseline fue más rápido en estas corridas, pero
  la configuración de los solvers no está normalizada.
- **Comparación controlada pendiente:** para atribuir diferencias de tiempo al
  solver, repetir en el mismo computador con un hilo en ambos, mismo límite de
  tiempo y parámetros comparables; guardar logs y tiempo de la relajación de
  ambos solvers.
- **Reproducibilidad:** los CSV de Gurobi están en `resultados/`; los de CPLEX
  y sus logs están en `resultados_cplex/`.

