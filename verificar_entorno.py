"""Verifica el entorno para la Tarea 3 e imprime un unico bloque de texto.

Uso:  python verificar_entorno.py
Comprueba: Python, gurobipy con licencia completa (modelo de 2500 variables y
2500 restricciones, por sobre el limite de 2000 de la licencia restringida),
docplex/CPLEX (modelo de 1500 variables y 1500 restricciones, por sobre el
limite de 1000 de la Community Edition) y la variable CPLEX_STUDIO_DIR222.
"""
import os
import platform
import sys

LINEAS = []


def out(clave, valor):
    LINEAS.append(f"{clave:<28}{valor}")


def prueba_gurobi():
    try:
        import gurobipy as gp
        v = ".".join(map(str, gp.gurobi.version()))
        out("gurobipy", f"importado, version {v}")
    except Exception as exc:
        out("gurobipy", f"FALLA al importar: {exc}")
        return
    try:
        m = gp.Model()
        m.Params.OutputFlag = 0
        n = 2500
        x = m.addVars(n, vtype="B")
        m.addConstrs((x[i] + x[(i + 1) % n] <= 1 for i in range(n)))
        m.setObjective(x.sum(), gp.GRB.MAXIMIZE)
        m.optimize()
        out("gurobi licencia", f"OK ({n} vars, {n} restr., objetivo {m.ObjVal:.0f}, "
            f"esperado {n // 2})")
    except Exception as exc:
        out("gurobi licencia", f"FALLA (licencia restringida?): {exc}")


def prueba_cplex():
    out("CPLEX_STUDIO_DIR222", os.environ.get("CPLEX_STUDIO_DIR222") or "no definida")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from convrp_tc3 import importar_cplex
        Model, Limites = importar_cplex()
    except Exception as exc:
        out("docplex", f"FALLA al importar: {exc}")
        return
    try:
        import docplex
        out("docplex", f"importado, version {docplex.__version__}")
    except Exception:
        out("docplex", "importado")
    try:
        import cplex
        out("cplex (paquete python)", f"version {cplex.Cplex().get_version()}")
    except Exception as exc:
        out("cplex (paquete python)", f"no disponible: {exc}")
    try:
        n = 1500
        mdl = Model()
        x = mdl.binary_var_list(n, name="x")
        mdl.add_constraints([x[i] + x[(i + 1) % n] <= 1 for i in range(n)])
        mdl.maximize(mdl.sum(x))
        s = mdl.solve()
        if s is None:
            out("cplex tamano", f"FALLA: sin solucion ({mdl.solve_details.status})")
        else:
            out("cplex tamano", f"OK sin error 1016 ({n} vars, {n} restr., "
                f"objetivo {s.objective_value:.0f}, esperado {n // 2})")
    except Limites as exc:
        out("cplex tamano", f"FALLA, limite Community Edition (error 1016): {exc}")
    except Exception as exc:
        out("cplex tamano", f"FALLA: {exc}")


def main():
    out("Python", f"{platform.python_version()} ({platform.architecture()[0]})")
    out("Sistema", f"{platform.system()} {platform.release()}")
    prueba_gurobi()
    prueba_cplex()
    print("=== VERIFICACION DE ENTORNO TC3 ===")
    print("\n".join(LINEAS))
    print("===================================")


if __name__ == "__main__":
    main()
