"""Tarea Computacional 3 - conVRP reducido (Campelo et al., 2019): Gurobi vs. CPLEX.

Un solo preproceso (`preproceso`) alimenta los dos constructores, de modo que
ambos solvers resuelven exactamente el mismo modelo.

Uso:
    python convrp_tc3.py run instancias/inst1.json compare
    python convrp_tc3.py run instancias/inst1.json relax --solver cplex
    python convrp_tc3.py run instancias/inst2.json mip --solver gurobi --timelimit 600
    python convrp_tc3.py run instancias/inst1.json compare --threads 0   # hilos por defecto
    python convrp_tc3.py final     # comparacion principal completa (threads 1, 600 s)
    python convrp_tc3.py extra     # opcional: hilos por defecto en ambos solvers

Nombres: logs/{inst}_{solver}_{relax|mip}_{h1|hdef}.log y
resultados/{inst}_{exp}_{solver(es)}_{h1|hdef}.csv. Aborta si ya existen (salvo --force).

Experimentos: relax (relajacion continua), mip (modelo entero), compare (ambos,
en ambos solvers, uno a la vez).
Parametros explicitos: Threads=1 y TimeLimit=600 s; todo lo demas en la
configuracion por defecto de cada solver.

Formulacion (numeracion del paper; O = {(i,t): q_it > 0} es el conjunto de pedidos):
    (1)  min  sum_{r,t} sum_{(i,j) in A_t} td_ij X^r_ijt
    (2)  sum_r Z^r_i = 1                                         para todo i
    (3)  sum_{i:(i,j) in A_t} X^r_ijt = Z^r_j                    para todo (j,t) en O, r
    (4)  sum_{j:(i,j) in A_t} X^r_ijt = Z^r_i                    para todo (i,t) en O, r
    (5)  sum_j X^r_0jt = 1                                       para todo t, r
    (7)  W_it + st_i + tt_ij <= W_jt + M_ij (1 - X^r_ijt)
    (8)  ventanas a_i <= W_it <= b_i (como cotas de W)
    (9)  dW^r + tt_0j <= W_jt + M_j (1 - X^r_0jt)
    (10) W_it + st_i + tt_i0 <= rW^r_t + M_i (1 - X^r_{i,n+1,t})
    (11) dW^r >= a_W     (12) rW^r_t <= b_W
    (14) sum_i q_it Z^r_i <= Q                                   para todo r, t
    (16) X, Z binarias; W, dW, rW >= 0
"""
import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_RES = os.path.join(AQUI, "resultados")
DIR_LOG = os.path.join(AQUI, "logs")


# ----------------------------------------------------------------------------
# Instancias y preproceso compartido
# ----------------------------------------------------------------------------
def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        inst = json.load(f)
    inst["ventana"] = {int(k): v for k, v in inst["ventana"].items()}
    return inst


def preproceso(inst):
    """Arcos por dia, cotas de W y Big-M. Lo consumen ambos constructores."""
    n, T = inst["n"], inst["T"]
    tt, st, q = inst["tt"], inst["st"], inst["q"]
    aW, bW, tw = inst["aW"], inst["bW"], inst["ventana"]
    fin = n + 1

    clientes = list(range(1, n + 1))
    lb = {i: max(tw[i][0] if i in tw else aW, aW + tt[0][i]) for i in clientes}
    ub = {i: min(tw[i][1] if i in tw else bW, bW - st[i] - tt[i][fin]) for i in clientes}

    # O: pedidos por dia (solo estos nodos entran al grafo del dia t)
    pedidos = {t: [i for i in clientes if q[i][t] > 0] for t in range(T)}

    arcos = {}
    for t in range(T):
        P = pedidos[t]
        A = [(0, j) for j in P] + [(i, fin) for i in P] + [(0, fin)]
        A += [(i, j) for i in P for j in P
              if i != j and lb[i] + st[i] + tt[i][j] <= ub[j]]
        arcos[t] = A

    # Big-M: (7) por arco, (9) por cliente j, (10) por cliente i
    M7 = {(i, j): max(0.0, ub[i] + st[i] + tt[i][j] - lb[j])
          for t in range(T) for (i, j) in arcos[t] if i != 0 and j != fin}
    M9 = {j: max(0.0, bW + tt[0][j] - lb[j]) for j in clientes}
    M10 = {i: max(0.0, ub[i] + st[i] + tt[i][0] - aW) for i in clientes}
    return dict(lb=lb, ub=ub, pedidos=pedidos, arcos=arcos, M7=M7, M9=M9, M10=M10)


# ----------------------------------------------------------------------------
# Constructor Gurobi
# ----------------------------------------------------------------------------
def construir_modelo_gurobi(inst, pre):
    import gurobipy as gp
    from gurobipy import GRB

    n, T, R = inst["n"], inst["T"], inst["R"]
    td, tt, st, q, Q = inst["td"], inst["tt"], inst["st"], inst["q"], inst["Q"]
    aW, bW = inst["aW"], inst["bW"]
    lb, ub, pedidos, arcos = pre["lb"], pre["ub"], pre["pedidos"], pre["arcos"]
    fin = n + 1
    D, Rs, N = range(T), range(R), range(1, n + 1)

    m = gp.Model("conVRP")
    X = {(r, i, j, t): m.addVar(vtype=GRB.BINARY, obj=td[i][j], name=f"X_{r}_{i}_{j}_{t}")
         for t in D for (i, j) in arcos[t] for r in Rs}
    Z = {(r, i): m.addVar(vtype=GRB.BINARY, name=f"Z_{r}_{i}") for r in Rs for i in N}
    W = {(i, t): m.addVar(lb=lb[i], ub=ub[i], name=f"W_{i}_{t}")
         for t in D for i in pedidos[t]}
    dW = {r: m.addVar(lb=0, ub=bW, name=f"dW_{r}") for r in Rs}
    rW = {(r, t): m.addVar(lb=0, ub=bW, name=f"rW_{r}_{t}") for r in Rs for t in D}
    m.ModelSense = GRB.MINIMIZE

    for i in N:                                                     # (2)
        m.addConstr(gp.quicksum(Z[r, i] for r in Rs) == 1, name=f"c2_{i}")
    for r in Rs:
        for t in D:
            for j in pedidos[t]:                                    # (3)-(4), (j,t) en O
                m.addConstr(gp.quicksum(X[r, i, k, t] for (i, k) in arcos[t] if k == j)
                            == Z[r, j], name=f"c3_{r}_{j}_{t}")
                m.addConstr(gp.quicksum(X[r, k, i, t] for (k, i) in arcos[t] if k == j)
                            == Z[r, j], name=f"c4_{r}_{j}_{t}")
    for r in Rs:
        for t in D:                                                 # (5)
            m.addConstr(gp.quicksum(X[r, 0, j, t] for (i, j) in arcos[t] if i == 0) == 1,
                        name=f"c5_{r}_{t}")
            for (i, j) in arcos[t]:                                 # (7)
                if i == 0 or j == fin:
                    continue
                m.addConstr(W[i, t] + st[i] + tt[i][j]
                            <= W[j, t] + pre["M7"][i, j] * (1 - X[r, i, j, t]),
                            name=f"c7_{r}_{i}_{j}_{t}")
            for j in pedidos[t]:                                    # (9)
                m.addConstr(dW[r] + tt[0][j]
                            <= W[j, t] + pre["M9"][j] * (1 - X[r, 0, j, t]),
                            name=f"c9_{r}_{j}_{t}")
            for i in pedidos[t]:                                    # (10)
                m.addConstr(W[i, t] + st[i] + tt[i][0]
                            <= rW[r, t] + pre["M10"][i] * (1 - X[r, i, fin, t]),
                            name=f"c10_{r}_{i}_{t}")
            m.addConstr(rW[r, t] <= bW, name=f"c12_{r}_{t}")        # (12)
            m.addConstr(gp.quicksum(q[i][t] * Z[r, i] for i in N) <= Q,
                        name=f"c14_{r}_{t}")                        # (14)
        m.addConstr(dW[r] >= aW, name=f"c11_{r}")                   # (11)
    m.update()
    return m, X, Z


# ----------------------------------------------------------------------------
# Constructor CPLEX (docplex)
# ----------------------------------------------------------------------------
def importar_cplex():
    """Importa docplex. Si CPLEX_STUDIO_DIR222 esta definida, carga antes el motor
    de Studio (necesario si el paquete pip trae solo la Community Edition)."""
    studio = os.environ.get("CPLEX_STUDIO_DIR222")
    if studio and os.name == "nt":
        import ctypes
        dll = os.path.join(studio, "cplex", "bin", "x64_win64", "cplex2220.dll")
        if not os.path.isfile(dll):
            raise RuntimeError(f"CPLEX_STUDIO_DIR222={studio} no contiene {dll}")
        ctypes.WinDLL(dll)
    try:
        from docplex.mp.model import Model
        from docplex.mp.utils import DOcplexLimitsExceeded
    except ImportError as exc:
        raise RuntimeError("No se pudo importar docplex (pip install docplex cplex): "
                           f"{exc}") from exc
    return Model, DOcplexLimitsExceeded


def construir_modelo_cplex(inst, pre, relajacion=False):
    Model, _ = importar_cplex()
    n, T, R = inst["n"], inst["T"], inst["R"]
    td, tt, st, q, Q = inst["td"], inst["tt"], inst["st"], inst["q"], inst["Q"]
    aW, bW = inst["aW"], inst["bW"]
    lb, ub, pedidos, arcos = pre["lb"], pre["ub"], pre["pedidos"], pre["arcos"]
    fin = n + 1
    D, Rs, N = range(T), range(R), range(1, n + 1)

    mdl = Model(name="conVRP")
    tipo = mdl.continuous_var_dict if relajacion else mdl.binary_var_dict
    xk = [(r, i, j, t) for t in D for (i, j) in arcos[t] for r in Rs]
    zk = [(r, i) for r in Rs for i in N]
    X = tipo(xk, lb=0, ub=1, name="X")
    Z = tipo(zk, lb=0, ub=1, name="Z")
    W = {(i, t): mdl.continuous_var(lb=lb[i], ub=ub[i], name=f"W_{i}_{t}")
         for t in D for i in pedidos[t]}
    dW = {r: mdl.continuous_var(lb=0, ub=bW, name=f"dW_{r}") for r in Rs}
    rW = {(r, t): mdl.continuous_var(lb=0, ub=bW, name=f"rW_{r}_{t}")
          for r in Rs for t in D}

    mdl.minimize(mdl.sum(td[i][j] * X[r, i, j, t] for t in D for (i, j) in arcos[t]
                         for r in Rs))                                       # (1)
    for i in N:                                                              # (2)
        mdl.add_constraint(mdl.sum(Z[r, i] for r in Rs) == 1, ctname=f"c2_{i}")
    for r in Rs:
        for t in D:
            for j in pedidos[t]:                                             # (3)-(4)
                mdl.add_constraint(mdl.sum(X[r, i, k, t] for (i, k) in arcos[t] if k == j)
                                   == Z[r, j], ctname=f"c3_{r}_{j}_{t}")
                mdl.add_constraint(mdl.sum(X[r, k, i, t] for (k, i) in arcos[t] if k == j)
                                   == Z[r, j], ctname=f"c4_{r}_{j}_{t}")
    for r in Rs:
        for t in D:
            mdl.add_constraint(mdl.sum(X[r, 0, j, t] for (i, j) in arcos[t] if i == 0) == 1,
                               ctname=f"c5_{r}_{t}")                         # (5)
            for (i, j) in arcos[t]:                                          # (7)
                if i == 0 or j == fin:
                    continue
                mdl.add_constraint(W[i, t] + st[i] + tt[i][j]
                                   <= W[j, t] + pre["M7"][i, j] * (1 - X[r, i, j, t]),
                                   ctname=f"c7_{r}_{i}_{j}_{t}")
            for j in pedidos[t]:                                             # (9)
                mdl.add_constraint(dW[r] + tt[0][j]
                                   <= W[j, t] + pre["M9"][j] * (1 - X[r, 0, j, t]),
                                   ctname=f"c9_{r}_{j}_{t}")
            for i in pedidos[t]:                                             # (10)
                mdl.add_constraint(W[i, t] + st[i] + tt[i][0]
                                   <= rW[r, t] + pre["M10"][i] * (1 - X[r, i, fin, t]),
                                   ctname=f"c10_{r}_{i}_{t}")
            mdl.add_constraint(rW[r, t] <= bW, ctname=f"c12_{r}_{t}")        # (12)
            mdl.add_constraint(mdl.sum(q[i][t] * Z[r, i] for i in N) <= Q,
                               ctname=f"c14_{r}_{t}")                        # (14)
        mdl.add_constraint(dW[r] >= aW, ctname=f"c11_{r}")                   # (11)
    return mdl, X, Z


# ----------------------------------------------------------------------------
# Resolucion
# ----------------------------------------------------------------------------
def _r(v, d=3):
    if v is None:
        return None
    v = float(v)
    return round(v, d) if math.isfinite(v) else None


ESTADOS_GUROBI = {1: "LOADED", 2: "OPTIMAL", 3: "INFEASIBLE", 4: "INF_OR_UNBD",
                  5: "UNBOUNDED", 6: "CUTOFF", 7: "ITERATION_LIMIT", 8: "NODE_LIMIT",
                  9: "TIME_LIMIT", 10: "SOLUTION_LIMIT", 11: "INTERRUPTED",
                  12: "NUMERIC", 13: "SUBOPTIMAL"}


def etiqueta_hilos(threads):
    """h1 = 1 hilo; hdef = hilos por defecto del solver (--threads 0)."""
    return "hdef" if threads == 0 else f"h{threads}"


def resolver_gurobi(inst, pre, relajacion, timelimit, threads, ruta_log):
    import gurobipy as gp
    from gurobipy import GRB

    m, X, Z = construir_modelo_gurobi(inst, pre)
    n_bin = sum(1 for v in m.getVars() if v.VType == GRB.BINARY)
    n_rest = m.NumConstrs
    if relajacion:
        m = m.relax()
    if os.path.exists(ruta_log):
        os.remove(ruta_log)
    m.Params.LogFile = ruta_log
    m.Params.LogToConsole = 0
    m.Params.OutputFlag = 1
    m.Params.Threads = threads        # 0 = valor por defecto del solver
    m.Params.TimeLimit = timelimit
    m.optimize()

    tiene = m.SolCount > 0
    fila = dict(solver="gurobi", gurobipy=gp.gurobi.version(),
                n_bin=n_bin, n_rest=n_rest,
                estado=ESTADOS_GUROBI.get(m.Status, str(m.Status)), tiempo_s=_r(m.Runtime),
                obj=_r(m.ObjVal) if tiene else None)
    sol = None
    if relajacion:
        fila.update(cota=None, gap_pct=None, nodos=None)
    else:
        fila.update(cota=_r(m.ObjBound),
                    gap_pct=_r(100 * m.MIPGap, 4) if tiene else None,
                    nodos=int(m.NodeCount))
        if tiene:
            sol = _extraer({k: v.X for k, v in X.items()}, {k: v.X for k, v in Z.items()})
    return fila, sol


def resolver_cplex(inst, pre, relajacion, timelimit, threads, ruta_log):
    _, LimitsExceeded = importar_cplex()
    mdl, X, Z = construir_modelo_cplex(inst, pre, relajacion)
    mdl.context.cplex_parameters.threads = threads   # 0 = valor por defecto del solver
    mdl.context.cplex_parameters.timelimit = timelimit
    with open(ruta_log, "w", encoding="utf-8") as log:
        try:
            s = mdl.solve(log_output=log)
        except LimitsExceeded as exc:
            raise RuntimeError(
                "CPLEX Community Edition: el modelo supera el limite de 1000 variables o "
                "restricciones (error 1016). Defina CPLEX_STUDIO_DIR222 con la ruta de "
                f"CPLEX Studio 22.2 o instale una licencia completa. Detalle: {exc}") from exc
    d = mdl.solve_details
    stats = mdl.statistics
    fila = dict(solver="cplex", gurobipy=None,
                n_bin=stats.number_of_binary_variables if not relajacion else 0,
                n_rest=mdl.number_of_constraints,
                estado=d.status, tiempo_s=_r(d.time),
                obj=_r(s.objective_value) if s else None)
    sol = None
    if relajacion:
        fila.update(cota=None, gap_pct=None, nodos=None)
    else:
        fila.update(cota=_r(d.best_bound),
                    gap_pct=_r(100 * d.mip_relative_gap, 4) if s else None,
                    nodos=int(d.nb_nodes_processed))
        if s:
            sol = _extraer({k: s.get_value(v) for k, v in X.items()},
                           {k: s.get_value(v) for k, v in Z.items()})
    return fila, sol


def _extraer(xv, zv):
    return dict(Z={f"{r},{i}": 1 for (r, i), v in zv.items() if v > 0.5},
                X=[list(k) for k, v in xv.items() if v > 0.5])


RESOLVEDORES = {"gurobi": resolver_gurobi, "cplex": resolver_cplex}
CAMPOS = ["instancia", "solver", "modelo", "hilos", "timelimit", "fecha", "estado", "obj",
          "cota", "gap_pct", "nodos", "tiempo_s", "n_bin", "n_rest", "gurobipy", "log"]
INSTANCIAS_FINALES = ["instancias/inst1.json", "instancias/inst2.json"]
TIMELIMIT_FINAL = 600


def ruta_log(nombre, solver, modelo, threads):
    return os.path.join(DIR_LOG, f"{nombre}_{solver}_{modelo}_{etiqueta_hilos(threads)}.log")


def ruta_sol(nombre, solver, threads):
    return os.path.join(DIR_RES, f"{nombre}_{solver}_mip_{etiqueta_hilos(threads)}_sol.json")


def ruta_csv(nombre, exp, solvers, threads):
    return os.path.join(
        DIR_RES, f"{nombre}_{exp}_{'-'.join(solvers)}_{etiqueta_hilos(threads)}.csv")


def trabajo(archivo, exp, solver, threads):
    """Un trabajo = una instancia con un conjunto de solvers y modelos."""
    solvers = ["gurobi", "cplex"] if solver == "both" else [solver]
    modelos = ["relax", "mip"] if exp == "compare" else [exp]
    return dict(inst=cargar(archivo), exp=exp, solvers=solvers, modelos=modelos,
                threads=threads)


def salidas(tr):
    """Archivos que escribira un trabajo (para detectar sobrescrituras)."""
    n, th = tr["inst"]["nombre"], tr["threads"]
    out = [ruta_csv(n, tr["exp"], tr["solvers"], th)]
    for s in tr["solvers"]:
        for mo in tr["modelos"]:
            out.append(ruta_log(n, s, mo, th))
        if "mip" in tr["modelos"]:
            out.append(ruta_sol(n, s, th))
    return out


def experimento(inst, solver, modelo, timelimit, threads):
    """Una corrida: un solver, relax o mip. Escribe log y (si hay) solucion."""
    os.makedirs(DIR_LOG, exist_ok=True)
    os.makedirs(DIR_RES, exist_ok=True)
    log = ruta_log(inst["nombre"], solver, modelo, threads)
    pre = preproceso(inst)
    fila, sol = RESOLVEDORES[solver](inst, pre, modelo == "relax", timelimit, threads, log)
    fila.update(instancia=inst["nombre"], modelo=modelo,
                hilos=threads if threads else "defecto", timelimit=timelimit,
                fecha=datetime.now().isoformat(timespec="seconds"),
                log=os.path.relpath(log, AQUI).replace("\\", "/"))
    if sol is not None:
        with open(ruta_sol(inst["nombre"], solver, threads), "w") as f:
            json.dump(sol, f)
    print({k: fila[k] for k in CAMPOS if k in fila and k != "log"}, flush=True)
    return fila


def guardar_csv(filas, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    print(f"-> {ruta}")


def ejecutar_plan(trabajos, timelimit, force):
    """Imprime el plan, comprueba sobrescrituras y solvers, corre en secuencia
    (un solver a la vez) e imprime un resumen."""
    print("=== PLAN ===")
    existentes = []
    for tr in trabajos:
        n, th = tr["inst"]["nombre"], etiqueta_hilos(tr["threads"])
        for s in tr["solvers"]:
            for mo in tr["modelos"]:
                print(f"  {n} | {s} | {mo} | hilos={th} | timelimit={timelimit:g} s")
        existentes += [o for o in salidas(tr) if os.path.exists(o)]
    if existentes and not force:
        lista = "\n  ".join(os.path.relpath(o, AQUI) for o in existentes)
        raise RuntimeError("ya existen archivos de salida (use --force para sobrescribir):"
                           f"\n  {lista}")
    solvers = {s for tr in trabajos for s in tr["solvers"]}
    if "gurobi" in solvers:
        try:
            import gurobipy  # noqa: F401  falla pronto si falta
        except ImportError as exc:
            raise RuntimeError(f"No se pudo importar gurobipy: {exc}") from exc
    if "cplex" in solvers:
        importar_cplex()
    print("=== EJECUCION ===", flush=True)
    resumen = []
    for tr in trabajos:
        filas = []
        for s in tr["solvers"]:     # secuencial: nunca dos solvers a la vez
            for mo in tr["modelos"]:
                filas.append(experimento(tr["inst"], s, mo, timelimit, tr["threads"]))
        guardar_csv(filas, ruta_csv(tr["inst"]["nombre"], tr["exp"], tr["solvers"],
                                    tr["threads"]))
        resumen += filas
    print("=== RESUMEN ===")
    print(f"{'inst':<6}{'solver':<8}{'modelo':<6}{'hilos':<8}{'estado':<24}{'obj':>8}"
          f"{'gap%':>8}{'nodos':>10}{'t(s)':>10}")
    for f in resumen:
        print(f"{f['instancia']:<6}{f['solver']:<8}{f['modelo']:<6}{str(f['hilos']):<8}"
              f"{str(f['estado']):<24}{str(f['obj']):>8}{str(f['gap_pct'] or '-'):>8}"
              f"{str(f['nodos'] or '-'):>10}{str(f['tiempo_s']):>10}")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="una instancia, un experimento")
    r.add_argument("instancia")
    r.add_argument("exp", choices=["relax", "mip", "compare"])
    r.add_argument("--solver", choices=["gurobi", "cplex", "both"], default="both")
    r.add_argument("--timelimit", type=float, default=TIMELIMIT_FINAL)
    r.add_argument("--threads", type=int, default=1, help="0 = hilos por defecto")
    sub.add_parser("final", help="comparacion principal: inst1 e inst2, ambos solvers, "
                                 "relax y mip, --threads 1, 600 s")
    sub.add_parser("extra", help="corrida opcional con hilos por defecto (--threads 0)")
    for sp in sub.choices.values():
        sp.add_argument("--force", action="store_true",
                        help="sobrescribir logs y CSV existentes")
    a = p.parse_args()

    if a.cmd == "run":
        if a.timelimit <= 0:
            p.error("--timelimit debe ser positivo")
        trabajos, tl = [trabajo(a.instancia, a.exp, a.solver, a.threads)], a.timelimit
    else:
        threads = 1 if a.cmd == "final" else 0
        trabajos = [trabajo(os.path.join(AQUI, f), "compare", "both", threads)
                    for f in INSTANCIAS_FINALES]
        tl = TIMELIMIT_FINAL
    ejecutar_plan(trabajos, tl, a.force)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"ERROR: {exc}")
