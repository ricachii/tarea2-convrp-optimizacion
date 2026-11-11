"""Implementacion CPLEX del conVRP de convrp.py.

Uso:
    python convrp_cplex.py run instancias\\inst1.json all --timelimit 600

Las corridas y los logs se guardan en resultados_cplex\\ para mantenerlos
separados de los resultados de Gurobi.
"""
import argparse
import ctypes
import csv
import json
import math
import os
import sys

#HABIA INSTALADO COMMUNITY EDITION AL PRINCIPIO PORQUE EL TUTORIAL DE INSTALACION DE CANVAS NO ME SIRVIO Y LUEGO QUE CONSEGUI EDICION ESTUDIANTE PYTHON NO ME LO QUERIA PESCAR POR LO QUE TENGO ESTA PARTE.
def cargar_runtime_cplex():
    """Carga el motor de Studio antes del DLL Community incluido con pip."""
    if os.name != "nt":
        return None
    studio_dir = os.environ.get("CPLEX_STUDIO_DIR222")
    if not studio_dir:
        return None
    dll = os.path.join(
        studio_dir, "cplex", "bin", "x64_win64", "cplex2220.dll"
    )
    if not os.path.isfile(dll):
        raise RuntimeError(
            "No se encontro el motor CPLEX 22.2 en "
            f"{dll}. Revise CPLEX_STUDIO_DIR222."
        )
    try:
        return ctypes.WinDLL(dll)
    except OSError as exc:
        raise RuntimeError(f"No se pudo cargar el motor CPLEX de {dll}: {exc}") from exc


_CPLEX_RUNTIME = cargar_runtime_cplex()

from docplex.mp.model import Model
from docplex.mp.utils import DOcplexLimitsExceeded

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_RES = os.path.join(AQUI, "resultados_cplex")
DIR_LOG = os.path.join(DIR_RES, "logs")


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        inst = json.load(f)
    inst["ventana"] = {int(k): v for k, v in inst["ventana"].items()}
    return inst


def construir_modelo(inst, relajacion=False):
    n, T, R = inst["n"], inst["T"], inst["R"]
    Q = inst["Q"]
    td, tt, st, q = inst["td"], inst["tt"], inst["st"], inst["q"]
    aW, bW, tw = inst["aW"], inst["bW"], inst["ventana"]
    fin = n + 1
    dias, rutas = range(T), range(R)

    lb = {
        i: max(tw[i][0] if i in tw else aW, aW + tt[0][i])
        for i in range(1, n + 1)
    }
    ub = {
        i: min(tw[i][1] if i in tw else bW, bW - st[i] - tt[i][fin])
        for i in range(1, n + 1)
    }

    mdl = Model(name="conVRP_CPLEX")
    pedidos = {
        t: [i for i in range(1, n + 1) if q[i][t] > 0]
        for t in dias
    }
    arcos = {}
    for t in dias:
        P = pedidos[t]
        A = [(0, j) for j in P] + [(i, fin) for i in P] + [(0, fin)]
        A += [
            (i, j)
            for i in P
            for j in P
            if i != j and lb[i] + st[i] + tt[i][j] <= ub[j]
        ]
        arcos[t] = A

    x_keys = [(r, i, j, t) for t in dias for i, j in arcos[t] for r in rutas]
    z_keys = [(r, i) for r in rutas for i in range(1, n + 1)]
    w_keys = [(i, t) for t in dias for i in pedidos[t]]
    x_type = mdl.continuous_var_dict if relajacion else mdl.binary_var_dict
    z_type = mdl.continuous_var_dict if relajacion else mdl.binary_var_dict
    X = x_type(x_keys, lb=0, ub=1, name="X")
    Z = z_type(z_keys, lb=0, ub=1, name="Z")
    W = {
        (i, t): mdl.continuous_var(lb=lb[i], ub=ub[i], name=f"W_{i}_{t}")
        for i, t in w_keys
    }
    dW = {
        r: mdl.continuous_var(lb=0, ub=bW, name=f"dW_{r}")
        for r in rutas
    }
    rW = {
        (r, t): mdl.continuous_var(lb=0, ub=bW, name=f"rW_{r}_{t}")
        for r in rutas
        for t in dias
    }

    mdl.minimize(
        mdl.sum(td[i][j] * X[r, i, j, t] for t in dias
                for i, j in arcos[t] for r in rutas)
    )

    # (2) Asignacion consistente de cada cliente a una ruta plantilla.
    for i in range(1, n + 1):
        mdl.add_constraint(
            mdl.sum(Z[r, i] for r in rutas) == 1, ctname=f"c2_{i}"
        )

    # (3)-(4) Grado solo para clientes que tienen pedido el dia t.
    for r in rutas:
        for t in dias:
            for j in pedidos[t]:
                mdl.add_constraint(
                    mdl.sum(X[r, i, k, t] for i, k in arcos[t] if k == j)
                    == Z[r, j],
                    ctname=f"c3_{r}_{j}_{t}",
                )
                mdl.add_constraint(
                    mdl.sum(X[r, k, i, t] for k, i in arcos[t] if k == j)
                    == Z[r, j],
                    ctname=f"c4_{r}_{j}_{t}",
                )

    # (5) Cada ruta parte una vez por dia (0 -> fin si no tiene pedidos).
    for r in rutas:
        for t in dias:
            mdl.add_constraint(
                mdl.sum(X[r, i, j, t] for i, j in arcos[t] if i == 0) == 1,
                ctname=f"c5_{r}_{t}",
            )

    # (7) Propagacion de tiempos, con Big-M ajustado por arco.
    for r in rutas:
        for t in dias:
            for i, j in arcos[t]:
                if i == 0 or j == fin:
                    continue
                big_m = max(0.0, ub[i] + st[i] + tt[i][j] - lb[j])
                mdl.add_constraint(
                    W[i, t] + st[i] + tt[i][j]
                    <= W[j, t] + big_m * (1 - X[r, i, j, t]),
                    ctname=f"c7_{r}_{i}_{j}_{t}",
                )

    # (9)-(10) Coordinacion de salida y retorno del deposito.
    for r in rutas:
        for t in dias:
            for j in pedidos[t]:
                big_m = max(0.0, bW + tt[0][j] - lb[j])
                mdl.add_constraint(
                    dW[r] + tt[0][j]
                    <= W[j, t] + big_m * (1 - X[r, 0, j, t]),
                    ctname=f"c9_{r}_{j}_{t}",
                )
            for i in pedidos[t]:
                big_m = max(0.0, ub[i] + st[i] + tt[i][0] - aW)
                mdl.add_constraint(
                    W[i, t] + st[i] + tt[i][0]
                    <= rW[r, t] + big_m * (1 - X[r, i, fin, t]),
                    ctname=f"c10_{r}_{i}_{t}",
                )

    # (11)-(12) Horario de operacion del deposito.
    for r in rutas:
        mdl.add_constraint(dW[r] >= aW, ctname=f"c11_{r}")
        for t in dias:
            mdl.add_constraint(rW[r, t] <= bW, ctname=f"c12_{r}_{t}")

    # (14) Capacidad por ruta y dia.
    for r in rutas:
        for t in dias:
            mdl.add_constraint(
                mdl.sum(q[i][t] * Z[r, i] for i in range(1, n + 1)) <= Q,
                ctname=f"c14_{r}_{t}",
            )

    return mdl


def _numero(valor, decimales=6):
    if valor is None:
        return None
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return None
    return round(valor, decimales) if math.isfinite(valor) else None


def resolver(inst, relajacion, timelimit):
    etiqueta = "relajacion" if relajacion else "entero"
    nombre = inst["nombre"]
    os.makedirs(DIR_LOG, exist_ok=True)
    ruta_log = os.path.join(DIR_LOG, f"{nombre}_{etiqueta}.log")
    mdl = construir_modelo(inst, relajacion=relajacion)
    mdl.parameters.timelimit = timelimit

    with open(ruta_log, "w", encoding="utf-8") as log:
        try:
            solucion = mdl.solve(log_output=log)
        except DOcplexLimitsExceeded as exc:
            print(
                f"CPLEX Community Edition no puede resolver {nombre}: "
                f"el modelo tiene {mdl.number_of_variables} variables y "
                f"{mdl.number_of_constraints} restricciones, superando "
                "el limite de 1000. Se requiere una licencia completa "
                f"(por ejemplo, academica). Detalle: {exc}",
                file=sys.stderr,
            )
            raise SystemExit(2) from exc

    detalles = mdl.solve_details
    fila = {
        "instancia": nombre,
        "modelo": etiqueta,
        "estado": detalles.status,
        "tiempo_s": _numero(detalles.time, 3),
        "objetivo": _numero(solucion.objective_value) if solucion else None,
        "cota": _numero(detalles.best_bound),
        "gap_pct": (
            _numero(100 * detalles.mip_relative_gap, 4)
            if not relajacion and detalles.mip_relative_gap is not None
            else None
        ),
        "nodos": detalles.nb_nodes_processed if not relajacion else 0,
        "log": os.path.relpath(ruta_log, AQUI),
    }
    print(fila)
    return fila


def guardar_csv(filas, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        writer.writeheader()
        writer.writerows(filas)
    print(f"-> {ruta}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("instancia")
    run.add_argument("exp", choices=["relax", "mip", "all"])
    run.add_argument("--timelimit", type=float, default=600)
    args = parser.parse_args()

    if args.timelimit <= 0:
        parser.error("--timelimit debe ser positivo")

    inst = cargar(args.instancia)
    os.makedirs(DIR_RES, exist_ok=True)
    experimentos = []
    if args.exp in ("relax", "all"):
        experimentos.append((True, f"{inst['nombre']}_relajacion.csv"))
    if args.exp in ("mip", "all"):
        experimentos.append((False, f"{inst['nombre']}_entero.csv"))

    for relajacion, archivo in experimentos:
        fila = resolver(inst, relajacion, args.timelimit)
        guardar_csv([fila], os.path.join(DIR_RES, archivo))


if __name__ == "__main__":
    main()
