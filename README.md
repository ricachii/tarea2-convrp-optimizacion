# Tarea Computacional 3 - conVRP: Gurobi vs. CPLEX

Optimización I (580451-1), UdeC. Grupo 1.

Rama de trabajo: `tarea3` (la Tarea 2 queda en `tarea2` / etiqueta `entrega-tc2`).

## Pasos en la máquina de corridas

```
git clone https://github.com/ricachii/tarea2-convrp-optimizacion
cd tarea2-convrp-optimizacion
git checkout tarea3
pip install -r requirements.txt
python verificar_entorno.py
```

`verificar_entorno.py` imprime un bloque con las versiones y comprueba que ambas
licencias aceptan modelos más grandes que las instancias. Si CPLEX falla con el
error 1016 (Community Edition), definir antes `CPLEX_STUDIO_DIR222` con la ruta de
CPLEX Studio 22.2.

## Experimentos

Parámetros: `Threads=1`, `TimeLimit=600 s`; el resto en la configuración por
defecto. Cerrar otros programas y correr un solver a la vez (el script ya lo hace).

```
python convrp_tc3.py run instancias/inst1.json compare
python convrp_tc3.py run instancias/inst2.json compare
# opcional: hilos por defecto en ambos
python convrp_tc3.py run instancias/inst1.json compare --threads 0
```

Salidas: `resultados/*.csv`, `resultados/*_sol.json` y `logs/{inst}_{solver}_{relax|mip}.log`.

## Archivos

| Archivo | Contenido |
|---|---|
| `convrp_tc3.py` | Preproceso compartido, modelos Gurobi y CPLEX, experimentos |
| `verificar_entorno.py` | Chequeo de Python, licencias y límites de tamaño |
| `convrp.py` | Código de la Tarea 2 (referencia, sin cambios) |
| `instancias/` | inst1.json, inst2.json |
| `docs/` | Retroalimentación TC2 y notas del equipo (no van al .zip) |
| `previo/` | Corridas previas de CPLEX con 8 hilos (no son resultados finales) |
