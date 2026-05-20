"""
Genera un dashboard HTML interactivo con Plotly que cuenta la historia
del proyecto. Single-file, self-contained, embebible en cualquier sitio.

Uso:
    python src/dashboard.py
    → escribe outputs/dashboard.html
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Paleta unificada con el resto del proyecto
COLOR_H = "#2c7fb8"
COLOR_M = "#d95f0e"
COLOR_CLARO = "#a6bddb"
GRIS = "#666666"

ESTADOS = {
    1:"Aguascalientes", 2:"Baja California", 3:"Baja California Sur", 4:"Campeche",
    5:"Coahuila", 6:"Colima", 7:"Chiapas", 8:"Chihuahua", 9:"Ciudad de México",
    10:"Durango", 11:"Guanajuato", 12:"Guerrero", 13:"Hidalgo", 14:"Jalisco",
    15:"Estado de México", 16:"Michoacán", 17:"Morelos", 18:"Nayarit", 19:"Nuevo León",
    20:"Oaxaca", 21:"Puebla", 22:"Querétaro", 23:"Quintana Roo", 24:"San Luis Potosí",
    25:"Sinaloa", 26:"Sonora", 27:"Tabasco", 28:"Tamaulipas", 29:"Tlaxcala",
    30:"Veracruz", 31:"Yucatán", 32:"Zacatecas",
}


def media_ponderada(s: pd.Series, w: pd.Series) -> float:
    m = s.notna() & w.notna()
    return float(np.average(s[m], weights=w[m])) if m.any() else float("nan")


def kpi_cards(df: pd.DataFrame) -> dict:
    h = df[df["mujer"] == 0]
    m = df[df["mujer"] == 1]
    ing_mens_h = media_ponderada(h["ingreso_mensual_w"], h["fac_tri"])
    ing_mens_m = media_ponderada(m["ingreso_mensual_w"], m["fac_tri"])
    hrs_h      = media_ponderada(h["horas_semanales"], h["fac_tri"])
    hrs_m      = media_ponderada(m["horas_semanales"], m["fac_tri"])
    esc_h      = media_ponderada(h["anios_escolaridad"], h["fac_tri"])
    esc_m      = media_ponderada(m["anios_escolaridad"], m["fac_tri"])
    return {
        "brecha_mensual": (ing_mens_h - ing_mens_m) / ing_mens_h * 100,
        "dif_horas":      hrs_h - hrs_m,
        "escolaridad_h":  esc_h,
        "escolaridad_m":  esc_m,
        "ing_mens_h":     ing_mens_h,
        "ing_mens_m":     ing_mens_m,
        "n":              len(df),
    }


def fig_caracterizacion(df: pd.DataFrame) -> go.Figure:
    h = df[df["mujer"] == 0]
    m = df[df["mujer"] == 1]
    casos = [
        ("Escolaridad (años)",   h["anios_escolaridad"],     m["anios_escolaridad"],     ""),
        ("Experiencia (años)",   h["experiencia"],            m["experiencia"],            ""),
        ("% en sector formal",   h["subordinado"].astype(float)*100, m["subordinado"].astype(float)*100, "%"),
        ("Horas semanales",      h["horas_semanales"],        m["horas_semanales"],        ""),
    ]
    fig = go.Figure()
    for titulo, sh, sm, suf in casos:
        vh = media_ponderada(sh, h["fac_tri"])
        vm = media_ponderada(sm, m["fac_tri"])
        fig.add_trace(go.Bar(
            y=[titulo, titulo], x=[vh, vm],
            orientation="h",
            marker_color=[COLOR_H, COLOR_M],
            text=[f"{vh:.1f}{suf}", f"{vm:.1f}{suf}"],
            textposition="inside",
            textfont=dict(color="white", size=14),
            hovertemplate="<b>%{customdata}</b><br>%{x:.2f}" + suf + "<extra></extra>",
            customdata=["Hombres", "Mujeres"],
            showlegend=False,
        ))
    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>Las mujeres ocupadas mexicanas tienen más educación, igual experiencia y más subordinación formal.</b><br><sub>La única variable donde están en desventaja: horas trabajadas.</sub>",
                   x=0.5, xanchor="center"),
        barmode="group",
        height=450,
        margin=dict(l=140, r=40, t=90, b=40),
        xaxis_title=None, yaxis_title=None,
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
    )
    return fig


def fig_horas(df: pd.DataFrame) -> go.Figure:
    h = df[df["mujer"] == 0]
    m = df[df["mujer"] == 1]
    hrs_h = media_ponderada(h["horas_semanales"], h["fac_tri"])
    hrs_m = media_ponderada(m["horas_semanales"], m["fac_tri"])

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=h["horas_semanales"], histnorm="probability", name="Hombres",
        marker_color=COLOR_H, opacity=0.6,
        xbins=dict(start=0, end=80, size=2),
        hovertemplate="<b>Hombres</b><br>Horas: %{x}<br>Proporción: %{y:.2%}<extra></extra>",
    ))
    fig.add_trace(go.Histogram(
        x=m["horas_semanales"], histnorm="probability", name="Mujeres",
        marker_color=COLOR_M, opacity=0.6,
        xbins=dict(start=0, end=80, size=2),
        hovertemplate="<b>Mujeres</b><br>Horas: %{x}<br>Proporción: %{y:.2%}<extra></extra>",
    ))
    fig.add_vline(x=hrs_h, line=dict(color=COLOR_H, dash="dash"),
                   annotation_text=f"Promedio H: {hrs_h:.1f}h",
                   annotation_position="top right")
    fig.add_vline(x=hrs_m, line=dict(color=COLOR_M, dash="dash"),
                   annotation_text=f"Promedio M: {hrs_m:.1f}h",
                   annotation_position="top left")
    fig.update_layout(
        template="plotly_white",
        title=dict(text=f"<b>Las mujeres trabajan {hrs_h-hrs_m:.1f} hrs menos por semana en el mercado remunerado</b>",
                   x=0.5, xanchor="center"),
        barmode="overlay",
        xaxis_title="Horas semanales trabajadas",
        yaxis_title="Proporción de personas ocupadas",
        height=450,
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
        legend=dict(x=0.85, y=0.95),
    )
    return fig


def fig_oaxaca(boot: pd.DataFrame) -> go.Figure:
    brecha = boot["brecha_log"].median()
    horas_pct = boot["aporte_horas"].median() / brecha * 100
    no_exp_pct = boot["no_explicado"].median() / brecha * 100
    horas_lo, horas_hi = np.percentile(boot["aporte_horas"]/boot["brecha_log"]*100, [2.5, 97.5])
    no_lo, no_hi = np.percentile(boot["no_explicado"]/boot["brecha_log"]*100, [2.5, 97.5])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Brecha mensual"], x=[horas_pct],
        orientation="h", name="Horas trabajadas",
        marker_color=COLOR_H,
        text=[f"<b>{horas_pct:.1f}%</b><br><span style='font-size:11px'>IC95: [{horas_lo:.1f}, {horas_hi:.1f}]</span>"],
        textposition="inside",
        textfont=dict(color="white", size=18),
        hovertemplate="<b>Horas trabajadas</b><br>Aporte: %{x:.1f}%<br>IC95: [" + f"{horas_lo:.1f}, {horas_hi:.1f}" + "]<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=["Brecha mensual"], x=[no_exp_pct],
        orientation="h", name="No explicado (residual)",
        marker_color=COLOR_M,
        text=[f"<b>{no_exp_pct:.1f}%</b><br><span style='font-size:11px'>IC95: [{no_lo:.1f}, {no_hi:.1f}]</span>"],
        textposition="inside",
        textfont=dict(color="white", size=18),
        hovertemplate="<b>No explicado</b><br>Residual: %{x:.1f}%<br>IC95: [" + f"{no_lo:.1f}, {no_hi:.1f}" + "]<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>De la brecha mensual del 32%, la mitad la explican las horas. La otra mitad no se explica con variables observables.</b><br><sub>Descomposición Oaxaca-Blinder pooled (Neumark) · IC 95% bootstrap (240 réplicas)</sub>",
                   x=0.5, xanchor="center"),
        barmode="stack", height=280,
        xaxis=dict(range=[0, 105], showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False),
        margin=dict(l=40, r=40, t=100, b=40),
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
    )
    return fig


def fig_bootstrap(boot: pd.DataFrame) -> go.Figure:
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=3,
                         subplot_titles=("Aporte de horas", "Aporte de composición", "No explicado (residual)"))
    for col_idx, (col, color) in enumerate(zip(
        ["aporte_horas", "aporte_composicion", "no_explicado"],
        [COLOR_H, COLOR_CLARO, COLOR_M]), start=1):
        pcts = boot[col] / boot["brecha_log"] * 100
        med, lo, hi = pcts.median(), np.percentile(pcts, 2.5), np.percentile(pcts, 97.5)
        fig.add_trace(go.Histogram(
            x=pcts, marker_color=color, opacity=0.85, nbinsx=25,
            name=f"med={med:.1f}%",
            hovertemplate="% brecha: %{x:.2f}<br>Cuenta: %{y}<extra></extra>",
        ), row=1, col=col_idx)
        fig.add_vline(x=med, line=dict(color="black", width=2), row=1, col=col_idx)
        fig.add_vline(x=lo, line=dict(color="black", dash="dash"), row=1, col=col_idx)
        fig.add_vline(x=hi, line=dict(color="black", dash="dash"), row=1, col=col_idx)
        fig.add_vline(x=0, line=dict(color="red", width=1), row=1, col=col_idx)
        fig.layout.annotations[col_idx-1].update(text=f"{fig.layout.annotations[col_idx-1].text}<br><sub>Mediana: {med:.1f}%  |  IC95: [{lo:.1f}, {hi:.1f}]</sub>")
    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>Distribución bootstrap de los tres componentes</b><br><sub>240 réplicas. La línea roja marca el cero — el aporte de composición lo incluye, las otras dos no.</sub>",
                   x=0.5, xanchor="center"),
        height=400, showlegend=False,
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
    )
    fig.update_xaxes(title="% de la brecha total")
    return fig


def fig_mapa(df: pd.DataFrame, geojson_path: Path) -> go.Figure:
    """Mapa coroplético de México con la brecha mensual por entidad."""
    import json
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    # Datos por entidad
    filas = []
    for ent_id, grp in df.groupby("ent", observed=True):
        hh = grp[grp["mujer"]==0]; mm = grp[grp["mujer"]==1]
        if len(hh) < 30 or len(mm) < 30: continue
        ing_h = media_ponderada(hh["ingreso_mensual_w"], hh["fac_tri"])
        ing_m = media_ponderada(mm["ingreso_mensual_w"], mm["fac_tri"])
        filas.append({"ent": int(ent_id),
                       "entidad": ESTADOS[int(ent_id)],
                       "brecha": (ing_h-ing_m)/ing_h*100})
    df_ent = pd.DataFrame(filas)

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=df_ent["ent"],
        z=df_ent["brecha"],
        featureidkey="properties.state_code",
        colorscale="OrRd",
        marker_line_color="white",
        marker_line_width=0.8,
        colorbar=dict(title="Brecha (%)", thickness=15, len=0.7),
        text=df_ent["entidad"],
        hovertemplate="<b>%{text}</b><br>Brecha mensual: %{z:.1f}%<extra></extra>",
    ))
    fig.update_geos(
        fitbounds="locations", visible=False,
        showcoastlines=False, showland=True, landcolor="#f5f5f5",
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>Brecha mensual de ingreso por entidad federativa</b><br><sub>Zonas más oscuras = mayor brecha. Pasa el cursor para ver el valor por estado.</sub>",
                   x=0.5, xanchor="center"),
        height=550,
        margin=dict(l=0, r=0, t=90, b=0),
        font=dict(family="system-ui, -apple-system, sans-serif", size=12),
    )
    return fig


def fig_entidades(df: pd.DataFrame) -> go.Figure:
    filas = []
    for ent_id, grp in df.groupby("ent", observed=True):
        hh = grp[grp["mujer"]==0]; mm = grp[grp["mujer"]==1]
        if len(hh) < 30 or len(mm) < 30: continue
        ing_h = media_ponderada(hh["ingreso_mensual_w"], hh["fac_tri"])
        ing_m = media_ponderada(mm["ingreso_mensual_w"], mm["fac_tri"])
        filas.append({"entidad": ESTADOS[int(ent_id)],
                       "brecha": (ing_h-ing_m)/ing_h*100})
    df_ent = pd.DataFrame(filas).sort_values("brecha")
    prom = df_ent["brecha"].mean()
    colores = [COLOR_CLARO if v < prom else COLOR_H for v in df_ent["brecha"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_ent["entidad"], x=df_ent["brecha"],
        orientation="h", marker_color=colores,
        text=[f"{v:.1f}%" for v in df_ent["brecha"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Brecha mensual: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=prom, line=dict(color=GRIS, dash="dash"),
                   annotation_text=f"Promedio: {prom:.1f}%",
                   annotation_position="bottom right")
    fig.update_layout(
        template="plotly_white",
        title=dict(text=f"<b>La brecha mensual varía 4× entre entidades</b><br><sub>Chiapas {df_ent.iloc[0]['brecha']:.0f}% (probable sesgo de selección) hasta Hidalgo {df_ent.iloc[-1]['brecha']:.0f}%</sub>",
                   x=0.5, xanchor="center"),
        height=750, xaxis_title="Brecha mensual (%)",
        margin=dict(l=140, r=80, t=90, b=40),
        font=dict(family="system-ui, -apple-system, sans-serif", size=11),
    )
    return fig


def kpi_card(label: str, valor: str, sub: str = "", color: str = COLOR_H) -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-valor" style="color:{color};">{valor}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """


def construir_html(df: pd.DataFrame, boot: pd.DataFrame, geojson_path: Path) -> str:
    kpis = kpi_cards(df)
    figs_html = {
        "caracterizacion": fig_caracterizacion(df).to_html(full_html=False, include_plotlyjs="cdn", div_id="fig-carac"),
        "horas":           fig_horas(df).to_html(full_html=False, include_plotlyjs=False, div_id="fig-horas"),
        "oaxaca":          fig_oaxaca(boot).to_html(full_html=False, include_plotlyjs=False, div_id="fig-oaxaca"),
        "bootstrap":       fig_bootstrap(boot).to_html(full_html=False, include_plotlyjs=False, div_id="fig-boot"),
        "mapa":            fig_mapa(df, geojson_path).to_html(full_html=False, include_plotlyjs=False, div_id="fig-mapa"),
        "entidades":       fig_entidades(df).to_html(full_html=False, include_plotlyjs=False, div_id="fig-ent"),
    }

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>La brecha salarial en México · Dashboard</title>
<style>
  body {{
    font-family: -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
    max-width: 1180px; margin: 0 auto; padding: 32px 24px;
    color: #1a1a1a; line-height: 1.55; background: #fafafa;
  }}
  header {{ text-align: center; margin-bottom: 48px; }}
  header h1 {{
    font-size: 38px; margin: 0 0 8px 0; color: #1a1a1a;
    font-weight: 800; letter-spacing: -0.02em;
  }}
  header h1 em {{ color: #d95f0e; font-style: italic; font-weight: 800; }}
  header p.subtitle {{ font-size: 17px; color: #666; max-width: 760px; margin: 0 auto; }}
  .kpi-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 18px; margin: 36px 0;
  }}
  .kpi-card {{
    background: white; border: 1px solid #e5e5e5; border-radius: 12px;
    padding: 22px 20px; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .kpi-label {{ font-size: 13px; color: #666; text-transform: uppercase;
                letter-spacing: 0.08em; margin-bottom: 8px; }}
  .kpi-valor {{ font-size: 38px; font-weight: 800; line-height: 1; margin: 4px 0; }}
  .kpi-sub {{ font-size: 13px; color: #888; margin-top: 6px; }}
  section {{ background: white; border: 1px solid #e5e5e5; border-radius: 12px;
             padding: 24px; margin-bottom: 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
  section h2 {{ margin: 0 0 4px 0; font-size: 22px; color: #1a1a1a; }}
  section .lede {{ color: #555; font-size: 15px; margin: 0 0 18px 0; }}
  footer {{
    text-align: center; margin-top: 32px; padding-top: 24px;
    border-top: 1px solid #e5e5e5; color: #888; font-size: 13px;
  }}
  footer a {{ color: #2c7fb8; text-decoration: none; }}
  footer a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>

<header>
  <h1>La brecha salarial en México <em>no es lo que crees</em></h1>
  <p class="subtitle">
    De la brecha mensual del 32% entre hombres y mujeres ocupadas, casi la mitad la explican
    las horas trabajadas. La otra mitad no se explica con educación, sector ni geografía.
  </p>
</header>

<div class="kpi-grid">
  {kpi_card("Brecha mensual bruta", f"{kpis['brecha_mensual']:.1f}%", "ENOE 4T 2025", COLOR_M)}
  {kpi_card("Hrs/semana menos en mujeres", f"{kpis['dif_horas']:.1f}", f"H {45.9:.0f}h vs M {37.6:.0f}h", COLOR_H)}
  {kpi_card("Escolaridad promedio", f"M {kpis['escolaridad_m']:.1f} > H {kpis['escolaridad_h']:.1f}", "Años ponderados", COLOR_M)}
  {kpi_card("Observaciones", f"{kpis['n']:,}", f"~33M personas representadas", GRIS)}
</div>

<section>
  <h2>1. El cliché que no funciona</h2>
  <p class="lede">
    La explicación común es "ganan menos porque están menos calificadas o más en la informalidad".
    Los datos no la sostienen — las mujeres ocupadas tienen <strong>más años de escuela</strong> y
    <strong>más presencia en sector formal</strong>. La única variable Mincer donde difieren fuerte
    son las horas. Puedes pasar el cursor para ver los valores exactos.
  </p>
  {figs_html['caracterizacion']}
</section>

<section>
  <h2>2. Donde sí difieren: las horas</h2>
  <p class="lede">
    No es que "todas trabajan menos" — la distribución femenina es bimodal. Una parte iguala a los
    hombres en jornada completa, otra parte amplia se concentra en jornadas parciales que casi no
    existen en hombres. Esa cola izquierda es el peso de la brecha mensual.
  </p>
  {figs_html['horas']}
</section>

<section>
  <h2>3. La descomposición Oaxaca-Blinder</h2>
  <p class="lede">
    Descomponiendo el log de la brecha en componentes vía la versión <em>pooled</em> de Neumark (1988),
    con bootstrap no paramétrico para intervalos de confianza al 95%. La composición observable
    (educación, sector, formalidad, entidad federativa) aporta 0.5% — estadísticamente indistinguible
    de cero.
  </p>
  {figs_html['oaxaca']}
  {figs_html['bootstrap']}
</section>

<section>
  <h2>4. Brecha por entidad federativa</h2>
  <p class="lede">
    La brecha varía 4× entre estados. Chiapas con la brecha más baja es contraintuitivo
    — probablemente refleja sesgo de selección, no menor desigualdad real: en estados con
    baja participación femenina, las mujeres que sí trabajan son una muestra muy seleccionada.
    Hidalgo en cambio aparece con la brecha más alta. El mapa muestra la geografía completa;
    el ranking abajo da los números exactos.
  </p>
  {figs_html['mapa']}
  {figs_html['entidades']}
</section>

<footer>
  Dashboard generado con Plotly · datos ENOE 4T 2025 (INEGI) ·
  <a href="https://github.com/darioomar-blip/brecha-salarial-mexico">Repositorio en GitHub</a> ·
  Análisis cerrado en mayo de 2026
</footer>

</body>
</html>
"""
    return html


def main():
    ROOT = Path(__file__).parent.parent
    df   = pd.read_parquet(ROOT / "data" / "processed" / "enoen_2025_4t_mincer.parquet")
    boot = pd.read_csv(ROOT / "outputs" / "oaxaca_bootstrap.csv")
    geojson_path = ROOT / "data" / "external" / "mexico_states.geojson"

    html = construir_html(df, boot, geojson_path)

    # Genera dos archivos: el index para GitHub Pages y una copia en outputs/
    # para mantener la convención de derivados.
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    (ROOT / "outputs" / "dashboard.html").write_text(html, encoding="utf-8")

    print(f"Dashboard generado:")
    print(f"  {ROOT / 'index.html'}  (raíz, para GitHub Pages)")
    print(f"  {ROOT / 'outputs' / 'dashboard.html'}  (copia en outputs/)")
    print(f"Tamaño: {(ROOT / 'index.html').stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
