"""Graficos y tabla comparativa de la Tarea 3 (Gurobi vs CPLEX).

Lee resultados/inst*_compare_gurobi-cplex_{h1,hdef}.csv y genera:
  figuras/a_tiempo_mip_1hilo.png
  figuras/b_nodos_mip_1hilo.png
  figuras/c_tiempo_1hilo_vs_defecto.png
  figuras/mapa_inst1.png, figuras/mapa_inst2.png (depósito y clientes de cada instancia)
  tabla_comparacion.md

No ejecuta ningun solver. Uso:  python graficos_tc3.py
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd

RAIZ = os.path.dirname(os.path.abspath(__file__))
DIR_RES = os.path.join(RAIZ, "resultados")
DIR_FIG = os.path.join(RAIZ, "figuras")
DPI = 300

# Un color fijo por solver (paleta Okabe-Ito, apta para daltonismo)
COLOR = {"gurobi": "#0072B2", "cplex": "#D55E00"}
NOMBRE = {"gurobi": "Gurobi", "cplex": "CPLEX"}
SOLVERS = ["gurobi", "cplex"]
TINTA, TINTA_SEC, GRILLA = "#222222", "#555555", "#DDDDDD"


def cargar():
    filas = []
    for ruta in sorted(glob.glob(os.path.join(DIR_RES, "inst*_compare_gurobi-cplex_h*.csv"))):
        df = pd.read_csv(ruta)
        df["hilos"] = df["hilos"].astype(str)
        filas.append(df)
    if not filas:
        raise SystemExit("No hay CSV de compare en resultados/")
    df = pd.concat(filas, ignore_index=True)
    df["config"] = df["hilos"].map(lambda h: "h1" if h == "1" else "hdef")
    # n_bin no es confiable en las filas de relajacion (CPLEX reporta 0): se descarta
    df.loc[df["modelo"] == "relax", "n_bin"] = pd.NA
    return df


def estilo(ax, ylabel):
    ax.set_ylabel(ylabel, color=TINTA)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRILLA, linewidth=0.8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#999999")
    ax.tick_params(colors=TINTA_SEC)
    ax.set_ylim(bottom=0)


def etiquetar(ax, barras, fmt):
    for b in barras:
        ax.annotate(fmt(b.get_height()), (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                    fontsize=9, color=TINTA)


def barras_por_solver(df, col, ylabel, titulo, archivo, fmt):
    mip = df[(df["modelo"] == "mip") & (df["config"] == "h1")]
    insts = sorted(mip["instancia"].unique())
    ancho = 0.36
    fig, ax = plt.subplots(figsize=(7, 4.6))
    for k, s in enumerate(SOLVERS):
        vals = [mip[(mip["instancia"] == i) & (mip["solver"] == s)][col].iloc[0] for i in insts]
        xs = [j + (k - 0.5) * ancho for j in range(len(insts))]
        etiquetar(ax, ax.bar(xs, vals, ancho * 0.92, color=COLOR[s], label=NOMBRE[s]), fmt)
    ax.set_xticks(range(len(insts)))
    ax.set_xticklabels(insts)
    ax.set_xlabel("Instancia", color=TINTA)
    estilo(ax, ylabel)
    ax.margins(y=0.12)
    ax.set_ylim(bottom=0)
    ax.set_title(titulo, loc="left", color=TINTA, fontsize=12)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(DIR_FIG, archivo), dpi=DPI)
    plt.close(fig)


def fig_c(df):
    mip = df[df["modelo"] == "mip"]
    insts = sorted(mip["instancia"].unique())
    ancho = 0.19
    fig, ax = plt.subplots(figsize=(8, 4.8))
    pos = 0
    for k, (s, cfg) in enumerate([(s, c) for s in SOLVERS for c in ("h1", "hdef")]):
        vals = [mip[(mip["instancia"] == i) & (mip["solver"] == s) & (mip["config"] == cfg)]["tiempo_s"].iloc[0]
                for i in insts]
        xs = [j + (k - 1.5) * ancho for j in range(len(insts))]
        barras = ax.bar(xs, vals, ancho * 0.92, color=COLOR[s],
                        alpha=1.0 if cfg == "h1" else 0.55,
                        hatch=None if cfg == "h1" else "///", edgecolor="white" if cfg == "h1" else COLOR[s],
                        linewidth=0.8)
        etiquetar(ax, barras, lambda v: f"{v:.0f}")
    ax.set_xticks(range(len(insts)))
    ax.set_xticklabels(insts)
    ax.set_xlabel("Instancia", color=TINTA)
    estilo(ax, "Tiempo MIP (s)")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.3)  # espacio para la leyenda
    ax.set_title("Tiempo MIP: 1 hilo vs hilos por defecto", loc="left", color=TINTA, fontsize=12)
    handles = [Patch(facecolor=COLOR[s], label=NOMBRE[s]) for s in SOLVERS]
    handles += [Patch(facecolor="#888888", label="1 hilo"),
                Patch(facecolor="#CCCCCC", hatch="///", edgecolor="#888888", label="Hilos por defecto (8)")]
    ax.legend(handles=handles, frameon=False, loc="upper right", ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(DIR_FIG, "c_tiempo_1hilo_vs_defecto.png"), dpi=DPI)
    plt.close(fig)


def mapa_instancia(ruta_json):
    """Mapa de una instancia: deposito (D) y clientes con su ID.
    Relleno = cliente con ventana horaria propia; hueco = sin ventana propia."""
    with open(ruta_json, encoding="utf-8") as f:
        inst = json.load(f)
    nombre, n, Q = inst["nombre"], inst["n"], inst["Q"]
    xy, con_ventana = inst["xy"], {int(k) for k in inst["ventana"]}
    verde = "#009E73"
    fig, ax = plt.subplots(figsize=(6, 5.4))
    ax.scatter(*xy[0], marker="s", s=110, color=TINTA, zorder=3)
    ax.annotate("D", xy[0], xytext=(7, 5), textcoords="offset points", fontsize=10,
                fontweight="bold", color=TINTA)
    colocadas = [xy[0]]          # etiquetas ya puestas (centros, en unidades de datos)
    candidatos = [(1.9, 1.3), (-1.9, 1.3), (1.9, -1.7), (-1.9, -1.7),
                  (0, 2.3), (0, -2.5), (-2.8, -0.2), (2.8, -0.2)]
    for i in range(1, n + 1):
        x, y = xy[i]
        if i in con_ventana:
            ax.scatter(x, y, s=55, color=verde, zorder=3)
        else:
            ax.scatter(x, y, s=55, facecolor="white", edgecolor=verde, linewidth=1.8, zorder=3)
        # elige la primera posicion de la etiqueta que no pisa otros puntos ni etiquetas
        elegido = candidatos[0]
        for dx, dy in candidatos:
            cx, cy = x + dx, y + dy
            libre = all(abs(cx - px) > 2.6 or abs(cy - py) > 2.0
                        for j, (px, py) in enumerate(xy) if j != i)
            libre = libre and all(abs(cx - lx) > 3.0 or abs(cy - ly) > 2.2 for lx, ly in colocadas[1:])
            if libre:
                elegido = (dx, dy)
                break
        colocadas.append((x + elegido[0], y + elegido[1]))
        ax.text(x + elegido[0], y + elegido[1], str(i), ha="center", va="center",
                fontsize=9, color=TINTA)
    ax.set_xlim(-4, 56)
    ax.set_ylim(-4, 56)
    ax.set_aspect("equal")
    ax.set_xlabel("Coordenada x", color=TINTA)
    ax.set_ylabel("Coordenada y", color=TINTA)
    ax.set_axisbelow(True)
    ax.grid(True, color=GRILLA, linewidth=0.8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#999999")
    ax.tick_params(colors=TINTA_SEC)
    ax.set_title(f"{nombre} · {n} clientes · Q = {Q}", loc="left", color=TINTA, fontsize=12)
    handles = [
        plt.Line2D([], [], marker="s", linestyle="", color=TINTA, markersize=8, label="Depósito (D)"),
        plt.Line2D([], [], marker="o", linestyle="", color=verde, markersize=7,
                   label="Cliente con ventana horaria"),
        plt.Line2D([], [], marker="o", linestyle="", markerfacecolor="white", markeredgecolor=verde,
                   markeredgewidth=1.8, markersize=7, label="Cliente sin ventana horaria"),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14),
              ncol=1, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(DIR_FIG, f"mapa_{nombre}.png"), dpi=DPI)
    plt.close(fig)


def fmt_num(v, dec=2):
    return "—" if pd.isna(v) else f"{v:,.{dec}f}"


def fmt_ent(v):
    return "—" if pd.isna(v) else f"{int(v):,}"


def tabla(df):
    L = ["# Comparación Gurobi vs CPLEX", "",
         "Generada por `graficos_tc3.py` a partir de `resultados/*_compare_gurobi-cplex_*.csv`. "
         "Razón = CPLEX / Gurobi (>1: CPLEX es más lento / explora más nodos). "
         "Las filas de relajación no tienen nodos.", ""]
    cab = ("| Instancia | Modelo | Hilos | Obj Gurobi | Obj CPLEX | Tiempo Gurobi (s) | Tiempo CPLEX (s) | "
           "Razón tiempo | Nodos Gurobi | Nodos CPLEX | Razón nodos |")
    L += [cab, "|" + "---|" * 11]
    orden_m = {"relax": 0, "mip": 1}
    for inst in sorted(df["instancia"].unique()):
        for modelo in ("relax", "mip"):
            for cfg, etq in (("h1", "1"), ("hdef", "defecto")):
                sub = df[(df["instancia"] == inst) & (df["modelo"] == modelo) & (df["config"] == cfg)]
                g = sub[sub["solver"] == "gurobi"].iloc[0]
                c = sub[sub["solver"] == "cplex"].iloc[0]
                rt = c["tiempo_s"] / g["tiempo_s"]
                rn = c["nodos"] / g["nodos"] if pd.notna(g["nodos"]) and pd.notna(c["nodos"]) else float("nan")
                L.append(f"| {inst} | {'Relajación' if modelo == 'relax' else 'MIP'} | {etq} | "
                         f"{fmt_num(g['obj'], 1)} | {fmt_num(c['obj'], 1)} | "
                         f"{fmt_num(g['tiempo_s'], 3)} | {fmt_num(c['tiempo_s'], 3)} | {fmt_num(rt, 2)} | "
                         f"{fmt_ent(g['nodos'])} | {fmt_ent(c['nodos'])} | {fmt_num(rn, 2)} |")
    L += ["", "Notas: tiempos de relajación de ~0.01–0.08 s son ruido de medición; no comparar sus razones. "
          "", ""]
    with open(os.path.join(RAIZ, "tabla_comparacion.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main():
    os.makedirs(DIR_FIG, exist_ok=True)
    df = cargar()
    barras_por_solver(df, "tiempo_s", "Tiempo MIP (s)", "Tiempo MIP con 1 hilo",
                      "a_tiempo_mip_1hilo.png", lambda v: f"{v:.1f}")
    barras_por_solver(df, "nodos", "Nodos explorados", "Nodos explorados con 1 hilo",
                      "b_nodos_mip_1hilo.png", lambda v: f"{int(v):,}")
    fig_c(df)
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "instancias", "inst*.json"))):
        mapa_instancia(ruta)
    tabla(df)
    print("Figuras en", DIR_FIG, "y tabla_comparacion.md generados")


if __name__ == "__main__":
    main()
