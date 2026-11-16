# Comparación Gurobi vs CPLEX

Generada por `graficos_tc3.py` a partir de `resultados/*_compare_gurobi-cplex_*.csv`. Razón = CPLEX / Gurobi (>1: CPLEX es más lento / explora más nodos). Las filas de relajación no tienen nodos.

| Instancia | Modelo | Hilos | Obj Gurobi | Obj CPLEX | Tiempo Gurobi (s) | Tiempo CPLEX (s) | Razón tiempo | Nodos Gurobi | Nodos CPLEX | Razón nodos |
|---|---|---|---|---|---|---|---|---|---|---|
| inst1 | Relajación | 1 | 494.0 | 494.0 | 0.081 | 0.062 | 0.77 | — | — | — |
| inst1 | Relajación | defecto | 494.0 | 494.0 | 0.041 | 0.016 | 0.39 | — | — | — |
| inst1 | MIP | 1 | 676.0 | 676.0 | 49.930 | 335.750 | 6.72 | 10,097 | 56,028 | 5.55 |
| inst1 | MIP | defecto | 676.0 | 676.0 | 23.856 | 142.438 | 5.97 | 13,413 | 117,164 | 8.74 |
| inst2 | Relajación | 1 | 446.0 | 446.0 | 0.033 | 0.015 | 0.45 | — | — | — |
| inst2 | Relajación | defecto | 446.0 | 446.0 | 0.035 | 0.031 | 0.89 | — | — | — |
| inst2 | MIP | 1 | 812.0 | 812.0 | 126.796 | 294.797 | 2.32 | 21,192 | 54,009 | 2.55 |
| inst2 | MIP | defecto | 812.0 | 812.0 | 48.741 | 182.078 | 3.74 | 30,205 | 201,164 | 6.66 |

Notas: tiempos de relajación de ~0.01–0.08 s son ruido de medición; no comparar sus razones. 
