# Estado de la Tarea 3 (para retomar en otra máquina)

Documento autocontenido. Última actualización: 2026-11-15.

## 1. Objetivo
Tarea Computacional 3 de Optimización I (580451-1, UdeC, profesora Rosa Medina Durán): reimplementar en CPLEX el modelo de ruteo consistente reducido (conVRP, Campelo et al., 2019) de la Tarea 2, corrigiendo lo detectado en TC2, y comparar Gurobi vs. CPLEX (relajación continua y modelo entero: objetivo, tiempo, nodos, gap).

- **Entrega:** .zip en Canvas el **martes 17-nov-2026, antes de las 23:59** (idealmente antes de las 18:00).
- **Presentación:** **miércoles 18-nov-2026** (pitch en PDF, máximo 5 minutos).
- **Contenido del .zip:** presentación PDF, código `.py` (no notebook) con ambos solvers, instancias, logs de los solvers.
- **Rúbrica (34 pts):** formulación algebraica 5, instancias 5, implementación CPLEX 5, validación cruzada 3, comparación de desempeño 3, discusión 5, .py y .log 3, exposición 3, organización del equipo 2.
- Equipo (Grupo 1): Benjamín Díaz Villalobos, Rodrigo Bascuñán León, Nicolás Ricciardi Acuña, Martín Tapia Medina.

## 2. Estado del repo
Remoto: `https://github.com/ricachii/tarea2-convrp-optimizacion`

| Rama / etiqueta | Punta | Contenido |
|---|---|---|
| `tarea2` | `6269fce` | Estado entregado de la Tarea 2: `convrp.py`, `instancias/`, `resultados/` (Gurobi), `AVANCE.md`, `CONTEXTO.md`. No se toca. |
| etiqueta `entrega-tc2` | `6269fce` | Mismo commit que `tarea2`. |
| `main` | `afcc252` | `tarea2` + 4 commits de CondorPepinillo (11-nov) con el primer intento de CPLEX (8 hilos). No se toca. |
| `tarea3` | ver `git log -1` (parte de `afcc252`) | Todo el trabajo nuevo. **Todo va aquí.** |

Commits de `tarea3` sobre `afcc252` hechos en esta sesión: `547a7e5` y `6e51411` (más el commit que agrega este documento).

## 3. Lo hecho en esta sesión (en orden)
1. **Diagnóstico (solo lectura):** se clonó el repo. Historial: commits de Tarea 2 (15 y 17-oct) y 4 commits de CondorPepinillo del 11-nov con CPLEX (`convrp_cplex.py`, logs, CSV, MD de comparación). `convrp.py`, instancias y resultados coinciden con lo esperado: z_LP = 494 / 446 y z_MILP = 676 / 812, 1.680 y 1.629 binarias.
2. **Revisión del modelo:** (3)-(4) ya se imponen solo para (j,t) con pedido y los arcos solo incluyen clientes con pedido ese día; las instancias ya tienen estructura multi-día. No se cambió el modelo ni las instancias. Detalle en `docs/retroalimentacion_tc2.md`.
3. **Retroalimentación de TC2:** el usuario indicó "no hay". Se asumió que lo marcado fue cómo se mostró (3)-(4): en la formulación deben escribirse explícitamente con ∀(j,t)∈O, donde O = {(i,t) : q_it > 0}.
4. **Ramas:** `tarea2` y etiqueta `entrega-tc2` en `6269fce`; `tarea3` desde `afcc252`. Subidas a origin con `git push -u origin tarea2 tarea3` y `git push origin entrega-tc2`.
5. **Reorganización (commit `547a7e5`):**
   - `AVANCE.md`, `CONTEXTO.md`, `RESULTADOS_CPLEX.md`, `RESULTADOS_GUROBI.md`, `COMPARACION_GUROBI_CPLEX.md` pasaron a `docs/notas_equipo/` (informales, no van al .zip).
   - `convrp_cplex.py` pasó a `previo/convrp_cplex_8hilos.py` (se borró el comentario informal de la línea 17).
   - `resultados_cplex/` pasó a `previo/resultados_cplex_8hilos/`. Esas corridas (CPLEX con 8 hilos: inst1 en 240 s, inst2 en 220 s) **no son resultados finales**.
6. **Código nuevo (commit `6e51411`):** `convrp_tc3.py`, `verificar_entorno.py`, `README.md`, `requirements.txt`, `docs/retroalimentacion_tc2.md`.
7. **Verificación del contenido de `tarea2`:** contiene todo el código, instancias y resultados de Gurobi; los 4 commits de `main` posteriores solo agregan archivos de CPLEX y no tocan `convrp.py`, `instancias/` ni `resultados/`.

## 4. Diseño de `convrp_tc3.py`
- **`preproceso(inst)`**: único para ambos solvers. Devuelve `lb`, `ub` (cotas de W), `pedidos` (O por día), `arcos` por día (solo clientes con pedido ese día más depósitos y arco (0, n+1); se conserva (i,j) si `lb_i + st_i + tt_ij <= ub_j`) y los Big-M: `M7[(i,j)]`, `M9[j]`, `M10[i]`.
- **`construir_modelo_gurobi(inst, pre)`** y **`construir_modelo_cplex(inst, pre, relajacion)`** (docplex): ecuaciones (1), (2), (3)-(4), (5), (7), (9)-(10), (11)-(12), (14), (16). (8) va como cotas de W.
- **`importar_cplex()`**: si existe la variable de entorno `CPLEX_STUDIO_DIR222` (Windows), carga antes `cplex2220.dll` con ctypes; si no, usa el API normal. Error claro si la ruta no tiene la DLL, si falta docplex o si aparece el límite de la Community Edition (error 1016).
- **Experimentos:** `relax` (Gurobi: `relax()`; CPLEX: variables continuas), `mip`, `compare` (ambos solvers, uno tras otro).
- **Uso:**
  ```
  python convrp_tc3.py run instancias/inst1.json compare
  python convrp_tc3.py run instancias/inst2.json compare
  python convrp_tc3.py run <inst> <relax|mip|compare> [--solver gurobi|cplex|both] [--timelimit 600] [--threads 1]
  ```
  `--threads 0` usa los hilos por defecto del solver (corrida opcional); los archivos llevan el sufijo `_hilosdef`.
- **Salidas:** `logs/{inst}_{solver}_{relax|mip}.log`; `resultados/{inst}_{exp}_{solvers}.csv` (campos: solver, modelo, hilos, estado, obj, cota, gap_pct, nodos, tiempo_s, n_bin, n_rest, log); `resultados/{inst}_{solver}_mip_sol.json` (Z y arcos X de la solución, para graficar).
- **Verificado:** el preproceso reproduce 1.680 (inst1) y 1.629 (inst2) binarias. Las funciones de resolución con solvers **no se ejecutaron** (ver sección 5).

## 5. Entorno de la máquina de esta sesión
- Python 3.10.11 (64 bits), Windows.
- Faltan `gurobipy`, `docplex` y `cplex`; matplotlib no está instalado.
- No hay CPLEX Studio y `CPLEX_STUDIO_DIR222` no está definida.
- Por eso **no sirve para las corridas finales**: no puede ejecutar ningún solver. Solo sirvió para escribir y probar el preproceso.

## 6. Decisiones tomadas
- Comparación principal con `Threads=1` y `TimeLimit=600` en ambos solvers (declarado en la presentación); el resto en la configuración por defecto. Opcional si sobra tiempo: corrida extra con hilos por defecto en ambos.
- Preproceso compartido en un solo archivo (`convrp_tc3.py`).
- Corridas finales en la **máquina del compañero con CPLEX Studio 22.2**, un solver a la vez, con logs de Gurobi y tiempos de relajación incluidos. Se rehacen todas (las previas de 8 hilos no valen).
- ctypes solo si hace falta `CPLEX_STUDIO_DIR222`.
- `.md` informales fuera del .zip. `convrp.py` queda intacto como referencia de TC2.
- Instancias y modelo sin cambios (se esperan los mismos valores de TC2 salvo diferencia numérica).
- Commits en español, **sin** líneas `Co-Authored-By` ni atribución a Claude; revisar con `git log --format=%B -n 3` antes de cada push.
- Avisar antes de lanzar cualquier corrida larga (hasta 600 s cada una).

## 7. Pendientes (en orden)
| | Tarea | Estado |
|---|---|---|
| a | El compañero corre `verificar_entorno.py` y pega la salida | Pendiente; bloquea (b) |
| b | Corridas finales (`compare` en inst1 e inst2; opcional `--threads 0`) | Bloqueado por (a); no ejecutado |
| c | Gráficos: mapa de instancias (depósito, clientes numerados, ventanas), rutas coloreadas con `*_sol.json`, barras de tiempo y nodos | Instancias se pueden graficar ya; los de rutas y comparación bloqueados por (b); no ejecutado |
| d | Discusión: causas de diferencias (presolve, cortes, heurísticas; nodos no comparables 1 a 1) con evidencia de los logs; límites honestos (una semilla, instancias pequeñas, un computador) | Bloqueado por (b) |
| e | Diapositivas (PDF, máximo 5 min, 10-12 láminas, con formulación ∀(j,t)∈O y Big-M) | El modelo y las correcciones se pueden hacer ya; resultados bloqueados por (b) |
| f | .zip: presentación PDF, `convrp_tc3.py`, `verificar_entorno.py`, `instancias/`, `logs/`, `resultados/`; subir antes de las 18:00 del 17-nov | Bloqueado por (b)-(e) |

## 8. Cómo retomar en otra máquina
```
git clone https://github.com/ricachii/tarea2-convrp-optimizacion
cd tarea2-convrp-optimizacion
git checkout tarea3
git pull origin tarea3
pip install -r requirements.txt
python verificar_entorno.py
```
Configurar la identidad de git **solo en este repo** (sin `--global`):
```
git config user.name "Nicolás Renato Ricciardi Acuña"
git config user.email "114707269+ricachii@users.noreply.github.com"
```
Siempre `git pull` antes de empezar y antes de `git push`; sin `push --force`.

## 9. Riesgos y puntos no verificados
- **No verificado:** si basta la instalación oficial del API de Python de CPLEX sin ctypes (lo dirá `verificar_entorno.py` en la máquina del compañero). Si pip instala la Community Edition, falla con error 1016 y habrá que definir `CPLEX_STUDIO_DIR222`.
- **No verificado:** que `gurobipy` tenga licencia completa en esa máquina (el script usa un modelo de 2.500 variables y restricciones para detectarlo).
- **No ejecutado:** ninguna corrida de `convrp_tc3.py` con solvers; no hay resultados de TC3 todavía. Los únicos números existentes son los de TC2 y los de CPLEX con 8 hilos, que no son comparables.
- Python 3.14 (usado en TC2) puede no tener wheel de `cplex`; si falla, crear un entorno virtual con 3.11 o 3.12.
- Una sola corrida por celda: los tiempos pueden variar entre corridas y en una máquina compartida.
- El **informe/presentación PDF de la Tarea 2 no está en el repo**: `.gitignore` excluye `*.pdf`. Se asume intencional; no verificado con el equipo.
- Git advierte conversión LF a CRLF en archivos nuevos (configuración de Windows); no afecta a Python.
