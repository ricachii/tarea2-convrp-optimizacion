"""Tarea Computacional 2 - conVRP reducido (Campelo et al., 2019) en gurobipy.

Uso:
    python convrp.py gen                      # genera instancias/*.json
    python convrp.py run <inst> <exp> [...]   # exp: relax | configs | tune | sens | all
    python convrp.py run instancias/inst1.json all --timelimit 600

Notacion del paper: nodos 0 (deposito salida) y n+1 (deposito retorno), clientes 1..n,
i,j in N, r in R (rutas plantilla), t in D (dias).
"""
import argparse
import json
import math
import os
import random

import gurobipy as gp
from gurobipy import GRB

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_INST = os.path.join(AQUI, "instancias")
DIR_RES = os.path.join(AQUI, "resultados")


# ----------------------------------------------------------------------------
# Instancias
# ----------------------------------------------------------------------------
def generar_instancia(nombre, seed, n=15, T=3, R=3, frac_tw=0.6, ancho_tw=60,
                      p_pedido=0.85, holgura_Q=1.10, aW=0, bW=480, st=10):
    """Instancia ficticia reproducible (semilla fija)."""
    rng = random.Random(seed)
    xy = [(25, 25)] + [(rng.randint(0, 50), rng.randint(0, 50)) for _ in range(n)]
    xy.append(xy[0])  # n+1 = deposito de retorno

    def d(a, b):
        return round(math.hypot(xy[a][0] - xy[b][0], xy[a][1] - xy[b][1]))

    td = [[d(i, j) for j in range(n + 2)] for i in range(n + 2)]
    tt = [row[:] for row in td]  # velocidad unitaria: tt_ij = td_ij

    q = [[0] * T for _ in range(n + 2)]
    for i in range(1, n + 1):
        for t in range(T):
            if rng.random() < p_pedido:
                q[i][t] = rng.randint(5, 20)
    for i in range(1, n + 1):  # todo cliente con al menos un pedido
        if sum(q[i]) == 0:
            q[i][rng.randrange(T)] = rng.randint(5, 20)

    ventana = {}
    for i in range(1, n + 1):
        if rng.random() < frac_tw:
            c = rng.randint(aW + 60, bW - 60)
            ventana[i] = [max(aW, c - ancho_tw // 2), min(bW, c + ancho_tw // 2)]

    dem_dia = max(sum(q[i][t] for i in range(1, n + 1)) for t in range(T))
    Q = math.ceil(holgura_Q * dem_dia / R)
    return dict(nombre=nombre, seed=seed, n=n, T=T, R=R, Q=Q, aW=aW, bW=bW,
                st=[0] + [st] * n + [0], xy=xy, td=td, tt=tt, q=q,
                ventana={str(k): v for k, v in ventana.items()})


def guardar(inst):
    os.makedirs(DIR_INST, exist_ok=True)
    with open(os.path.join(DIR_INST, inst["nombre"] + ".json"), "w") as f:
        json.dump(inst, f)


def cargar(ruta):
    with open(ruta) as f:
        inst = json.load(f)
    inst["ventana"] = {int(k): v for k, v in inst["ventana"].items()}
    return inst


# ----------------------------------------------------------------------------
# Modelo
# ----------------------------------------------------------------------------
def construir_modelo(inst, Q=None):
    n, T, R = inst["n"], inst["T"], inst["R"]
    Q = inst["Q"] if Q is None else Q
    td, tt, st, q = inst["td"], inst["tt"], inst["st"], inst["q"]
    aW, bW, tw = inst["aW"], inst["bW"], inst["ventana"]
    fin = n + 1
    D, Rs = range(T), range(R)

    # Cotas de W_it: ventana (8) si i in N_TW; si no, horario del deposito.
    lb = {i: max(tw[i][0] if i in tw else aW, aW + tt[0][i]) for i in range(1, n + 1)}
    ub = {i: min(tw[i][1] if i in tw else bW, bW - st[i] - tt[i][fin]) for i in range(1, n + 1)}

    m = gp.Model("conVRP")
    pedidos = {t: [i for i in range(1, n + 1) if q[i][t] > 0] for t in D}

    # Arcos A por dia (solo nodos con pedido ese dia + depositos), con preproceso por ventanas
    arcos = {}
    for t in D:
        P = pedidos[t]
        A = [(0, j) for j in P] + [(i, fin) for i in P] + [(0, fin)]
        A += [(i, j) for i in P for j in P if i != j and lb[i] + st[i] + tt[i][j] <= ub[j]]
        arcos[t] = A

    X = {(r, i, j, t): m.addVar(vtype=GRB.BINARY, obj=td[i][j], name=f"X_{r}_{i}_{j}_{t}")
         for t in D for (i, j) in arcos[t] for r in Rs}
    Z = {(r, i): m.addVar(vtype=GRB.BINARY, name=f"Z_{r}_{i}")
         for r in Rs for i in range(1, n + 1)}
    W = {(i, t): m.addVar(lb=lb[i], ub=ub[i], name=f"W_{i}_{t}")
         for t in D for i in pedidos[t]}
    dW = {r: m.addVar(lb=0, ub=bW, name=f"dW_{r}") for r in Rs}
    rW = {(r, t): m.addVar(lb=0, ub=bW, name=f"rW_{r}_{t}") for r in Rs for t in D}
    m.ModelSense = GRB.MINIMIZE

    # (2) cada nodo en exactamente una ruta
    for i in range(1, n + 1):
        m.addConstr(gp.quicksum(Z[r, i] for r in Rs) == 1, name=f"c2_{i}")

    # (3)-(4) grado de entrada/salida de cada nodo con pedido el dia t
    for r in Rs:
        for t in D:
            for j in pedidos[t]:
                m.addConstr(gp.quicksum(X[r, i, k, t] for (i, k) in arcos[t] if k == j) == Z[r, j],
                            name=f"c3_{r}_{j}_{t}")
                m.addConstr(gp.quicksum(X[r, k, i, t] for (k, i) in arcos[t] if k == j) == Z[r, j],
                            name=f"c4_{r}_{j}_{t}")

    # (5) cada ruta sale del deposito una vez por dia
    for r in Rs:
        for t in D:
            m.addConstr(gp.quicksum(X[r, 0, j, t] for (i, j) in arcos[t] if i == 0) == 1,
                        name=f"c5_{r}_{t}")

    # (7) tiempo de llegada, Big-M ajustado por arco
    for r in Rs:
        for t in D:
            for (i, j) in arcos[t]:
                if i == 0 or j == fin:
                    continue
                M = max(0.0, ub[i] + st[i] + tt[i][j] - lb[j])
                m.addConstr(W[i, t] + st[i] + tt[i][j] <= W[j, t] + M * (1 - X[r, i, j, t]),
                            name=f"c7_{r}_{i}_{j}_{t}")

    # (9) salida del deposito coordinada con la primera entrega
    for r in Rs:
        for t in D:
            for j in pedidos[t]:
                M = max(0.0, bW + tt[0][j] - lb[j])
                m.addConstr(dW[r] + tt[0][j] <= W[j, t] + M * (1 - X[r, 0, j, t]),
                            name=f"c9_{r}_{j}_{t}")

    # (10) retorno coordinado con la ultima entrega
    for r in Rs:
        for t in D:
            for i in pedidos[t]:
                M = max(0.0, ub[i] + st[i] + tt[i][0] - aW)
                m.addConstr(W[i, t] + st[i] + tt[i][0] <= rW[r, t] + M * (1 - X[r, i, fin, t]),
                            name=f"c10_{r}_{i}_{t}")

    # (11)-(12) horario de operacion del deposito
    for r in Rs:
        m.addConstr(dW[r] >= aW, name=f"c11_{r}")
        for t in D:
            m.addConstr(rW[r, t] <= bW, name=f"c12_{r}_{t}")

    # (14) capacidad
    cap = {}
    for r in Rs:
        for t in D:
            cap[r, t] = m.addConstr(gp.quicksum(q[i][t] * Z[r, i] for i in range(1, n + 1)) <= Q,
                                    name=f"c14_{r}_{t}")

    m.update()
    m._cap = cap
    return m


def parametros(m, timelimit, **extra):
    m.Params.Threads = 1
    m.Params.TimeLimit = timelimit
    m.Params.Seed = 0
    for k, v in extra.items():
        m.setParam(k, v)


def resumen(m, etiqueta):
    tiene = m.SolCount > 0
    return dict(config=etiqueta, estado=m.Status, tiempo_s=round(m.Runtime, 2),
                obj=round(m.ObjVal, 3) if tiene else None,
                cota=round(m.ObjBound, 3),
                gap_pct=round(100 * m.MIPGap, 3) if tiene else None,
                nodos=int(m.NodeCount))


def guardar_csv(filas, nombre):
    import csv
    os.makedirs(DIR_RES, exist_ok=True)
    ruta = os.path.join(DIR_RES, nombre)
    with open(ruta, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"-> {ruta}")


# ----------------------------------------------------------------------------
# Experimentos
# ----------------------------------------------------------------------------
def exp_relajacion(inst, tl, z_milp=None):
    m = construir_modelo(inst)
    rel = m.relax()  # X y Z -> [0,1]
    rel.Params.OutputFlag = 0
    rel.Params.Threads = 1
    rel.optimize()
    z_lp = rel.ObjVal
    if z_milp is None:
        b = construir_modelo(inst)
        parametros(b, tl, OutputFlag=0)
        b.optimize()
        z_milp = b.ObjVal
    brecha = 100 * (z_milp - z_lp) / z_milp
    fila = dict(instancia=inst["nombre"], z_lp=round(z_lp, 3), z_milp=round(z_milp, 3),
                brecha_integralidad_pct=round(brecha, 2))
    print(fila)
    guardar_csv([fila], f"{inst['nombre']}_relajacion.csv")
    return fila


CONFIGS = [
    ("baseline", {}),
    ("Cuts=0", {"Cuts": 0}),
    ("Presolve=0", {"Presolve": 0}),
    ("MIPFocus=1", {"MIPFocus": 1}),
    ("MIPFocus=3", {"MIPFocus": 3}),
    ("Heuristics=0", {"Heuristics": 0}),
]


def exp_configs(inst, tl):
    filas = []
    for nombre, p in CONFIGS:
        m = construir_modelo(inst)
        parametros(m, tl, OutputFlag=0, **p)
        m.optimize()
        f = resumen(m, nombre)
        f["instancia"] = inst["nombre"]
        print(f)
        filas.append(f)
    guardar_csv(filas, f"{inst['nombre']}_configs.csv")
    return filas


def exp_tune(inst, tl, tune_tl=1200):
    m = construir_modelo(inst)
    parametros(m, tl, OutputFlag=0)
    m.Params.TuneTimeLimit = tune_tl
    m.tune()
    if m.TuneResultCount == 0:
        print("tune no encontro mejores parametros")
        return None
    m.getTuneResult(0)  # carga los mejores parametros en el modelo
    ruta = os.path.join(DIR_RES, f"{inst['nombre']}_tune.prm")
    os.makedirs(DIR_RES, exist_ok=True)
    m.write(ruta)
    m.Params.TimeLimit = tl
    m.Params.Threads = 1
    m.optimize()
    f = resumen(m, "tune")
    f["instancia"] = inst["nombre"]
    print(f)
    guardar_csv([f], f"{inst['nombre']}_tune.csv")
    return f


def exp_sensibilidad(inst, tl):
    m = construir_modelo(inst)
    parametros(m, tl, OutputFlag=0)
    m.optimize()
    if m.SolCount == 0:
        print("sin incumbente")
        return None
    fx = m.fixed()  # enteras fijas -> LP
    fx.Params.OutputFlag = 0
    fx.Params.Threads = 1
    fx.optimize()
    filas = []
    for (r, t), c in m._cap.items():
        cf = fx.getConstrByName(c.ConstrName)
        filas.append(dict(instancia=inst["nombre"], ruta=r, dia=t, Q=inst["Q"],
                          carga=round(inst["Q"] - cf.Slack, 2), holgura=round(cf.Slack, 2),
                          Pi=round(cf.Pi, 4), SARHSLow=round(cf.SARHSLow, 2),
                          SARHSUp=cf.SARHSUp if cf.SARHSUp >= 1e20 else round(cf.SARHSUp, 2)))
    for f in filas:
        print(f)
    guardar_csv(filas, f"{inst['nombre']}_sensibilidad.csv")
    return filas


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("gen")
    r = sp.add_parser("run")
    r.add_argument("instancia")
    r.add_argument("exp", choices=["relax", "configs", "tune", "sens", "all"])
    r.add_argument("--timelimit", type=float, default=600)
    r.add_argument("--tune-timelimit", type=float, default=1200)
    a = ap.parse_args()

    if a.cmd == "gen":
        guardar(generar_instancia("inst1", seed=11, n=15, frac_tw=0.6, ancho_tw=60, holgura_Q=1.10))
        guardar(generar_instancia("inst2", seed=22, n=16, frac_tw=0.75, ancho_tw=45, holgura_Q=1.05))
        print("instancias generadas en", DIR_INST)
        return

    inst = cargar(a.instancia)
    if a.exp in ("relax", "all"):
        exp_relajacion(inst, a.timelimit)
    if a.exp in ("configs", "all"):
        exp_configs(inst, a.timelimit)
    if a.exp in ("tune", "all"):
        exp_tune(inst, a.timelimit, a.tune_timelimit)
    if a.exp in ("sens", "all"):
        exp_sensibilidad(inst, a.timelimit)


if __name__ == "__main__":
    main()
