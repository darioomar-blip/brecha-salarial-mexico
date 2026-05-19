"""
Módulo para cargar microdatos de la ENOE (INEGI) y construir el dataset
listo para regresiones tipo Mincer.

El INEGI publica los microdatos en archivos CSV con encoding latin-1 (no UTF-8)
y nombres de tabla que varían ligeramente entre trimestres. Las funciones aquí
detectan los archivos por patrón en lugar de asumir nombres fijos, y devuelven
DataFrames con nombres de columnas en minúsculas para evitar problemas de case.

Llaves canónicas para pegar las tablas individuales:
    cd_a, ent, con, v_sel, n_hog, h_mud, n_ren

El factor de expansión (`fac_tri` o `fac`) vive en la tabla sociodemográfica
y se arrastra al merge.
"""

from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd


# Llaves para hacer merge entre tablas ENOE
LLAVES = ["cd_a", "ent", "con", "v_sel", "n_hog", "h_mud", "n_ren"]


def detectar_archivos(carpeta: str | Path) -> dict[str, Path]:
    """Detecta los CSVs de SDEMT, COE1 y COE2 dentro de la carpeta.

    El INEGI cambia las nomenclaturas casi cada trimestre. Esta función busca
    por patrón con regex y devuelve un diccionario con las rutas detectadas.

    Parameters
    ----------
    carpeta : str o Path
        Carpeta donde se descomprimió el ZIP de la ENOE.

    Returns
    -------
    dict con llaves "sdemt", "coe1", "coe2" apuntando a Path de cada CSV.

    Raises
    ------
    FileNotFoundError si alguna de las tres tablas no aparece.
    """
    carpeta = Path(carpeta)
    if not carpeta.exists():
        raise FileNotFoundError(f"No existe la carpeta {carpeta}")

    csvs = list(carpeta.rglob("*.csv")) + list(carpeta.rglob("*.CSV"))
    encontrados: dict[str, Path] = {}

    patrones = {
        "sdemt": re.compile(r"sdem", re.IGNORECASE),
        "coe1":  re.compile(r"coe1",  re.IGNORECASE),
        "coe2":  re.compile(r"coe2",  re.IGNORECASE),
    }

    for tabla, patron in patrones.items():
        for csv in csvs:
            if patron.search(csv.name):
                encontrados[tabla] = csv
                break

    faltan = [t for t in patrones if t not in encontrados]
    if faltan:
        raise FileNotFoundError(
            f"No encontré las tablas {faltan} en {carpeta}. "
            f"Archivos vistos: {[c.name for c in csvs[:10]]}"
        )

    return encontrados


def cargar_tabla(ruta: str | Path) -> pd.DataFrame:
    """Lee un CSV de la ENOE con el encoding correcto y baja a minúsculas."""
    df = pd.read_csv(ruta, encoding="latin-1", low_memory=False)
    df.columns = df.columns.str.lower()
    return df


def pegar_enoe(sdemt: pd.DataFrame, coe1: pd.DataFrame, coe2: pd.DataFrame) -> pd.DataFrame:
    """Pega las tres tablas ENOE por las llaves canónicas.

    Se hace inner join — solo nos quedamos con personas que aparecen en las
    tres. Pierde un puñado de registros con inconsistencias entre tablas
    (típicamente <1% del total).
    """
    llaves_disponibles = [k for k in LLAVES if k in sdemt.columns and k in coe1.columns]

    df = sdemt.merge(coe1, on=llaves_disponibles, how="inner", suffixes=("", "_c1"))
    df = df.merge(coe2, on=llaves_disponibles, how="inner", suffixes=("", "_c2"))
    return df


def _resolver_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    """Devuelve la primera columna que existe en el df, o None."""
    for c in candidatos:
        if c in df.columns:
            return c
    return None


def construir_variables_mincer(df: pd.DataFrame) -> pd.DataFrame:
    """Construye las variables del modelo Mincer a partir del DataFrame pegado.

    Variables construidas:
        mujer                : 1 si sexo == 2 (codificación INEGI), 0 si == 1
        anios_escolaridad    : años aprobados de educación (0–24)
        edad                 : copia limpia
        experiencia          : edad - anios_escolaridad - 6 (mínimo 0)
        experiencia2         : experiencia al cuadrado
        ocupada              : 1 si está ocupada (clase2 == 1)
        ingreso_mensual      : pesos por mes
        horas_semanales      : horas trabajadas a la semana
        ingreso_hora         : ingreso_mensual / (horas_semanales * 4.33)
        log_ingreso_hora     : logaritmo natural del ingreso por hora
        fac_tri              : factor de expansión (renombrado si vino como `fac`)

    Las personas sin ingreso reportado, con horas == 0, o no ocupadas, se
    mantienen en el DataFrame pero con NaN en las variables salariales.
    El filtrado final se hace en el notebook para ser explícito.
    """
    out = df.copy()

    # Factor de expansión: en ENOEN suele ser `fac_tri`, en versiones viejas `fac`.
    col_fac = _resolver_columna(out, ["fac_tri", "fac"])
    if col_fac is None:
        raise KeyError("No encontré factor de expansión (fac_tri ni fac).")
    out["fac_tri"] = out[col_fac].astype(float)

    # Sexo: en ENOE 1 = hombre, 2 = mujer.
    # OJO: el INEGI publica varias variables como string con espacios (' ')
    # en lugar de NaN. Convertir a numérico antes de comparar es obligatorio
    # — si no, comparaciones tipo `serie == 2` siempre dan False y todos
    # los registros quedan marcados como hombres.
    col_sex = _resolver_columna(out, ["sex", "sexo"])
    if col_sex is None:
        raise KeyError("No encontré columna de sexo.")
    sex_num = pd.to_numeric(out[col_sex], errors="coerce")
    out["mujer"] = (sex_num == 2).astype("Int64")
    out.loc[sex_num.isna(), "mujer"] = pd.NA

    # Edad
    col_eda = _resolver_columna(out, ["eda", "edad"])
    out["edad"] = pd.to_numeric(out[col_eda], errors="coerce")

    # Escolaridad: anios_esc viene precalculado en algunas versiones; si no,
    # se construye a partir de cs_p13_2 (años aprobados del nivel).
    col_esc = _resolver_columna(out, ["anios_esc", "cs_p13_2"])
    out["anios_escolaridad"] = pd.to_numeric(out[col_esc], errors="coerce")
    # ENOE codifica respuestas no aplica con 99 / 999 — convertir a NaN
    out.loc[out["anios_escolaridad"] >= 90, "anios_escolaridad"] = np.nan
    out["anios_escolaridad"] = out["anios_escolaridad"].clip(lower=0, upper=24)

    # Experiencia potencial (Mincer)
    out["experiencia"] = (out["edad"] - out["anios_escolaridad"] - 6).clip(lower=0)
    out["experiencia2"] = out["experiencia"] ** 2

    # Condición de ocupación. En ENOE `clase2 == 1` significa ocupado.
    col_oc = _resolver_columna(out, ["clase2"])
    if col_oc is not None:
        oc_num = pd.to_numeric(out[col_oc], errors="coerce")
        out["ocupada"] = (oc_num == 1).astype("Int64")
        out.loc[oc_num.isna(), "ocupada"] = pd.NA
    else:
        out["ocupada"] = pd.NA

    # Ingreso mensual. Las variables varían entre trimestres; intentamos varias.
    col_ing = _resolver_columna(out, ["ingocup", "ing7c", "p6c", "p6b2"])
    if col_ing is None:
        raise KeyError("No encontré una variable de ingreso reconocible.")
    out["ingreso_mensual"] = pd.to_numeric(out[col_ing], errors="coerce")
    # Códigos especiales de no respuesta en INEGI suelen ser 999998, 999999
    out.loc[out["ingreso_mensual"] >= 999990, "ingreso_mensual"] = np.nan

    # Horas semanales trabajadas
    col_hrs = _resolver_columna(out, ["hrsocup", "p5b_thrs", "p5c_thrs"])
    if col_hrs is None:
        raise KeyError("No encontré una variable de horas trabajadas.")
    out["horas_semanales"] = pd.to_numeric(out[col_hrs], errors="coerce")
    out.loc[out["horas_semanales"] > 168, "horas_semanales"] = np.nan  # 168 = 7×24

    # Ingreso por hora
    out["ingreso_hora"] = out["ingreso_mensual"] / (out["horas_semanales"] * 4.33)
    out.loc[out["ingreso_hora"] <= 0, "ingreso_hora"] = np.nan
    out["log_ingreso_hora"] = np.log(out["ingreso_hora"])

    # Sector: en ENOE viene como `c_ocu11c` o `rama_est2`. Usamos rama de
    # actividad como primer intento; si no, dejamos NaN y se rehace luego.
    col_sect = _resolver_columna(out, ["rama", "rama_est1", "rama_est2"])
    if col_sect is not None:
        out["sector"] = pd.to_numeric(out[col_sect], errors="coerce")

    # Formalidad (cuando aplica). emp_ppal = 1 → formal, = 2 → informal
    col_form = _resolver_columna(out, ["emp_ppal"])
    if col_form is not None:
        form_num = pd.to_numeric(out[col_form], errors="coerce")
        out["formal"] = (form_num == 1).astype("Int64")
        out.loc[form_num.isna(), "formal"] = pd.NA

    return out


def winsorizar(serie: pd.Series, weights: pd.Series, p_low: float = 0.01,
               p_high: float = 0.99) -> pd.Series:
    """Winsoriza una serie a los percentiles indicados, ponderando por weights.

    Reemplaza valores debajo de p_low por el valor del p_low, y arriba de p_high
    por el valor del p_high. No descarta filas — solo recorta.
    """
    valida = serie.notna() & weights.notna() & (weights > 0)
    if not valida.any():
        return serie

    # Percentiles ponderados manuales (numpy no los trae directos)
    s = serie[valida].to_numpy()
    w = weights[valida].to_numpy()
    orden = np.argsort(s)
    s_ord, w_ord = s[orden], w[orden]
    cum = np.cumsum(w_ord) / w_ord.sum()

    lo = s_ord[np.searchsorted(cum, p_low)]
    hi = s_ord[np.searchsorted(cum, p_high)]

    return serie.clip(lower=lo, upper=hi)


def media_ponderada(x: pd.Series, weights: pd.Series) -> float:
    """Media ponderada robusta a NaN."""
    m = x.notna() & weights.notna()
    return float(np.average(x[m], weights=weights[m])) if m.any() else float("nan")
