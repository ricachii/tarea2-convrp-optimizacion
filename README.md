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

Presentada: hilos por defecto (`--threads 0`; 8 hilos en los logs). Control: 1 hilo
(`--threads 1`, anexo). `TimeLimit=600 s` en ambos; el resto en la configuración por
defecto de cada solver. Cerrar otros programas antes de correr. El script ejecuta un
solver a la vez, imprime al inicio el plan y al final un resumen.

```
python convrp_tc3.py final      # control con 1 hilo: inst1 e inst2, ambos solvers, relax y mip (--threads 1, 600 s)
python convrp_tc3.py extra      # comparación presentada: lo mismo con hilos por defecto (--threads 0)
```

Corridas sueltas:

```
python convrp_tc3.py run instancias/inst1.json relax --solver cplex
python convrp_tc3.py run instancias/inst2.json mip --solver gurobi --timelimit 600
python convrp_tc3.py run instancias/inst1.json compare [--threads 0]
```

Salidas (los hilos van siempre en el nombre: `h1` = 1 hilo, `hdef` = por defecto):
- `logs/{inst}_{solver}_{relax|mip}_{h1|hdef}.log`
- `resultados/{inst}_{exp}_{solver(es)}_{h1|hdef}.csv` (incluye timelimit, fecha y estado en texto)
- `resultados/{inst}_{solver}_mip_{h1|hdef}_sol.json` (solución, para graficar)

El script **aborta si algún log o CSV ya existe**, para no sobrescribir
resultados. Con `--force` se sobrescribe (por ejemplo, `python convrp_tc3.py final --force`).

## Archivos

| Archivo | Contenido |
|---|---|
| `convrp_tc3.py` | Preproceso compartido, modelos Gurobi y CPLEX, experimentos |
| `verificar_entorno.py` | Chequeo de Python, licencias y límites de tamaño |
| `convrp.py` | Código de la Tarea 2 (referencia, sin cambios) |
| `instancias/` | inst1.json, inst2.json |
| `docs/` | Retroalimentación TC2 y notas del equipo (no van al .zip) |
| `previo/` | Corridas previas de CPLEX con 8 hilos (no son resultados finales) |
