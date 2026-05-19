"""
Descomposición Oaxaca-Blinder de la brecha salarial entre dos grupos.

Tres versiones:
- Clásica con referencia en hombres (β_h)
- Clásica con referencia en mujeres (β_m)
- Pooled (Neumark, 1988) usando los coeficientes de una regresión pooled

La descomposición tradicional:
    brecha = (X_h - X_m) · β_ref + ...

La versión pooled estima un β* sobre todos los datos juntos y descompone:
    brecha = (X_h - X_m) · β*       (parte explicada)
           + X_h · (β_h - β*)       (parte no explicada — "ventaja masculina")
           + X_m · (β* - β_m)       (parte no explicada — "desventaja femenina")

Esta versión es menos sensible a la elección del grupo de referencia y es el
estándar actual en economía laboral aplicada.
"""

from __future__ import annotations
from typing import Sequence

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def descomponer_pooled(df: pd.DataFrame, formula: str, peso: str,
                        grupo: str, vars_explicativas: Sequence[str],
                        bloques: dict[str, list[str]] | None = None,
                        ) -> dict:
    """Descomposición Oaxaca-Blinder pooled (Neumark) ponderada.

    Estima tres regresiones (hombres, mujeres, pooled) y descompone la diferencia
    promedio de log-salarios en componente explicado y no explicado.

    Parameters
    ----------
    df : DataFrame con todos los datos
    formula : fórmula patsy SIN incluir grupo (igual para los 3 modelos)
    peso : nombre de la columna de factor de expansión
    grupo : nombre de la columna binaria 0/1 (0=referencia "alta", 1=otra)
    vars_explicativas : lista de nombres de columnas que entran al modelo
        — usado para los aportes por bloque
    bloques : dict {nombre_bloque: [vars]} para reportar contribuciones por bloque
        — debe cubrir todas las vars_explicativas

    Returns
    -------
    dict con campos:
        brecha_log, explicado, no_explicado, no_explicado_h, no_explicado_m
        explicado_por_bloque (dict), tabla_completa (DataFrame)
    """
    grp0 = df[df[grupo] == 0]   # típicamente: hombres
    grp1 = df[df[grupo] == 1]   # típicamente: mujeres
    w0, w1 = grp0[peso], grp1[peso]

    # Tres regresiones
    res0 = smf.wls(formula, data=grp0, weights=w0).fit()
    res1 = smf.wls(formula, data=grp1, weights=w1).fit()
    res_pool = smf.wls(formula, data=df,  weights=df[peso]).fit()

    beta0 = res0.params
    beta1 = res1.params
    bstar = res_pool.params

    # Media ponderada de cada variable en cada grupo, usando la matriz de
    # diseño que armó patsy. Esto garantiza alineación con los coeficientes.
    X0 = pd.DataFrame(res0.model.exog, columns=res0.model.exog_names)
    X1 = pd.DataFrame(res1.model.exog, columns=res1.model.exog_names)
    X0_mean = np.average(X0, axis=0, weights=w0.values)
    X1_mean = np.average(X1, axis=0, weights=w1.values)
    X0_mean = pd.Series(X0_mean, index=res0.model.exog_names)
    X1_mean = pd.Series(X1_mean, index=res1.model.exog_names)

    # Brecha total observada (en log)
    y0_mean = np.average(grp0[res0.model.endog_names], weights=w0.values) \
              if res0.model.endog_names in grp0.columns else None
    # Más robusto: usar predict de cada modelo en su muestra
    brecha_log = float((X0_mean * beta0).sum() - (X1_mean * beta1).sum())

    # Descomposición pooled
    explicado     = float(((X0_mean - X1_mean) * bstar).sum())
    no_explicado_h = float((X0_mean * (beta0 - bstar)).sum())
    no_explicado_m = float((X1_mean * (bstar - beta1)).sum())
    no_explicado   = no_explicado_h + no_explicado_m

    # Aporte explicado por bloque
    aporte_bloque = {}
    if bloques is not None:
        for nombre_bloque, vars_bloque in bloques.items():
            cols_bloque = [c for c in X0_mean.index
                           if any(c == v or c.startswith(f"C({v})") for v in vars_bloque)]
            if cols_bloque:
                aporte = float(((X0_mean[cols_bloque] - X1_mean[cols_bloque]) *
                                bstar[cols_bloque]).sum())
                aporte_bloque[nombre_bloque] = aporte

    return {
        "brecha_log": brecha_log,
        "explicado": explicado,
        "no_explicado": no_explicado,
        "no_explicado_h": no_explicado_h,
        "no_explicado_m": no_explicado_m,
        "explicado_pct_brecha": explicado / brecha_log * 100 if brecha_log else 0,
        "no_explicado_pct_brecha": no_explicado / brecha_log * 100 if brecha_log else 0,
        "aporte_por_bloque": aporte_bloque,
        "r2_pool": res_pool.rsquared,
    }


def bootstrap_oaxaca(df: pd.DataFrame, formula: str, peso: str,
                      grupo: str, vars_explicativas: Sequence[str],
                      bloques: dict[str, list[str]],
                      n_iter: int = 500, seed: int = 42,
                      ) -> pd.DataFrame:
    """Bootstrap no paramétrico de la descomposición Oaxaca-Blinder pooled.

    En cada réplica re-muestra el dataset con reemplazo (peso constante por fila),
    re-estima los tres modelos y la descomposición. Devuelve un DataFrame con una
    fila por réplica y los componentes en columnas.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    df_idx = df.reset_index(drop=True)

    filas = []
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        boot = df_idx.iloc[idx]
        try:
            res = descomponer_pooled(boot, formula, peso, grupo,
                                       vars_explicativas, bloques)
            fila = {
                "iter": i,
                "brecha_log": res["brecha_log"],
                "explicado": res["explicado"],
                "no_explicado": res["no_explicado"],
            }
            for nombre, valor in res["aporte_por_bloque"].items():
                fila[f"aporte_{nombre}"] = valor
            filas.append(fila)
        except Exception:
            continue  # tolerante a réplicas con matriz singular

    return pd.DataFrame(filas)
