# Contexto del proyecto: Tarea Computacional 2 (conVRP reducido en Gurobi)

## Objetivo
Modelar una situación de ruteo consistente como PLEM, implementarla en Python con `gurobipy` y analizar el efecto de distintas configuraciones del solver sobre el desempeño computacional.

- Curso: Optimización I, Semestre 2 2026. Evaluación: 39 puntos (8% del curso).
- Grupo: 5 integrantes (el enunciado menciona 4; verificar si afecta "Organización del equipo").
- Paper base: Campelo, Neves-Moreira, Amorim & Almada-Lobo (2019), *Consistent vehicle routing problem with service level agreements: A case study in the pharmaceutical distribution sector*, EJOR 273(1), 131–145. PDF en la carpeta.
- Se implementa una **versión reducida** del modelo del paper.

## Fechas
- Entrega (.zip en Canvas): **martes 20 de octubre de 2026, 23:59**.
- Presentación: **miércoles 21 de octubre de 2026**, horario de clases y práctica.

## Modelo (numeración del paper)
Consistencia: cada cliente se asigna a una única ruta (mismo vehículo) todos los días. Las rutas son plantilla (sin índice de día).

**Incluir:** (1) objetivo (distancia total), (2) asignación nodo–ruta, (3)–(4) flujo/grado, (5) salida del depósito una vez por día, (7) tiempos de llegada con Big-M (elimina subtours), (8) ventanas de tiempo solo para N_TW, (9)–(10) coordinación salida/retorno del depósito, (11)–(12) horario del depósito, (14) capacidad, (16) binariedad y no negatividad.

**Fuera de alcance:** fechas de liberación (13), múltiples períodos de despacho por cliente (6), duración máxima de ruta (15).

**Variables:** X^r_ijt, Z^r_i, W_it, dW_r, rW^r_t.

## Instancias
Cada grupo genera 2 instancias ficticias propias, con al menos 15 clientes, 3 días y 3 rutas por día. Deben ser computacionalmente no triviales (no cerrar de inmediato con la configuración por defecto, y que las configuraciones produzcan diferencias). Se pueden ajustar amplitud de ventanas, capacidad relativa a la demanda o número de clientes. También se permite usar un subconjunto de Solomon / Gehring & Homberger (CVRPLIB).

## Experimentos
Siempre `Threads=1` y `TimeLimit=600`.

1. **Relajación continua:** z_LP vs z_MILP, brecha de integralidad = (z_MILP − z_LP)/z_MILP × 100%. Interpretar (dualidad débil, qué tan ajustada es).
2. **Configuraciones:** baseline vs `Cuts=0`, `Presolve=0`, `MIPFocus=1`, `MIPFocus=3`, `Heuristics=0` (una a la vez). Reportar tiempo, gap y objetivo.
3. **Ajuste automático:** `model.tune()` con `TuneTimeLimit` razonable; comparar contra baseline y mejor manual.
4. **Sensibilidad de Q:** fijar enteras con `Model.fixed()`; analizar `SARHSLow`/`SARHSUp` y `Pi` de la capacidad. Interpretar.

## Entregables (.zip)
1. Presentación PDF, formato pitch, máx. 5 min (grupo, contexto, modelo, instancias, resultados, discusión).
2. Código Python con modelo, lectura de instancias y todas las corridas.
3. Archivos de las instancias.

## Rúbrica (39 pts)
| Concepto | Pts |
|---|---|
| Componentes y modelo matemático | 5 |
| Definición de las instancias | 5 |
| Implementación correcta en gurobipy | 5 |
| Relajación continua y brecha | 2 |
| Comparación: Cuts / Presolve / MIPFocus / Heuristics | 2 c/u |
| Ajuste automático (tune) | 2 |
| Sensibilidad de Q | 2 |
| Discusión de resultados | 5 |
| Calidad de la exposición | 3 |
| Organización del equipo | 2 |

## Reglas y cuidados
- Notación fiel al paper; índices claros (i, j ∈ N, r ∈ R, t ∈ D).
- Código reproducible: semilla fija, parámetros explícitos, una función por experimento, resultados en CSV.
- Big-M ajustado, no arbitrariamente grande.
- Si una corrida llega a TimeLimit, reportar gap y mejor incumbente.
- Discusión: explicar el *por qué* de cada efecto, no solo listar números.
- Se permite IA generativa, pero todo debe estar revisado y validado.
- Archivos en blanco = NCR; no se aceptan tareas de semestres anteriores.

## Entorno
Python 3.14.3, gurobipy 13.0.3 (licencia académica, vence 2027-09-30), Windows 11.
