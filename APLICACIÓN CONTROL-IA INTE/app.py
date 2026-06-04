import io
import base64
import math
import os
import re
import time as time_module
import unicodedata
from datetime import date, datetime, time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm, shapiro
from supabase import create_client


st.set_page_config(
    page_title="CEP Frutas y Hortalizas",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

MIN_SUBGROUPS = 25
UNIMAG_ESCUDO_URL = "https://cdn.unimagdalena.edu.co/images/escudo/bg_light/384.png"
CHART_COLORS = ["#004A87", "#D17900", "#00A50B", "#0183EF", "#240090", "#D10500"]
INSERT_CHUNK_SIZE = 100


def apply_design():
    st.markdown(
        """
        <style>
        :root {
            --bg: #f6f8fb;
            --panel: #ffffff;
            --ink: #182230;
            --muted: #667085;
            --line: #d7e1ea;
            --brand: #004A87;
            --brand-soft: #e7f2f9;
            --brand-2: #0183EF;
            --leaf: #00A50B;
            --gold: #D17900;
            --bad: #D10500;
        }
        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(1, 131, 239, .10), transparent 30%),
                radial-gradient(circle at 100% 8%, rgba(209, 121, 0, .10), transparent 26%),
                linear-gradient(180deg, #ffffff 0%, var(--bg) 58%, #edf3f8 100%);
            color: var(--ink);
        }
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        section[data-testid="stSidebar"]::before {
            content: "UNIMAGDALENA";
            display: block;
            margin: 1.1rem 1rem .35rem;
            color: var(--brand);
            font-weight: 900;
            letter-spacing: .08em;
            font-size: .78rem;
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--muted);
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label {
            padding: .44rem .55rem;
            border-radius: 8px;
            margin: .12rem 0;
            border: 1px solid transparent;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: var(--brand-soft);
            border-color: #c6dbef;
        }
        div[data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 22px rgba(20, 33, 61, .055);
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: .88rem;
        }
        div[data-testid="stMetricValue"] {
            color: var(--ink);
        }
        .cep-hero {
            background:
                linear-gradient(135deg, #004A87 0%, #0183EF 64%, #D17900 122%);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, .35);
            border-radius: 14px;
            padding: 1.2rem 1.3rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 18px 44px rgba(24, 34, 48, .14);
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: center;
            gap: 1rem;
            position: relative;
            overflow: hidden;
        }
        .cep-hero::after {
            content: "";
            position: absolute;
            right: -40px;
            bottom: -70px;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            background: rgba(255, 255, 255, .12);
            pointer-events: none;
        }
        .cep-hero img {
            width: 72px;
            height: 72px;
            object-fit: contain;
            background: rgba(255,255,255,.92);
            border-radius: 50%;
            padding: .42rem;
            position: relative;
            z-index: 1;
        }
        .cep-hero h1 {
            margin: 0;
            font-size: clamp(1.8rem, 3.2vw, 3rem);
            line-height: 1.03;
            letter-spacing: 0;
            color: #ffffff;
            position: relative;
            z-index: 1;
        }
        .cep-hero p {
            margin: .55rem 0 0;
            color: rgba(255, 255, 255, .86);
            max-width: 880px;
            position: relative;
            z-index: 1;
        }
        .cep-hero-badge {
            background: rgba(255, 255, 255, .94);
            color: var(--brand);
            border: 1px solid rgba(255,255,255,.65);
            border-radius: 999px;
            padding: .35rem .65rem;
            font-size: .82rem;
            font-weight: 800;
            white-space: nowrap;
            position: relative;
            z-index: 1;
        }
        .cep-nav {
            background: rgba(255,255,255,.92);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: .7rem .75rem .55rem;
            margin: -.2rem 0 1rem;
            box-shadow: 0 12px 28px rgba(0,74,135,.075);
        }
        .cep-nav div[data-testid="stPills"] {
            margin-bottom: 0;
        }
        .cep-nav [role="radiogroup"] {
            gap: .45rem;
            flex-wrap: wrap;
        }
        .cep-nav [role="radiogroup"] label {
            background: #ffffff;
            border: 1px solid #d7e1ea;
            border-radius: 999px;
            padding: .42rem .78rem !important;
            box-shadow: 0 3px 10px rgba(0,74,135,.045);
            transition: all .15s ease;
        }
        .cep-nav [role="radiogroup"] label:hover {
            border-color: var(--brand-2);
            background: #eef7ff;
            transform: translateY(-1px);
        }
        .cep-nav button {
            border-radius: 999px !important;
            border-color: #d7e1ea !important;
        }
        .cep-nav button:hover {
            border-color: var(--brand-2) !important;
            background: #eef7ff !important;
        }
        .cep-section {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 1.1rem 0 .65rem;
            border-bottom: 1px solid var(--line);
            padding-bottom: .5rem;
        }
        .cep-section h2 {
            margin: 0;
            font-size: 1.18rem;
            color: var(--ink);
        }
        .cep-section span {
            color: var(--muted);
            font-size: .92rem;
        }
        .cep-note {
            background: #ffffff;
            border: 1px solid var(--line);
            border-left: 5px solid var(--brand);
            border-radius: 8px;
            padding: .85rem 1rem;
            color: #334155;
            box-shadow: 0 10px 24px rgba(15, 23, 42, .05);
        }
        .cep-empty {
            background: #f1f7fd;
            border: 1px solid #c6dbef;
            border-radius: 8px;
            padding: 1rem;
            color: var(--brand);
        }
        .cep-upload-panel {
            background: linear-gradient(135deg, rgba(0,74,135,.08), rgba(209,121,0,.08));
            border: 1px solid #c8dce8;
            border-radius: 12px;
            padding: 1rem;
            margin: .6rem 0 1rem;
        }
        .cep-upload-panel h3 {
            margin: 0 0 .35rem;
            color: var(--brand);
            font-size: 1.05rem;
        }
        .cep-upload-panel p {
            margin: 0;
            color: #334155;
        }
        div[data-testid="stForm"] {
            background: rgba(255,255,255,.82);
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, .05);
        }
        .stButton button, .stDownloadButton button, div[data-testid="stFormSubmitButton"] button {
            border-radius: 8px;
            border: 1px solid var(--brand);
            background: var(--brand);
            color: white;
            font-weight: 700;
        }
        .stButton button:hover, .stDownloadButton button:hover, div[data-testid="stFormSubmitButton"] button:hover {
            background: #003A6B;
            color: white;
            border-color: #003A6B;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }
        @media (max-width: 760px) {
            .cep-hero {
                grid-template-columns: 1fr;
            }
            .cep-hero img {
                width: 58px;
                height: 58px;
            }
            .cep-hero-badge {
                width: fit-content;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=None):
    subtitle_html = f"<span>{subtitle}</span>" if subtitle else ""
    st.markdown(f"<div class='cep-section'><h2>{title}</h2>{subtitle_html}</div>", unsafe_allow_html=True)


def empty_state(text):
    st.markdown(f"<div class='cep-empty'>{text}</div>", unsafe_allow_html=True)


def note(text):
    st.markdown(f"<div class='cep-note'>{text}</div>", unsafe_allow_html=True)


def style_chart(fig, height=430):
    fig.update_layout(
        template="plotly_white",
        colorway=CHART_COLORS,
        height=height,
        hovermode="x unified",
        margin=dict(l=18, r=18, t=58, b=42),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title=dict(font=dict(size=20, color="#172033")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033"),
        xaxis=dict(showgrid=True, gridcolor="#e7eee9", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#e7eee9", zeroline=False),
    )
    return fig


@st.cache_resource
def get_supabase_client():
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
    except Exception:
        url = ""
        key = ""
    url = url or os.getenv("SUPABASE_URL", "")
    key = key or os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        st.error("Configura SUPABASE_URL y SUPABASE_KEY en variables de entorno o .streamlit/secrets.toml.")
        st.stop()
    return create_client(url, key)


sb = get_supabase_client()


def show_missing_table_help(table):
    st.error(f"La app si conecto a Supabase, pero no encontro la tabla '{table}'.")
    st.markdown(
        """
        En este proyecto de Supabase falta ejecutar o refrescar el archivo `schema_supabase.sql`.

        Pasos:
        1. Abre Supabase.
        2. Entra al proyecto conectado por `SUPABASE_URL`.
        3. Ve a `SQL Editor`.
        4. Copia y ejecuta todo el contenido de `schema_supabase.sql`.
        5. Si acabas de crear la tabla y sigue apareciendo este error, ejecuta `NOTIFY pgrst, 'reload schema';`.
        6. Reinicia la app.
        """
    )


def query_table(table, columns="*", order=None):
    q = sb.table(table).select(columns)
    if order:
        q = q.order(order)
    try:
        return q.execute().data or []
    except Exception as exc:
        detail = str(exc)
        if "PGRST205" in detail or "Could not find the table" in detail or "schema cache" in detail:
            show_missing_table_help(table)
        else:
            st.error(f"No se pudo conectar a Supabase para leer la tabla '{table}'.")
            st.markdown(
                """
                Revisa estos puntos antes de la sustentacion:

                1. Que el equipo tenga internet.
                2. Que `SUPABASE_URL` y `SUPABASE_KEY` esten configuradas.
                3. Que el antivirus/firewall no bloquee Python o Streamlit.
                4. Que el SQL de `schema_supabase.sql` ya se haya ejecutado en Supabase.

                Si ves `getaddrinfo fallido`, normalmente es un problema de red/DNS, no de formulas ni de tablas.
                """
            )
        with st.expander("Detalle tecnico"):
            st.code(detail)
        st.stop()


def insert_row(table, payload):
    last_error = None
    for attempt in range(4):
        try:
            return sb.table(table).insert(payload).execute()
        except Exception as exc:
            last_error = exc
            detail = str(exc)
            transient = any(token in detail for token in ["ConnectionTerminated", "RemoteProtocolError", "timeout", "Timeout", "server disconnected"])
            if not transient or attempt == 3:
                break
            time_module.sleep(0.6 * (attempt + 1))
    detail = str(last_error)
    if "PGRST205" in detail or "Could not find the table" in detail or "schema cache" in detail:
        show_missing_table_help(table)
        with st.expander("Detalle tecnico"):
            st.code(detail)
        st.stop()
    st.error(f"No se pudo guardar en la tabla '{table}'.")
    st.markdown("Verifica conexion a internet, credenciales de Supabase y politicas RLS.")
    with st.expander("Detalle tecnico"):
        st.code(detail)
    st.stop()


def insert_rows(table, payloads):
    if not payloads:
        return None
    results = []
    for start in range(0, len(payloads), INSERT_CHUNK_SIZE):
        chunk = payloads[start:start + INSERT_CHUNK_SIZE]
        last_error = None
        for attempt in range(4):
            try:
                result = sb.table(table).insert(chunk).execute()
                if getattr(result, "data", None):
                    results.extend(result.data)
                break
            except Exception as exc:
                last_error = exc
                detail = str(exc)
                transient = any(token in detail for token in ["ConnectionTerminated", "RemoteProtocolError", "timeout", "Timeout", "server disconnected"])
                if not transient or attempt == 3:
                    if "PGRST205" in detail or "Could not find the table" in detail or "schema cache" in detail:
                        show_missing_table_help(table)
                        with st.expander("Detalle tecnico"):
                            st.code(detail)
                        st.stop()
                    st.error(f"No se pudo guardar en la tabla '{table}'.")
                    st.markdown("Verifica conexion a internet, credenciales de Supabase y politicas RLS.")
                    with st.expander("Detalle tecnico"):
                        st.code(str(last_error))
                    st.stop()
                time_module.sleep(0.6 * (attempt + 1))
        time_module.sleep(0.03)
    return results


def to_df(rows):
    return pd.DataFrame(rows) if rows else pd.DataFrame()


@st.cache_data(ttl=30)
def load_productos():
    return to_df(query_table("productos", "*", "nombre"))


@st.cache_data(ttl=30)
def load_variables():
    return to_df(query_table("variables_continuas", "*, productos(nombre,tipo)", "nombre_variable"))


@st.cache_data(ttl=30)
def load_atributos():
    return to_df(query_table("atributos", "*, productos(nombre,tipo)", "nombre_atributo"))


@st.cache_data(ttl=30)
def load_subgrupos():
    return to_df(query_table("subgrupos", "*, productos(nombre,tipo)", "fecha_hora"))


@st.cache_data(ttl=30)
def load_mediciones():
    rows = query_table(
        "mediciones",
        "id, valor, subgrupo_id, variable_id, subgrupos(id, producto_id, fecha_hora, analista, lote, tamano_muestra, productos(nombre,tipo)), variables_continuas(nombre_variable, unidad)",
    )
    return to_df(rows)


@st.cache_data(ttl=30)
def load_inspecciones():
    rows = query_table(
        "inspecciones_atributos",
        "id, conforma, subgrupo_id, atributo_id, subgrupos(id, producto_id, fecha_hora, analista, lote, unidades_inspeccionadas, productos(nombre,tipo)), atributos(nombre_atributo, tipo_inspeccion)",
    )
    return to_df(rows)


@st.cache_data(ttl=30)
def load_datos_importados():
    return to_df(query_table("datos_importados", "*", "created_at"))


def clear_cache():
    st.cache_data.clear()


def nested_value(row, column, key, default=None):
    value = row.get(column)
    if isinstance(value, dict):
        return value.get(key, default)
    return default


def flatten_mediciones(df):
    if df.empty:
        return df
    out = df.copy()
    out["fecha_hora"] = out.apply(lambda r: nested_value(r, "subgrupos", "fecha_hora"), axis=1)
    out["analista"] = out.apply(lambda r: nested_value(r, "subgrupos", "analista"), axis=1)
    out["lote"] = out.apply(lambda r: nested_value(r, "subgrupos", "lote"), axis=1)
    out["tamano_muestra"] = out.apply(lambda r: nested_value(r, "subgrupos", "tamano_muestra", 1), axis=1)
    out["producto_id"] = out.apply(lambda r: nested_value(r, "subgrupos", "producto_id"), axis=1)
    out["producto"] = out["subgrupos"].apply(lambda v: (v or {}).get("productos", {}).get("nombre") if isinstance(v, dict) else None)
    out["nombre_variable"] = out["variables_continuas"].apply(lambda v: (v or {}).get("nombre_variable") if isinstance(v, dict) else None)
    out["unidad"] = out["variables_continuas"].apply(lambda v: (v or {}).get("unidad") if isinstance(v, dict) else None)
    out["fecha_hora"] = pd.to_datetime(out["fecha_hora"], errors="coerce")
    out["valor"] = pd.to_numeric(out["valor"], errors="coerce")
    return out


def flatten_inspecciones(df):
    if df.empty:
        return df
    out = df.copy()
    out["fecha_hora"] = out.apply(lambda r: nested_value(r, "subgrupos", "fecha_hora"), axis=1)
    out["analista"] = out.apply(lambda r: nested_value(r, "subgrupos", "analista"), axis=1)
    out["lote"] = out.apply(lambda r: nested_value(r, "subgrupos", "lote"), axis=1)
    out["unidades_inspeccionadas"] = out.apply(lambda r: nested_value(r, "subgrupos", "unidades_inspeccionadas", 1), axis=1)
    out["producto_id"] = out.apply(lambda r: nested_value(r, "subgrupos", "producto_id"), axis=1)
    out["producto"] = out["subgrupos"].apply(lambda v: (v or {}).get("productos", {}).get("nombre") if isinstance(v, dict) else None)
    out["nombre_atributo"] = out["atributos"].apply(lambda v: (v or {}).get("nombre_atributo") if isinstance(v, dict) else None)
    out["tipo_inspeccion"] = out["atributos"].apply(lambda v: (v or {}).get("tipo_inspeccion") if isinstance(v, dict) else None)
    out["fecha_hora"] = pd.to_datetime(out["fecha_hora"], errors="coerce")
    out["no_conforma"] = ~out["conforma"].astype(bool)
    return out


def product_options(df):
    if df.empty:
        return {}
    return {f"{r['nombre']} ({r['tipo']})": r["id"] for _, r in df.iterrows()}


def variable_options(df, producto_id=None):
    if producto_id and not df.empty:
        df = df[df["producto_id"] == producto_id]
    if df.empty:
        return {}
    return {f"{r['nombre_variable']} [{r['unidad']}]": r["id"] for _, r in df.iterrows()}


def atributo_options(df, producto_id=None):
    if producto_id and not df.empty:
        df = df[df["producto_id"] == producto_id]
    if df.empty:
        return {}
    return {f"{r['nombre_atributo']} ({r['tipo_inspeccion']})": r["id"] for _, r in df.iterrows()}


def chart_with_limits(df, x, y, center, ucl, lcl, title, y_title):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[y],
            mode="lines+markers",
            name=y_title,
            line=dict(color="#004A87", width=3),
            marker=dict(size=8, color="#004A87", line=dict(width=1, color="#ffffff")),
            customdata=df[["fecha_hora"]] if "fecha_hora" in df.columns else None,
            hovertemplate="Subgrupo=%{x}<br>Valor=%{y:.4f}<extra></extra>",
        )
    )
    fig.add_hline(y=center, line_dash="solid", line_color="#00A50B", annotation_text="LC")
    if np.isscalar(ucl):
        fig.add_hline(y=ucl, line_dash="dash", line_color="#D10500", annotation_text="LSC")
    else:
        fig.add_trace(go.Scatter(x=df[x], y=ucl, mode="lines", name="LSC", line=dict(color="#D10500", dash="dash", width=2)))
    if np.isscalar(lcl):
        fig.add_hline(y=lcl, line_dash="dash", line_color="#D10500", annotation_text="LIC")
    else:
        fig.add_trace(go.Scatter(x=df[x], y=lcl, mode="lines", name="LIC", line=dict(color="#D10500", dash="dash", width=2)))
    fig.update_layout(title=title, xaxis_title="Subgrupo", yaxis_title=y_title)
    return style_chart(fig)


def descriptive_stats(values):
    clean = pd.Series(values).dropna().astype(float)
    if clean.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "n": clean.count(),
                "media": clean.mean(),
                "mediana": clean.median(),
                "desv_est": clean.std(ddof=1),
                "min": clean.min(),
                "q1": clean.quantile(0.25),
                "q3": clean.quantile(0.75),
                "max": clean.max(),
            }
        ]
    )


def detect_control_rules(df, y, center, ucl, lcl):
    values = df[y].astype(float).reset_index(drop=True)
    subgroups = df["subgrupo"].reset_index(drop=True)
    if values.empty:
        return pd.DataFrame(columns=["regla", "subgrupo", "detalle"])

    if np.isscalar(ucl):
        sigma = abs(float(ucl) - float(center)) / 3 if ucl != center else values.std(ddof=1)
        ucl_series = pd.Series([ucl] * len(values))
        lcl_series = pd.Series([lcl] * len(values))
    else:
        ucl_series = pd.Series(ucl).reset_index(drop=True).astype(float)
        lcl_series = pd.Series(lcl).reset_index(drop=True).astype(float)
        sigma = ((ucl_series - center).abs() / 3).replace([np.inf, -np.inf], np.nan).median()
    if not sigma or np.isnan(sigma):
        sigma = values.std(ddof=1)
    if not sigma or np.isnan(sigma):
        return pd.DataFrame(columns=["regla", "subgrupo", "detalle"])

    findings = []

    def add(rule, idx, detail):
        findings.append({"regla": rule, "subgrupo": int(subgroups.iloc[idx]), "detalle": detail})

    for i, value in enumerate(values):
        if value > ucl_series.iloc[i] or value < lcl_series.iloc[i]:
            add("Prueba 1", i, "Punto fuera de limites de control de 3 sigma.")

    side = np.sign(values - center)
    for i in range(8, len(values)):
        window = side.iloc[i - 8 : i + 1]
        if (window > 0).all() or (window < 0).all():
            add("Prueba 2", i, "Nueve puntos consecutivos del mismo lado de la linea central.")

    for i in range(5, len(values)):
        window = values.iloc[i - 5 : i + 1]
        if window.is_monotonic_increasing or window.is_monotonic_decreasing:
            add("Prueba 3", i, "Seis puntos consecutivos aumentando o disminuyendo.")

    for i in range(13, len(values)):
        window = side.iloc[i - 13 : i + 1]
        alternating = all(window.iloc[j] * window.iloc[j - 1] < 0 for j in range(1, len(window)))
        if alternating:
            add("Prueba 4", i, "Catorce puntos consecutivos alternando arriba y abajo.")

    for i in range(2, len(values)):
        window = values.iloc[i - 2 : i + 1] - center
        if (window > 2 * sigma).sum() >= 2 or (window < -2 * sigma).sum() >= 2:
            add("Prueba 5", i, "Dos de tres puntos a mas de 2 sigma del mismo lado.")

    for i in range(4, len(values)):
        window = values.iloc[i - 4 : i + 1] - center
        if (window > sigma).sum() >= 4 or (window < -sigma).sum() >= 4:
            add("Prueba 6", i, "Cuatro de cinco puntos a mas de 1 sigma del mismo lado.")

    for i in range(14, len(values)):
        window = (values.iloc[i - 14 : i + 1] - center).abs()
        if (window < sigma).all():
            add("Prueba 7", i, "Quince puntos consecutivos dentro de 1 sigma.")

    for i in range(7, len(values)):
        window = (values.iloc[i - 7 : i + 1] - center).abs()
        if (window > sigma).all():
            add("Prueba 8", i, "Ocho puntos consecutivos fuera de 1 sigma.")

    return pd.DataFrame(findings).drop_duplicates() if findings else pd.DataFrame(columns=["regla", "subgrupo", "detalle"])


def show_control_decision(violations):
    if violations.empty:
        st.success("Proceso sin alarmas segun las 8 pruebas basicas de graficos de control.")
    else:
        st.error("Proceso con senales de causa especial. Revisar lote, analista, fecha y condiciones del proceso.")
        st.dataframe(violations, width="stretch")


def subgroup_stats(df):
    stats = (
        df.groupby("subgrupo_id", as_index=False)
        .agg(
            fecha_hora=("fecha_hora", "min"),
            media=("valor", "mean"),
            rango=("valor", lambda x: x.max() - x.min()),
            s=("valor", "std"),
            n=("valor", "count"),
        )
        .sort_values("fecha_hora")
    )
    stats["subgrupo"] = np.arange(1, len(stats) + 1)
    stats["s"] = stats["s"].fillna(0)
    return stats


def xbar_r_limits(stats):
    xbarbar = stats["media"].mean()
    rbar = stats["rango"].mean()
    n = int(round(stats["n"].median()))
    factors = {
        2: (1.880, 0.000, 3.267),
        3: (1.023, 0.000, 2.574),
        4: (0.729, 0.000, 2.282),
        5: (0.577, 0.000, 2.114),
        6: (0.483, 0.000, 2.004),
        7: (0.419, 0.076, 1.924),
        8: (0.373, 0.136, 1.864),
        9: (0.337, 0.184, 1.816),
        10: (0.308, 0.223, 1.777),
        11: (0.285, 0.256, 1.744),
        12: (0.266, 0.283, 1.717),
        13: (0.249, 0.307, 1.693),
        14: (0.235, 0.328, 1.672),
        15: (0.223, 0.347, 1.653),
        16: (0.212, 0.363, 1.637),
        17: (0.203, 0.378, 1.622),
        18: (0.194, 0.391, 1.608),
        19: (0.187, 0.403, 1.597),
        20: (0.180, 0.415, 1.585),
        21: (0.173, 0.425, 1.575),
        22: (0.167, 0.434, 1.566),
        23: (0.162, 0.443, 1.557),
        24: (0.157, 0.451, 1.548),
        25: (0.153, 0.459, 1.541),
    }
    a2, d3, d4 = factors.get(n, (3 / np.sqrt(max(n, 1)), 0, 2.0))
    return {
        "x_center": xbarbar,
        "x_ucl": xbarbar + a2 * rbar,
        "x_lcl": xbarbar - a2 * rbar,
        "r_center": rbar,
        "r_ucl": d4 * rbar,
        "r_lcl": max(0, d3 * rbar),
        "n": n,
    }


def xbar_s_limits(stats):
    xbarbar = stats["media"].mean()
    sbar = stats["s"].mean()
    n = int(round(stats["n"].median()))
    c4 = np.sqrt(2 / (n - 1)) * math.gamma(n / 2) / math.gamma((n - 1) / 2) if n > 1 else 1
    a3 = 3 / (c4 * np.sqrt(n)) if n > 1 else 0
    b3 = max(0, 1 - (3 * np.sqrt(max(0, 1 - c4**2)) / c4)) if c4 else 0
    b4 = 1 + (3 * np.sqrt(max(0, 1 - c4**2)) / c4) if c4 else 0
    return {
        "x_center": xbarbar,
        "x_ucl": xbarbar + a3 * sbar,
        "x_lcl": xbarbar - a3 * sbar,
        "s_center": sbar,
        "s_ucl": b4 * sbar,
        "s_lcl": b3 * sbar,
        "n": n,
    }


def attribute_stats(df):
    stats = (
        df.groupby("subgrupo_id", as_index=False)
        .agg(
            fecha_hora=("fecha_hora", "min"),
            defectos=("no_conforma", "sum"),
            inspeccionados=("conforma", "count"),
            unidades_inspeccionadas=("unidades_inspeccionadas", "max"),
        )
        .sort_values("fecha_hora")
    )
    stats["subgrupo"] = np.arange(1, len(stats) + 1)
    stats["p"] = stats["defectos"] / stats["inspeccionados"].replace(0, np.nan)
    stats["u"] = stats["defectos"] / stats["unidades_inspeccionadas"].replace(0, np.nan)
    return stats


def normality_card(values):
    clean = pd.Series(values).dropna()
    if len(clean) < 3:
        st.info("Se requieren al menos 3 datos para Shapiro-Wilk.")
        return
    if len(clean) > 5000:
        clean = clean.sample(5000, random_state=42)
    stat, p_value = shapiro(clean)
    verdict = "Compatible con normalidad" if p_value >= 0.05 else "No normal al 5%"
    c1, c2, c3 = st.columns(3)
    c1.metric("Shapiro-Wilk W", f"{stat:.4f}")
    c2.metric("p-valor", f"{p_value:.4f}")
    c3.metric("Decision", verdict)
    st.caption("Criterio: p >= 0.05 sugiere normalidad; p < 0.05 sugiere desviacion de normalidad.")


def capability(values, lsl, usl):
    x = pd.Series(values).dropna().astype(float)
    if len(x) < 2:
        return None
    mean = x.mean()
    sigma_within = x.diff().abs().mean() / 1.128 if len(x) > 2 else x.std(ddof=1)
    sigma_overall = x.std(ddof=1)
    cp = (usl - lsl) / (6 * sigma_within) if sigma_within > 0 else np.nan
    cpk = min((usl - mean) / (3 * sigma_within), (mean - lsl) / (3 * sigma_within)) if sigma_within > 0 else np.nan
    pp = (usl - lsl) / (6 * sigma_overall) if sigma_overall > 0 else np.nan
    ppk = min((usl - mean) / (3 * sigma_overall), (mean - lsl) / (3 * sigma_overall)) if sigma_overall > 0 else np.nan
    return {"Media": mean, "Sigma dentro": sigma_within, "Sigma total": sigma_overall, "Cp": cp, "Cpk": cpk, "Pp": pp, "Ppk": ppk}


def process_capability_from_subgroups(df, lsl, usl):
    clean = df.dropna(subset=["valor"]).copy()
    if len(clean) < 2:
        return None
    mean = clean["valor"].mean()
    sigma_overall = clean["valor"].std(ddof=1)
    grouped = clean.groupby("subgrupo_id")["valor"]
    subgroup_sizes = grouped.count()
    subgroup_std = grouped.std(ddof=1).dropna()
    if len(subgroup_std) and (subgroup_sizes > 1).any():
        numerator = 0.0
        denominator = 0
        for subgroup_id, sigma in subgroup_std.items():
            n_i = int(subgroup_sizes.loc[subgroup_id])
            numerator += (n_i - 1) * (sigma**2)
            denominator += n_i - 1
        sigma_within = math.sqrt(numerator / denominator) if denominator > 0 else np.nan
        sigma_method = "Desviacion estandar agrupada por subgrupos"
    else:
        ordered = clean.sort_values("fecha_hora")["valor"]
        sigma_within = ordered.diff().abs().mean() / 1.128 if len(ordered) > 2 else sigma_overall
        sigma_method = "Rango movil promedio"

    cp = (usl - lsl) / (6 * sigma_within) if sigma_within and sigma_within > 0 else np.nan
    cpk = min((usl - mean) / (3 * sigma_within), (mean - lsl) / (3 * sigma_within)) if sigma_within and sigma_within > 0 else np.nan
    pp = (usl - lsl) / (6 * sigma_overall) if sigma_overall and sigma_overall > 0 else np.nan
    ppk = min((usl - mean) / (3 * sigma_overall), (mean - lsl) / (3 * sigma_overall)) if sigma_overall and sigma_overall > 0 else np.nan
    return {
        "Media": mean,
        "Sigma dentro": sigma_within,
        "Sigma total": sigma_overall,
        "Metodo sigma dentro": sigma_method,
        "Cp": cp,
        "Cpk": cpk,
        "Pp": pp,
        "Ppk": ppk,
    }


def capability_label(value):
    if pd.isna(value):
        return "Sin calculo"
    if value >= 2:
        return "Seis Sigma"
    if value >= 1.33:
        return "Satisfactorio"
    if value >= 1:
        return "Aceptable con mejora"
    if value >= 0.67:
        return "Deficiente"
    return "No apropiado para continuar sin ajustes"


def capability_gauge(value, title):
    safe_value = 0 if pd.isna(value) else float(max(0, min(value, 2.2)))
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=safe_value,
            title={"text": title},
            gauge={
                "axis": {"range": [0, 2.2]},
                "bar": {"color": "#2563eb"},
                "steps": [
                    {"range": [0, 0.67], "color": "#fee2e2"},
                    {"range": [0.67, 1.0], "color": "#ffedd5"},
                    {"range": [1.0, 1.33], "color": "#fef3c7"},
                    {"range": [1.33, 2.2], "color": "#dcfce7"},
                ],
                "threshold": {"line": {"color": "#172033", "width": 3}, "thickness": 0.75, "value": 1.33},
            },
            number={"valueformat": ".3f"},
        )
    )
    return style_chart(fig, height=260)


def attribute_capability(df, subgroup_limit=None):
    if subgroup_limit:
        ordered = attribute_stats(df).tail(int(subgroup_limit))
        ids = ordered["subgrupo_id"].tolist()
        df = df[df["subgrupo_id"].isin(ids)]
    units = len(df)
    defects = int(df["no_conforma"].sum())
    opportunities = max(units, 1)
    dpmo = defects / opportunities * 1_000_000
    yield_rate = max(min(1 - defects / opportunities, 0.999999999), 0.000000001)
    z_value = norm.ppf(yield_rate)
    return {
        "unidades": units,
        "defectos": defects,
        "rendimiento": yield_rate,
        "DPMO": dpmo,
        "nivel_z": z_value,
    }


def build_ai_context():
    context = {
        "productos": len(productos),
        "variables_continuas": len(variables),
        "atributos": len(atributos),
        "subgrupos": len(load_subgrupos()),
        "mediciones": len(mediciones),
        "inspecciones": len(inspecciones),
    }
    if not mediciones.empty:
        var_summary = (
            mediciones.groupby(["producto", "nombre_variable"], dropna=False)
            .agg(
                subgrupos=("subgrupo_id", "nunique"),
                n=("valor", "count"),
                media=("valor", "mean"),
                desv_est=("valor", "std"),
                min=("valor", "min"),
                max=("valor", "max"),
            )
            .reset_index()
            .round(4)
        )
        context["variables"] = var_summary.to_dict(orient="records")
    if not inspecciones.empty:
        attr_summary = (
            inspecciones.groupby(["producto", "nombre_atributo", "tipo_inspeccion"], dropna=False)
            .agg(
                subgrupos=("subgrupo_id", "nunique"),
                inspecciones=("conforma", "count"),
                no_conformes=("no_conforma", "sum"),
            )
            .reset_index()
        )
        attr_summary["porcentaje_no_conforme"] = (
            attr_summary["no_conformes"] / attr_summary["inspecciones"].replace(0, np.nan) * 100
        ).round(3)
        context["atributos_resumen"] = attr_summary.to_dict(orient="records")
    return context


def generate_ai_report(provider, api_key, model, context, question, base_url=None):
    try:
        from openai import OpenAI
    except ImportError:
        st.error("Instala la dependencia de IA con: pip install -r requirements.txt")
        st.stop()
    prompt = f"""
Eres asesor de Control Estadistico de Procesos para frutas y hortalizas.
Usa solo el resumen entregado; no inventes datos. Redacta en espanol claro.

Resumen de la app:
{context}

Pregunta o enfoque del usuario:
{question}

Entrega:
1. Diagnostico breve.
2. Hallazgos por variables y atributos.
3. Riesgos o datos faltantes.
4. Recomendaciones accionables.
5. Texto corto para informe tecnico academico.
"""
    if provider == "OpenAI":
        client = OpenAI(api_key=api_key)
        response = client.responses.create(model=model, input=prompt)
        return response.output_text
    if provider == "Gemini":
        try:
            from google import genai
        except ImportError:
            st.error("Instala Gemini con: pip install -r requirements.txt")
            st.stop()
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or "Gemini no devolvio texto."
    if provider == "OpenRouter / compatible":
        client = OpenAI(api_key=api_key, base_url=base_url or "https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Eres asesor de Control Estadistico de Procesos."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or "El proveedor no devolvio texto."
    raise ValueError("Proveedor IA no soportado.")


def friendly_ai_error(exc):
    text = str(exc)
    if "insufficient_quota" in text or "quota" in text.lower():
        return "La clave funciona, pero la cuenta no tiene cuota o facturacion disponible. Activa creditos/facturacion o usa Gemini/OpenRouter."
    if "invalid_api_key" in text or "api key" in text.lower() or "401" in text:
        return "La API key no es valida o fue revocada. Crea una nueva y pegala de nuevo."
    if "429" in text:
        return "El proveedor esta limitando solicitudes. Espera un momento o usa otro proveedor."
    return "No se pudo generar el informe. Revisa la clave, el modelo y la conexion."


def excel_bytes(frames):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, df in frames.items():
            clean = df.copy()
            for col in clean.columns:
                if clean[col].apply(lambda v: isinstance(v, (dict, list))).any():
                    clean[col] = clean[col].astype(str)
                if pd.api.types.is_datetime64_any_dtype(clean[col]):
                    try:
                        clean[col] = clean[col].dt.tz_localize(None)
                    except TypeError:
                        pass
            clean.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()


def seed_demo_dataset():
    existing = load_productos()
    if not existing.empty and (existing["nombre"] == "Mango Demo CEP").any():
        st.warning("El producto 'Mango Demo CEP' ya existe. Usa esos datos o cambia el nombre antes de volver a cargar demo.")
        return

    rng = np.random.default_rng(42)
    producto = insert_row("productos", {"nombre": "Mango Demo CEP", "tipo": "Fruta"}).data[0]
    variables_demo = insert_rows(
        "variables_continuas",
        [
            {"producto_id": producto["id"], "nombre_variable": "Peso", "unidad": "g"},
            {"producto_id": producto["id"], "nombre_variable": "pH", "unidad": "pH"},
        ],
    ).data
    atributos_demo = insert_rows(
        "atributos",
        [
            {"producto_id": producto["id"], "nombre_atributo": "Manchas", "tipo_inspeccion": "p"},
            {"producto_id": producto["id"], "nombre_atributo": "Golpes", "tipo_inspeccion": "u"},
        ],
    ).data

    start = datetime(2026, 5, 1, 8, 0)
    for i in range(25):
        subgrupo = insert_row(
            "subgrupos",
            {
                "producto_id": producto["id"],
                "fecha_hora": (start + pd.Timedelta(hours=i)).isoformat(),
                "analista": "Analista Demo",
                "lote": f"L-CEP-{i + 1:03d}",
                "tamano_muestra": 5,
                "unidades_inspeccionadas": 30,
            },
        ).data[0]
        peso_center = 420 + 0.18 * i
        ph_center = 4.15 + 0.004 * math.sin(i / 3)
        mediciones_demo = []
        for value in rng.normal(peso_center, 4.8, 5):
            mediciones_demo.append({"subgrupo_id": subgrupo["id"], "variable_id": variables_demo[0]["id"], "valor": round(float(value), 3)})
        for value in rng.normal(ph_center, 0.035, 5):
            mediciones_demo.append({"subgrupo_id": subgrupo["id"], "variable_id": variables_demo[1]["id"], "valor": round(float(value), 4)})
        insert_rows("mediciones", mediciones_demo)

        defectos_manchas = int(rng.binomial(30, 0.08))
        defectos_golpes = int(rng.binomial(30, 0.05))
        inspecciones_demo = []
        inspecciones_demo.extend(
            {"subgrupo_id": subgrupo["id"], "atributo_id": atributos_demo[0]["id"], "conforma": idx >= defectos_manchas}
            for idx in range(30)
        )
        inspecciones_demo.extend(
            {"subgrupo_id": subgrupo["id"], "atributo_id": atributos_demo[1]["id"], "conforma": idx >= defectos_golpes}
            for idx in range(30)
        )
        insert_rows("inspecciones_atributos", list(inspecciones_demo))

    clear_cache()
    st.success("Datos demo cargados: 25 subgrupos continuos y 25 subgrupos por atributos.")


def append_cached_row(df, row):
    if not row:
        return df
    if not df.empty and "id" in df.columns and row.get("id") in set(df["id"]):
        return df
    return pd.concat([df, pd.DataFrame([row])], ignore_index=True)


def stop_insert_error(table, exc):
    st.error(f"No se pudo guardar en la tabla '{table}'.")
    st.markdown("Verifica conexion a internet, credenciales de Supabase y politicas RLS.")
    with st.expander("Detalle tecnico"):
        st.code(str(exc))
    st.stop()


def ensure_producto(nombre, tipo, productos_df):
    nombre = clean_text_value(nombre, "Producto importado")
    tipo = str(tipo).strip() if str(tipo).strip() in ["Fruta", "Hortaliza", "Otro"] else "Otro"
    match = productos_df[
        productos_df["nombre"].fillna("").astype(str).str.casefold() == nombre.casefold()
    ] if not productos_df.empty and "nombre" in productos_df.columns else pd.DataFrame()
    if not match.empty:
        return match.iloc[0]["id"], productos_df

    existing = sb.table("productos").select("*").eq("nombre", nombre).limit(1).execute().data or []
    if existing:
        row = existing[0]
        productos_df = append_cached_row(productos_df, row)
        return row["id"], productos_df

    try:
        row = sb.table("productos").insert({"nombre": nombre, "tipo": tipo}).execute().data[0]
    except Exception as exc:
        detail = str(exc)
        if "23505" in detail or "duplicate key" in detail:
            existing = sb.table("productos").select("*").eq("nombre", nombre).limit(1).execute().data or []
            if existing:
                row = existing[0]
                productos_df = append_cached_row(productos_df, row)
                return row["id"], productos_df
        stop_insert_error("productos", exc)
    productos_df = append_cached_row(productos_df, row)
    return row["id"], productos_df


def ensure_variable(producto_id, nombre_variable, unidad, variables_df):
    nombre_variable = clean_text_value(nombre_variable, "Variable importada")
    unidad = clean_text_value(unidad, "Sin unidad")
    match = variables_df[
        (variables_df["producto_id"] == producto_id)
        & (variables_df["nombre_variable"].fillna("").astype(str).str.casefold() == nombre_variable.casefold())
    ] if not variables_df.empty and {"producto_id", "nombre_variable"}.issubset(variables_df.columns) else pd.DataFrame()
    if not match.empty:
        return match.iloc[0]["id"], variables_df

    existing = (
        sb.table("variables_continuas")
        .select("*")
        .eq("producto_id", producto_id)
        .eq("nombre_variable", nombre_variable)
        .limit(1)
        .execute()
        .data
        or []
    )
    if existing:
        row = existing[0]
        variables_df = append_cached_row(variables_df, row)
        return row["id"], variables_df

    try:
        row = (
            sb.table("variables_continuas")
            .insert({"producto_id": producto_id, "nombre_variable": nombre_variable, "unidad": unidad})
            .execute()
            .data[0]
        )
    except Exception as exc:
        detail = str(exc)
        if "23505" in detail or "duplicate key" in detail:
            existing = (
                sb.table("variables_continuas")
                .select("*")
                .eq("producto_id", producto_id)
                .eq("nombre_variable", nombre_variable)
                .limit(1)
                .execute()
                .data
                or []
            )
            if existing:
                row = existing[0]
                variables_df = append_cached_row(variables_df, row)
                return row["id"], variables_df
        stop_insert_error("variables_continuas", exc)
    variables_df = append_cached_row(variables_df, row)
    return row["id"], variables_df


def ensure_atributo(producto_id, nombre_atributo, tipo_inspeccion, atributos_df):
    nombre_atributo = clean_text_value(nombre_atributo, "Atributo importado")
    tipo_inspeccion = str(tipo_inspeccion).strip().lower()
    tipo_inspeccion = tipo_inspeccion if tipo_inspeccion in ["p", "np", "c", "u"] else "p"
    match = atributos_df[
        (atributos_df["producto_id"] == producto_id)
        & (atributos_df["nombre_atributo"].fillna("").astype(str).str.casefold() == nombre_atributo.casefold())
    ] if not atributos_df.empty and {"producto_id", "nombre_atributo"}.issubset(atributos_df.columns) else pd.DataFrame()
    if not match.empty:
        return match.iloc[0]["id"], atributos_df

    existing = (
        sb.table("atributos")
        .select("*")
        .eq("producto_id", producto_id)
        .eq("nombre_atributo", nombre_atributo)
        .limit(1)
        .execute()
        .data
        or []
    )
    if existing:
        row = existing[0]
        atributos_df = append_cached_row(atributos_df, row)
        return row["id"], atributos_df

    try:
        row = (
            sb.table("atributos")
            .insert({"producto_id": producto_id, "nombre_atributo": nombre_atributo, "tipo_inspeccion": tipo_inspeccion})
            .execute()
            .data[0]
        )
    except Exception as exc:
        detail = str(exc)
        if "23505" in detail or "duplicate key" in detail:
            existing = (
                sb.table("atributos")
                .select("*")
                .eq("producto_id", producto_id)
                .eq("nombre_atributo", nombre_atributo)
                .limit(1)
                .execute()
                .data
                or []
            )
            if existing:
                row = existing[0]
                atributos_df = append_cached_row(atributos_df, row)
                return row["id"], atributos_df
        stop_insert_error("atributos", exc)
    atributos_df = append_cached_row(atributos_df, row)
    return row["id"], atributos_df


COLUMN_ALIASES = {
    "fecha": "fecha_hora",
    "fecha_y_hora": "fecha_hora",
    "fechahora": "fecha_hora",
    "encargado": "analista",
    "responsable": "analista",
    "producto_nombre": "producto",
    "nombre_producto": "producto",
    "cultivo": "producto",
    "muestra": "subgrupo",
    "numero_muestra": "subgrupo",
    "no_muestra": "subgrupo",
    "no_cliente": "subgrupo",
    "cliente": "subgrupo",
}


def normalize_column_name(column):
    name = unicodedata.normalize("NFKD", str(column).strip().lower())
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "columna"


def normalize_columns(df):
    out = df.copy()
    seen = {}
    columns = []
    for column in out.columns:
        name = normalize_column_name(column)
        count = seen.get(name, 0)
        seen[name] = count + 1
        columns.append(name if count == 0 else f"{name}_{count + 1}")
    out.columns = columns
    rename_map = {
        source: target
        for source, target in COLUMN_ALIASES.items()
        if source in out.columns and target not in out.columns
    }
    if rename_map:
        out = out.rename(columns=rename_map)
    return out


def is_blank_value(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except TypeError:
        return False
    return str(value).strip() == ""


def clean_text_value(value, default):
    return default if is_blank_value(value) else str(value).strip()


def clean_datetime_value(value, default_iso):
    if is_blank_value(value):
        return default_iso
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return default_iso
    return parsed.isoformat()


def to_numeric_flexible(values):
    parsed = pd.to_numeric(values, errors="coerce")
    if isinstance(values, pd.Series):
        decimal_comma = pd.to_numeric(values.astype(str).str.replace(",", ".", regex=False), errors="coerce")
        return parsed.fillna(decimal_comma)
    if pd.isna(parsed) and not is_blank_value(values):
        return pd.to_numeric(str(values).replace(",", "."), errors="coerce")
    return parsed


def required_bulk_columns(mode):
    return (
        {"subgrupo", "producto", "variable", "valor"}
        if mode == "Continuos"
        else {"subgrupo", "producto", "atributo", "unidades_inspeccionadas", "no_conformes"}
    )


def add_default_columns(out, defaults):
    for column, default in defaults.items():
        if column not in out.columns:
            out[column] = default
        elif column == "fecha_hora":
            out[column] = out[column].apply(lambda value: clean_datetime_value(value, default))
        else:
            out[column] = out[column].apply(lambda value: clean_text_value(value, default))
    return out


def add_required_defaults(out, mode):
    if "producto" not in out.columns:
        out["producto"] = "Producto importado"
    else:
        out["producto"] = out["producto"].apply(lambda value: clean_text_value(value, "Producto importado"))

    if "subgrupo" not in out.columns:
        out["subgrupo"] = range(1, len(out) + 1)
    else:
        fallback = pd.Series(range(1, len(out) + 1), index=out.index)
        parsed = pd.to_numeric(out["subgrupo"], errors="coerce")
        out["subgrupo"] = parsed.where(parsed.notna(), fallback).astype(int)

    if mode == "Continuos":
        if "variable" in out.columns:
            out["variable"] = out["variable"].apply(lambda value: clean_text_value(value, "Variable importada"))
    else:
        if "atributo" not in out.columns:
            out["atributo"] = "Atributo importado"
        else:
            out["atributo"] = out["atributo"].apply(lambda value: clean_text_value(value, "Atributo importado"))
        if "unidades_inspeccionadas" not in out.columns:
            out["unidades_inspeccionadas"] = 1
        if "no_conformes" not in out.columns:
            out["no_conformes"] = 0
    return out


def continuous_measurement_columns(out):
    metadata = {
        "subgrupo",
        "producto",
        "tipo_producto",
        "variable",
        "unidad",
        "fecha_hora",
        "analista",
        "lote",
        "valor",
        "id",
        "codigo",
        "codigo_producto",
        "observacion",
        "observaciones",
    }
    numeric_columns = []
    for column in out.columns:
        if column in metadata:
            continue
        values = to_numeric_flexible(out[column])
        if values.notna().any():
            numeric_columns.append(column)
    return numeric_columns


def prepare_continuous_data(out):
    out = add_required_defaults(out, "Continuos")
    if {"variable", "valor"}.issubset(out.columns):
        out["valor"] = to_numeric_flexible(out["valor"])
        return out

    value_columns = continuous_measurement_columns(out)
    if not value_columns:
        out["variable"] = "Variable importada"
        out["valor"] = np.nan
        return out

    id_columns = [
        column
        for column in ["subgrupo", "producto", "tipo_producto", "fecha_hora", "analista", "lote", "unidad"]
        if column in out.columns
    ]
    melted = out.melt(
        id_vars=id_columns,
        value_vars=value_columns,
        var_name="variable",
        value_name="valor",
    )
    melted["valor"] = to_numeric_flexible(melted["valor"])
    melted = melted.dropna(subset=["valor"])
    melted["unidad"] = melted["unidad"] if "unidad" in melted.columns else "Sin unidad"
    return melted


def prepare_bulk_data(df, mode):
    out = normalize_columns(df)
    default_datetime = datetime.now().replace(microsecond=0).isoformat()
    defaults = {
        "tipo_producto": "Otro",
        "fecha_hora": default_datetime,
        "analista": "Sin registrar",
        "lote": "Sin lote",
    }
    if mode == "Continuos":
        defaults["unidad"] = "Sin unidad"
    else:
        defaults["tipo_inspeccion"] = "p"

    out = add_default_columns(out, defaults)
    if mode == "Continuos":
        out = prepare_continuous_data(out)
    else:
        out = add_required_defaults(out, mode)
    return out


def read_csv_flexible(file_obj, sep=None):
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error = None
    for encoding in encodings:
        try:
            file_obj.seek(0)
            return pd.read_csv(file_obj, sep=sep, engine="python", encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.ParserError as exc:
            last_error = exc
    raise last_error


def parse_data_input(uploaded_file, pasted_text, sheet_name=None):
    if uploaded_file is not None:
        uploaded_file.seek(0)
        name = uploaded_file.name.lower()
        try:
            if name.endswith(".csv"):
                return normalize_columns(read_csv_flexible(uploaded_file, sep=None))
            if name.endswith(".tsv") or name.endswith(".txt"):
                return normalize_columns(read_csv_flexible(uploaded_file, sep="\t"))
            if name.endswith(".xlsx") or name.endswith(".xls"):
                return normalize_columns(pd.read_excel(uploaded_file, sheet_name=sheet_name or 0))
            if name.endswith(".json"):
                return normalize_columns(pd.read_json(uploaded_file))
            st.error("Formato no soportado. Usa CSV, TSV, XLSX, XLS o JSON tabular.")
        except Exception as exc:
            st.error("No se pudo leer el archivo. Revisa que sea una tabla valida de Excel, CSV, TSV o JSON.")
            with st.expander("Detalle tecnico"):
                st.code(str(exc))
        return pd.DataFrame()
    if pasted_text and pasted_text.strip():
        try:
            return normalize_columns(pd.read_csv(io.StringIO(pasted_text.strip()), sep=None, engine="python"))
        except Exception as exc:
            st.error("No se pudo leer el CSV pegado.")
            with st.expander("Detalle tecnico"):
                st.code(str(exc))
    return pd.DataFrame()


def json_safe_value(value):
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime, date, time)):
        return value.isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, dict):
        return {str(k): json_safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe_value(v) for v in value]
    return value


def dataframe_to_json_records(df):
    records = df.to_dict(orient="records")
    return [
        {str(column): json_safe_value(value) for column, value in row.items()}
        for row in records
    ]


def save_raw_import(df, upload_mode, source_name, sheet_name=None):
    payload = {
        "nombre_archivo": source_name or "CSV pegado",
        "hoja": sheet_name if sheet_name else None,
        "tipo_carga": upload_mode,
        "filas": int(len(df)),
        "columnas": [str(column) for column in df.columns],
        "datos": dataframe_to_json_records(df),
    }
    insert_row("datos_importados", payload)
    clear_cache()
    st.success(f"Importacion guardada en Supabase: {len(df)} filas y {len(df.columns)} columnas reales.")


def template_continuous_df():
    return pd.DataFrame(
        [
            {
                "subgrupo": 1,
                "producto": "Mango Tommy",
                "tipo_producto": "Fruta",
                "variable": "Peso",
                "unidad": "g",
                "fecha_hora": "2026-05-19 08:00",
                "analista": "Ana",
                "lote": "L-001",
                "valor": 421.4,
            },
            {
                "subgrupo": 1,
                "producto": "Mango Tommy",
                "tipo_producto": "Fruta",
                "variable": "Peso",
                "unidad": "g",
                "fecha_hora": "2026-05-19 08:00",
                "analista": "Ana",
                "lote": "L-001",
                "valor": 419.8,
            },
            {
                "subgrupo": 2,
                "producto": "Mango Tommy",
                "tipo_producto": "Fruta",
                "variable": "Peso",
                "unidad": "g",
                "fecha_hora": "2026-05-19 09:00",
                "analista": "Ana",
                "lote": "L-002",
                "valor": 420.6,
            },
        ]
    )


def template_attributes_df():
    return pd.DataFrame(
        [
            {
                "subgrupo": 1,
                "producto": "Mango Tommy",
                "tipo_producto": "Fruta",
                "atributo": "Manchas",
                "tipo_inspeccion": "p",
                "fecha_hora": "2026-05-19 08:00",
                "analista": "Ana",
                "lote": "L-001",
                "unidades_inspeccionadas": 30,
                "no_conformes": 3,
            },
            {
                "subgrupo": 2,
                "producto": "Mango Tommy",
                "tipo_producto": "Fruta",
                "atributo": "Manchas",
                "tipo_inspeccion": "p",
                "fecha_hora": "2026-05-19 09:00",
                "analista": "Ana",
                "lote": "L-002",
                "unidades_inspeccionadas": 30,
                "no_conformes": 1,
            },
        ]
    )


def file_bytes_for_df(df, kind):
    output = io.BytesIO()
    if kind == "xlsx":
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="datos", index=False)
        return output.getvalue()
    return df.to_csv(index=False).encode("utf-8")


def validate_bulk_data(df, mode):
    prepared = prepare_bulk_data(df, mode)
    missing = required_bulk_columns(mode) - set(prepared.columns)
    if missing:
        return False, f"Faltan columnas: {', '.join(sorted(missing))}"
    if prepared.empty:
        return False, "El archivo no tiene filas."
    return True, "Archivo listo para cargar. Fecha, analista/encargado y lote son opcionales."


def human_size(size_bytes):
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024


def save_support_file(uploaded_file, responsable, descripcion):
    data = uploaded_file.getvalue()
    max_size = 8 * 1024 * 1024
    if len(data) > max_size:
        st.warning(f"{uploaded_file.name}: supera 8 MB. Para la sustentacion, sube archivos mas pequenos o usa Drive/OneDrive.")
        return False
    payload = {
        "nombre_archivo": uploaded_file.name,
        "mime_type": uploaded_file.type or "application/octet-stream",
        "tamano_bytes": len(data),
        "responsable": responsable.strip() or "Sin registrar",
        "descripcion": descripcion.strip(),
        "contenido_base64": base64.b64encode(data).decode("ascii"),
    }
    insert_row("archivos_soporte", payload)
    return True


def bulk_load_continuous(df):
    df = prepare_bulk_data(df, "Continuos")
    missing = required_bulk_columns("Continuos") - set(df.columns)
    if missing:
        st.error(f"Faltan columnas: {', '.join(sorted(missing))}")
        return
    productos_df = load_productos().copy()
    variables_df = load_variables().copy()
    created_subgroups = 0
    created_values = 0
    group_cols = ["subgrupo", "producto", "tipo_producto", "fecha_hora", "analista", "lote"]
    for keys, group in df.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, keys))
        producto_id, productos_df = ensure_producto(record["producto"], record["tipo_producto"], productos_df)
        measurement_rows = []
        variable_sizes = []
        for variable_keys, variable_group in group.groupby(["variable", "unidad"], dropna=False):
            variable_name, unit = variable_keys
            variable_id, variables_df = ensure_variable(producto_id, variable_name, unit, variables_df)
            values = to_numeric_flexible(variable_group["valor"]).dropna().tolist()
            if not values:
                continue
            variable_sizes.append(len(values))
            measurement_rows.extend(
                {"variable_id": variable_id, "valor": float(value)}
                for value in values
            )
        if not measurement_rows:
            continue
        subgrupo = insert_row(
            "subgrupos",
            {
                "producto_id": producto_id,
                "fecha_hora": clean_datetime_value(record["fecha_hora"], datetime.now().replace(microsecond=0).isoformat()),
                "analista": clean_text_value(record["analista"], "Sin registrar"),
                "lote": clean_text_value(record["lote"], "Sin lote"),
                "tamano_muestra": max(variable_sizes) if variable_sizes else 1,
            },
        ).data[0]
        insert_rows(
            "mediciones",
            [{"subgrupo_id": subgrupo["id"], **row} for row in measurement_rows],
        )
        created_subgroups += 1
        created_values += len(measurement_rows)
    clear_cache()
    st.success(f"Carga continua completada: {created_subgroups} subgrupos y {created_values} mediciones.")


def bulk_load_attributes(df):
    df = prepare_bulk_data(df, "Atributos")
    missing = required_bulk_columns("Atributos") - set(df.columns)
    if missing:
        st.error(f"Faltan columnas: {', '.join(sorted(missing))}")
        return
    productos_df = load_productos().copy()
    atributos_df = load_atributos().copy()
    created_subgroups = 0
    created_checks = 0
    for _, row in df.iterrows():
        producto_id, productos_df = ensure_producto(row["producto"], row["tipo_producto"], productos_df)
        atributo_id, atributos_df = ensure_atributo(producto_id, row["atributo"], row["tipo_inspeccion"], atributos_df)
        unidades = pd.to_numeric(row["unidades_inspeccionadas"], errors="coerce")
        unidades = 1 if pd.isna(unidades) or unidades < 1 else int(unidades)
        no_conformes = pd.to_numeric(row["no_conformes"], errors="coerce")
        no_conformes = 0 if pd.isna(no_conformes) else int(no_conformes)
        no_conformes = max(0, min(no_conformes, unidades))
        subgrupo = insert_row(
            "subgrupos",
            {
                "producto_id": producto_id,
                "fecha_hora": clean_datetime_value(row["fecha_hora"], datetime.now().replace(microsecond=0).isoformat()),
                "analista": clean_text_value(row["analista"], "Sin registrar"),
                "lote": clean_text_value(row["lote"], "Sin lote"),
                "unidades_inspeccionadas": unidades,
            },
        ).data[0]
        insert_rows(
            "inspecciones_atributos",
            [
                {"subgrupo_id": subgrupo["id"], "atributo_id": atributo_id, "conforma": idx >= no_conformes}
                for idx in range(unidades)
            ],
        )
        created_subgroups += 1
        created_checks += unidades
    clear_cache()
    st.success(f"Carga de atributos completada: {created_subgroups} subgrupos y {created_checks} inspecciones.")


def uploaded_continuous_frame(df):
    prepared = prepare_bulk_data(df, "Continuos")
    if "valor" not in prepared.columns:
        return pd.DataFrame()
    out = prepared.copy()
    out["valor"] = to_numeric_flexible(out["valor"])
    out = out.dropna(subset=["valor"]).copy()
    if out.empty:
        return out
    for column, default in {
        "producto": "Producto importado",
        "variable": "Variable importada",
        "unidad": "Sin unidad",
        "fecha_hora": datetime.now().replace(microsecond=0).isoformat(),
        "analista": "Sin registrar",
        "lote": "Sin lote",
        "subgrupo": 1,
    }.items():
        if column not in out.columns:
            out[column] = default
    out["fecha_hora"] = pd.to_datetime(out["fecha_hora"], errors="coerce")
    out["fecha_hora"] = out["fecha_hora"].fillna(pd.Timestamp.now())
    fallback_subgroups = pd.Series(np.arange(1, len(out) + 1), index=out.index)
    out["subgrupo"] = pd.to_numeric(out["subgrupo"], errors="coerce").fillna(fallback_subgroups).astype(int)
    group_cols = ["producto", "subgrupo", "fecha_hora", "analista", "lote"]
    out["subgrupo_id"] = pd.factorize(out[group_cols].astype(str).agg("|".join, axis=1))[0] + 1
    out["nombre_variable"] = out["variable"].apply(lambda value: clean_text_value(value, "Variable importada"))
    out["unidad"] = out["unidad"].apply(lambda value: clean_text_value(value, "Sin unidad"))
    return out


def uploaded_attribute_frame(df):
    prepared = prepare_bulk_data(df, "Atributos")
    required = {"atributo", "unidades_inspeccionadas", "no_conformes"}
    if not required.issubset(prepared.columns):
        return pd.DataFrame()
    rows = []
    default_dt = datetime.now().replace(microsecond=0).isoformat()
    for idx, row in prepared.iterrows():
        unidades = pd.to_numeric(row.get("unidades_inspeccionadas"), errors="coerce")
        unidades = 1 if pd.isna(unidades) or unidades < 1 else int(unidades)
        no_conformes = pd.to_numeric(row.get("no_conformes"), errors="coerce")
        no_conformes = 0 if pd.isna(no_conformes) else int(no_conformes)
        no_conformes = max(0, min(no_conformes, unidades))
        fecha_hora = pd.to_datetime(row.get("fecha_hora", default_dt), errors="coerce")
        if pd.isna(fecha_hora):
            fecha_hora = pd.Timestamp.now()
        record = {
            "subgrupo_id": idx + 1,
            "producto": clean_text_value(row.get("producto"), "Producto importado"),
            "nombre_atributo": clean_text_value(row.get("atributo"), "Atributo importado"),
            "tipo_inspeccion": clean_text_value(row.get("tipo_inspeccion"), "p").lower(),
            "fecha_hora": fecha_hora,
            "analista": clean_text_value(row.get("analista"), "Sin registrar"),
            "lote": clean_text_value(row.get("lote"), "Sin lote"),
            "unidades_inspeccionadas": unidades,
        }
        if record["tipo_inspeccion"] not in ["p", "np", "c", "u"]:
            record["tipo_inspeccion"] = "p"
        rows.extend({**record, "conforma": unit >= no_conformes} for unit in range(unidades))
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out["no_conforma"] = ~out["conforma"].astype(bool)
    return out


def render_continuous_uploaded_results(df, key_prefix):
    analysis = uploaded_continuous_frame(df)
    if analysis.empty:
        st.warning("No se detectaron columnas numericas suficientes para analisis continuo.")
        return
    products = ["Todos"] + sorted(analysis["producto"].dropna().astype(str).unique())
    product = st.selectbox("Producto", products, key=f"{key_prefix}_product")
    filtered = analysis if product == "Todos" else analysis[analysis["producto"].astype(str) == product]
    variable = st.selectbox("Variable continua", sorted(filtered["nombre_variable"].dropna().astype(str).unique()), key=f"{key_prefix}_var")
    current = filtered[filtered["nombre_variable"].astype(str) == variable].copy()
    stats = subgroup_stats(current)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Subgrupos", len(stats))
    c2.metric("Mediciones", len(current))
    c3.metric("Media", f"{current['valor'].mean():.4g}")
    c4.metric("Desv. est.", f"{current['valor'].std(ddof=1):.4g}" if len(current) > 1 else "0")
    if len(stats) < MIN_SUBGROUPS:
        st.warning(f"Hay {len(stats)} subgrupos. La app calcula resultados exploratorios, pero para control formal se recomiendan minimo {MIN_SUBGROUPS}.")
    tab_summary, tab_control, tab_capacity, tab_export = st.tabs(["Resumen", "Control", "Capacidad", "Exportar"])
    with tab_summary:
        st.dataframe(descriptive_stats(current["valor"]).round(4), width="stretch", hide_index=True)
        normality_card(current["valor"])
        fig = px.histogram(current, x="valor", nbins=30, marginal="box")
        fig.update_layout(title=f"Distribucion de {variable}", xaxis_title=variable, yaxis_title="Frecuencia")
        st.plotly_chart(style_chart(fig), width="stretch")
    with tab_control:
        if len(stats) < 2:
            st.info("Se necesitan al menos 2 subgrupos para graficos de control.")
        else:
            if stats["n"].nunique() > 1:
                st.warning("Hay tamanos de subgrupo diferentes. Los limites usan el tamano mediano.")
            limits_r = xbar_r_limits(stats)
            limits_s = xbar_s_limits(stats)
            st.plotly_chart(chart_with_limits(stats, "subgrupo", "media", limits_r["x_center"], limits_r["x_ucl"], limits_r["x_lcl"], "Grafico X barra", "Media"), width="stretch")
            st.plotly_chart(chart_with_limits(stats, "subgrupo", "rango", limits_r["r_center"], limits_r["r_ucl"], limits_r["r_lcl"], "Grafico R", "Rango"), width="stretch")
            with st.expander("Ver grafico X-S"):
                st.plotly_chart(chart_with_limits(stats, "subgrupo", "media", limits_s["x_center"], limits_s["x_ucl"], limits_s["x_lcl"], "Grafico X barra (X-S)", "Media"), width="stretch")
                st.plotly_chart(chart_with_limits(stats, "subgrupo", "s", limits_s["s_center"], limits_s["s_ucl"], limits_s["s_lcl"], "Grafico S", "Desv. est."), width="stretch")
            violations = pd.concat(
                [
                    detect_control_rules(stats, "media", limits_r["x_center"], limits_r["x_ucl"], limits_r["x_lcl"]),
                    detect_control_rules(stats, "rango", limits_r["r_center"], limits_r["r_ucl"], limits_r["r_lcl"]),
                ],
                ignore_index=True,
            )
            show_control_decision(violations)
    with tab_capacity:
        min_value = float(current["valor"].min())
        max_value = float(current["valor"].max())
        spread = max(max_value - min_value, 1.0)
        col_lsl, col_usl = st.columns(2)
        lsl = col_lsl.number_input("LIE", value=min_value, key=f"{key_prefix}_lsl")
        usl = col_usl.number_input("LSE", value=max_value + (0.01 * spread if max_value == min_value else 0.0), key=f"{key_prefix}_usl")
        if usl <= lsl:
            st.error("LSE debe ser mayor que LIE.")
        else:
            result = process_capability_from_subgroups(current.sort_values("fecha_hora"), lsl, usl)
            if result:
                for metric in ["Cp", "Cpk", "Pp", "Ppk"]:
                    result[f"Interpretacion {metric}"] = capability_label(result[metric])
                st.dataframe(pd.DataFrame([result]).round(4), width="stretch", hide_index=True)
                g1, g2, g3, g4 = st.columns(4)
                g1.plotly_chart(capability_gauge(result["Cp"], "Cp"), width="stretch")
                g2.plotly_chart(capability_gauge(result["Cpk"], "Cpk"), width="stretch")
                g3.plotly_chart(capability_gauge(result["Pp"], "Pp"), width="stretch")
                g4.plotly_chart(capability_gauge(result["Ppk"], "Ppk"), width="stretch")
    with tab_export:
        frames = {
            "datos_originales": df,
            "datos_continuos": analysis,
            "subgrupos": stats,
            "descriptiva": descriptive_stats(current["valor"]).round(4),
        }
        st.download_button(
            "Descargar resultados continuos en Excel",
            excel_bytes(frames),
            file_name="analisis_continuo_carga.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key_prefix}_download",
        )


def render_attribute_uploaded_results(df, key_prefix):
    analysis = uploaded_attribute_frame(df)
    if analysis.empty:
        st.warning("No se detectaron columnas de atributos. Usa columnas como atributo, unidades_inspeccionadas y no_conformes.")
        return
    atributo = st.selectbox("Atributo", sorted(analysis["nombre_atributo"].dropna().astype(str).unique()), key=f"{key_prefix}_attr")
    current = analysis[analysis["nombre_atributo"].astype(str) == atributo].copy()
    stats = attribute_stats(current)
    chart_type = current["tipo_inspeccion"].dropna().iloc[0] if not current["tipo_inspeccion"].dropna().empty else "p"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Subgrupos", len(stats))
    c2.metric("Inspecciones", len(current))
    c3.metric("No conformes", int(current["no_conforma"].sum()))
    c4.metric("Tipo", chart_type)
    if len(stats) < MIN_SUBGROUPS:
        st.warning(f"Hay {len(stats)} subgrupos. La app calcula resultados exploratorios, pero para control formal se recomiendan minimo {MIN_SUBGROUPS}.")
    tab_control, tab_pareto, tab_capacity, tab_export = st.tabs(["Control", "Pareto", "Capacidad", "Exportar"])
    with tab_control:
        if len(stats) < 2:
            st.info("Se necesitan al menos 2 subgrupos para graficos de control.")
        elif chart_type == "p":
            pbar = stats["defectos"].sum() / stats["inspeccionados"].sum()
            stats["ucl"] = np.minimum(1, pbar + 3 * np.sqrt((pbar * (1 - pbar)) / stats["inspeccionados"]))
            stats["lcl"] = np.maximum(0, pbar - 3 * np.sqrt((pbar * (1 - pbar)) / stats["inspeccionados"]))
            st.plotly_chart(chart_with_limits(stats, "subgrupo", "p", pbar, stats["ucl"], stats["lcl"], "Grafico p", "Proporcion no conforme"), width="stretch")
            show_control_decision(detect_control_rules(stats, "p", pbar, stats["ucl"], stats["lcl"]))
        elif chart_type == "np":
            nbar = stats["inspeccionados"].mean()
            pbar = stats["defectos"].sum() / stats["inspeccionados"].sum()
            center = nbar * pbar
            ucl = center + 3 * np.sqrt(nbar * pbar * (1 - pbar))
            lcl = max(0, center - 3 * np.sqrt(nbar * pbar * (1 - pbar)))
            st.plotly_chart(chart_with_limits(stats, "subgrupo", "defectos", center, ucl, lcl, "Grafico np", "No conformes"), width="stretch")
            show_control_decision(detect_control_rules(stats, "defectos", center, ucl, lcl))
        elif chart_type == "c":
            cbar = stats["defectos"].mean()
            ucl = cbar + 3 * np.sqrt(cbar)
            lcl = max(0, cbar - 3 * np.sqrt(cbar))
            st.plotly_chart(chart_with_limits(stats, "subgrupo", "defectos", cbar, ucl, lcl, "Grafico c", "Defectos"), width="stretch")
            show_control_decision(detect_control_rules(stats, "defectos", cbar, ucl, lcl))
        else:
            ubar = stats["defectos"].sum() / stats["unidades_inspeccionadas"].sum()
            stats["u"] = stats["defectos"] / stats["unidades_inspeccionadas"]
            stats["ucl"] = ubar + 3 * np.sqrt(ubar / stats["unidades_inspeccionadas"])
            stats["lcl"] = np.maximum(0, ubar - 3 * np.sqrt(ubar / stats["unidades_inspeccionadas"]))
            st.plotly_chart(chart_with_limits(stats, "subgrupo", "u", ubar, stats["ucl"], stats["lcl"], "Grafico u", "Defectos por unidad"), width="stretch")
            show_control_decision(detect_control_rules(stats, "u", ubar, stats["ucl"], stats["lcl"]))
    with tab_pareto:
        pareto = analysis.groupby("nombre_atributo", as_index=False)["no_conforma"].sum()
        pareto = pareto.sort_values("no_conforma", ascending=False)
        total = pareto["no_conforma"].sum()
        pareto["porcentaje_acumulado"] = pareto["no_conforma"].cumsum() / total * 100 if total else 0
        fig = go.Figure()
        fig.add_bar(x=pareto["nombre_atributo"], y=pareto["no_conforma"], name="Frecuencia")
        fig.add_trace(go.Scatter(x=pareto["nombre_atributo"], y=pareto["porcentaje_acumulado"], yaxis="y2", mode="lines+markers", name="% acumulado"))
        fig.update_layout(title="Diagrama de Pareto", yaxis_title="No conformidades", yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 110]))
        st.plotly_chart(style_chart(fig), width="stretch")
        st.dataframe(pareto, width="stretch", hide_index=True)
    with tab_capacity:
        result = pd.DataFrame([attribute_capability(current)])
        st.dataframe(result.round(4), width="stretch", hide_index=True)
        fig = px.bar(result, y="DPMO", text="DPMO")
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig.update_layout(title="DPMO observado", xaxis_title="", yaxis_title="DPMO", showlegend=False)
        st.plotly_chart(style_chart(fig, height=360), width="stretch")
    with tab_export:
        frames = {
            "datos_originales": df,
            "datos_atributos": analysis,
            "subgrupos": stats,
        }
        st.download_button(
            "Descargar resultados de atributos en Excel",
            excel_bytes(frames),
            file_name="analisis_atributos_carga.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key_prefix}_download",
        )


def render_uploaded_analysis(df, upload_mode):
    section_header("Analisis automatico del archivo", "Resultados calculados directamente desde la carga actual")
    if upload_mode == "Continuos":
        render_continuous_uploaded_results(df, "upload_continuous")
    elif upload_mode == "Atributos":
        render_attribute_uploaded_results(df, "upload_attributes")
    else:
        cont_tab, attr_tab = st.tabs(["Continuos detectados", "Atributos detectados"])
        with cont_tab:
            render_continuous_uploaded_results(df, "upload_free_cont")
        with attr_tab:
            render_attribute_uploaded_results(df, "upload_free_attr")


apply_design()

st.markdown(
    f"""
    <div class="cep-hero">
        <img src="{UNIMAG_ESCUDO_URL}" alt="Escudo Universidad del Magdalena">
        <div>
            <h1>Control Estadistico de Procesos</h1>
            <p>Monitoreo de calidad para frutas y hortalizas con trazabilidad, graficos de control, capacidad de proceso, Pareto y exportacion.</p>
        </div>
        <div class="cep-hero-badge">Universidad del Magdalena</div>
    </div>
    """,
    unsafe_allow_html=True,
)

productos = load_productos()
variables = load_variables()
atributos = load_atributos()
mediciones = flatten_mediciones(load_mediciones())
inspecciones = flatten_inspecciones(load_inspecciones())

pages = [
    "Panel",
    "Subir datos",
    "Tutorial",
    "Catalogos",
    "Registro continuo",
    "Registro atributos",
    "Inspeccion y muestreo",
    "Graficos de control",
    "Capacidad",
    "Pareto",
    "Trazabilidad",
    "Informe IA",
    "Exportar",
]
st.markdown("<div class='cep-nav'>", unsafe_allow_html=True)
if "current_page" not in st.session_state:
    st.session_state.current_page = "Panel"
if st.session_state.current_page == "Carga masiva":
    st.session_state.current_page = "Subir datos"
if hasattr(st, "pills"):
    selected_page = st.pills(
        "Modulo",
        pages,
        default=st.session_state.current_page if st.session_state.current_page in pages else "Panel",
        selection_mode="single",
        label_visibility="collapsed",
    )
    page = selected_page or st.session_state.current_page
else:
    page = st.radio(
        "Modulo",
        pages,
        index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0,
        horizontal=True,
        label_visibility="collapsed",
    )
st.session_state.current_page = page
st.markdown("</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.metric("Productos", len(productos))
st.sidebar.metric("Subgrupos", len(load_subgrupos()))
st.sidebar.caption("Base Supabase conectada. Los analisis requieren minimo 25 subgrupos por grafico.")

if page == "Panel":
    section_header("Resumen ejecutivo", "Estado general de captura, inspeccion y analisis")
    st.markdown(
        """
        <div class="cep-upload-panel">
            <h3>Sube tus datos reales para la sustentacion</h3>
            <p>Usa el modulo <strong>Subir datos</strong> para importar Excel, CSV, TSV, JSON tabular o adjuntar archivos de soporte como PDF, Word y PowerPoint.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Ir a Subir datos"):
        st.session_state.current_page = "Subir datos"
        st.rerun()
    productos_filtro = ["Todos"] + sorted(productos["nombre"].dropna().unique()) if not productos.empty else ["Todos"]
    producto_filtro = st.selectbox("Producto en dashboard", productos_filtro)
    mediciones_dash = mediciones.copy()
    inspecciones_dash = inspecciones.copy()
    if producto_filtro != "Todos":
        mediciones_dash = mediciones_dash[mediciones_dash["producto"] == producto_filtro] if not mediciones_dash.empty else mediciones_dash
        inspecciones_dash = inspecciones_dash[inspecciones_dash["producto"] == producto_filtro] if not inspecciones_dash.empty else inspecciones_dash

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Productos", len(productos))
    c2.metric("Variables continuas", len(variables))
    c3.metric("Atributos", len(atributos))
    c4.metric("Mediciones", len(mediciones_dash))

    if productos.empty:
        note("La base esta conectada, pero todavia no hay datos. Puedes crear catalogos manualmente o cargar un conjunto demo para probar todos los analisis.")
        if st.button("Cargar datos demo para verificar analisis"):
            seed_demo_dataset()
            st.rerun()

    c5, c6 = st.columns(2)
    with c5:
        if not mediciones_dash.empty:
            section_header("Mediciones por producto")
            fig = px.histogram(mediciones_dash, x="producto", color="nombre_variable", barmode="group")
            fig.update_layout(title="Volumen de mediciones continuas", xaxis_title="Producto", yaxis_title="Mediciones")
            st.plotly_chart(style_chart(fig), width="stretch")
        else:
            empty_state("Aun no hay mediciones continuas.")
    with c6:
        if not inspecciones_dash.empty:
            section_header("No conformidades por atributo")
            pareto = inspecciones_dash.groupby("nombre_atributo", as_index=False)["no_conforma"].sum()
            fig = px.bar(pareto, x="nombre_atributo", y="no_conforma", color="nombre_atributo")
            fig.update_layout(title="Frecuencia de no conformidades", xaxis_title="Atributo", yaxis_title="No conformidades", showlegend=False)
            st.plotly_chart(style_chart(fig), width="stretch")
        else:
            empty_state("Aun no hay inspecciones por atributos.")

    if not mediciones_dash.empty or not inspecciones_dash.empty:
        section_header("Preparacion para analisis", "El taller exige minimo 25 subgrupos por grafico")
        c7, c8 = st.columns(2)
        if not mediciones_dash.empty:
            ready_var = (
                mediciones_dash.groupby("nombre_variable")["subgrupo_id"]
                .nunique()
                .reset_index(name="subgrupos")
                .assign(estado=lambda d: np.where(d["subgrupos"] >= MIN_SUBGROUPS, "Listo", "Faltan datos"))
            )
            c7.dataframe(ready_var, width="stretch", hide_index=True)
        if not inspecciones_dash.empty:
            ready_attr = (
                inspecciones_dash.groupby("nombre_atributo")["subgrupo_id"]
                .nunique()
                .reset_index(name="subgrupos")
                .assign(estado=lambda d: np.where(d["subgrupos"] >= MIN_SUBGROUPS, "Listo", "Faltan datos"))
            )
            c8.dataframe(ready_attr, width="stretch", hide_index=True)

elif page == "Tutorial":
    section_header("Mini tutorial", "Guia rapida para que el docente pruebe la aplicacion")
    note("La aplicacion guarda datos reales en Supabase. Para generar graficos de control se requieren minimo 25 subgrupos por variable o atributo.")
    paso1, paso2, paso3 = st.tabs(["1. Preparar datos", "2. Cargar datos", "3. Analizar y exportar"])
    with paso1:
        st.markdown(
            """
            **Opcion manual**

            1. Entra a `Catalogos`.
            2. Crea un producto: por ejemplo `Mango`, `Tomate` o `Banano`.
            3. Crea variables continuas: `Peso`, `pH`, `Brix`, `Diametro`.
            4. Crea atributos: `Manchas`, `Golpes`, `Podrido`, `Defecto de color`.

            **Opcion con archivo**

            En `Subir datos` puedes guardar una tabla real tal como viene del archivo. Si quieres que alimente graficos CEP estructurados, usa las plantillas de continuos o atributos como referencia.
            """
        )
        col_a, col_b = st.columns(2)
        col_a.download_button(
            "Plantilla continua Excel",
            file_bytes_for_df(template_continuous_df(), "xlsx"),
            "plantilla_continuos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        col_b.download_button(
            "Plantilla atributos Excel",
            file_bytes_for_df(template_attributes_df(), "xlsx"),
            "plantilla_atributos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with paso2:
        st.markdown(
            """
            **Carga manual**

            - `Registro continuo`: cada guardado crea un subgrupo con varias mediciones numericas.
            - `Registro atributos`: cada guardado crea un subgrupo de inspeccion conforme/no conforme.

            **Subir datos**

            1. Entra a `Subir datos`.
            2. Elige si la importacion es `Continuos`, `Atributos` o `Libre`.
            3. Sube un archivo `.csv`, `.tsv`, `.xlsx`, `.xls` o `.json`.
            4. Revisa la vista previa con las columnas reales detectadas.
            5. Marca la confirmacion y pulsa `Guardar importacion en Supabase`.
            """
        )
    with paso3:
        st.markdown(
            """
            **Analisis disponibles**

            - `Graficos de control`: X-R, X-S, p, np, c, u y reglas de alarma.
            - `Capacidad`: Cp, Cpk, Pp, Ppk y DPMO/Z para atributos.
            - `Pareto`: prioridad de defectos.
            - `Trazabilidad`: filtros por analista, lote y fecha.
            - `Informe IA`: genera una interpretacion si configuras Gemini, OpenAI u OpenRouter.
            - `Exportar`: descarga la base consolidada a Excel.
            """
        )
        st.success("Ruta recomendada para sustentacion: Panel -> Tutorial -> Subir datos -> Graficos de control -> Capacidad -> Exportar.")

elif page == "Catalogos":
    section_header("Catalogos maestros", "Define productos, variables continuas y atributos antes de registrar datos")
    with st.form("producto_form"):
        nombre = st.text_input("Nombre del producto")
        tipo = st.selectbox("Tipo", ["Fruta", "Hortaliza", "Otro"])
        submitted = st.form_submit_button("Guardar producto")
        if submitted:
            if not nombre.strip():
                st.warning("Escribe el nombre del producto.")
                st.stop()
            insert_row("productos", {"nombre": nombre.strip(), "tipo": tipo})
            clear_cache()
            st.success("Producto guardado.")
            st.rerun()

    p_opts = product_options(productos)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Variables continuas")
        with st.form("variable_form"):
            producto_label = st.selectbox("Producto", list(p_opts.keys()), key="var_prod") if p_opts else None
            nombre_variable = st.text_input("Variable", placeholder="Peso, pH, Brix, diametro")
            unidad = st.text_input("Unidad", placeholder="g, pH, Brix, mm")
            submitted = st.form_submit_button("Guardar variable")
            if submitted and producto_label:
                if not nombre_variable.strip() or not unidad.strip():
                    st.warning("Completa nombre de variable y unidad.")
                    st.stop()
                insert_row(
                    "variables_continuas",
                    {"producto_id": p_opts[producto_label], "nombre_variable": nombre_variable.strip(), "unidad": unidad.strip()},
                )
                clear_cache()
                st.success("Variable guardada.")
                st.rerun()
    with col2:
        st.subheader("Atributos")
        with st.form("atributo_form"):
            producto_label = st.selectbox("Producto", list(p_opts.keys()), key="atr_prod") if p_opts else None
            nombre_atributo = st.text_input("Atributo", placeholder="Golpeado, podrido, mancha")
            tipo_inspeccion = st.selectbox("Tipo de grafico", ["p", "np", "c", "u"])
            submitted = st.form_submit_button("Guardar atributo")
            if submitted and producto_label:
                if not nombre_atributo.strip():
                    st.warning("Completa el nombre del atributo.")
                    st.stop()
                insert_row(
                    "atributos",
                    {"producto_id": p_opts[producto_label], "nombre_atributo": nombre_atributo.strip(), "tipo_inspeccion": tipo_inspeccion},
                )
                clear_cache()
                st.success("Atributo guardado.")
                st.rerun()

    section_header("Datos registrados")
    t1, t2, t3 = st.tabs(["Productos", "Variables", "Atributos"])
    with t1:
        st.dataframe(productos, width="stretch", hide_index=True)
    with t2:
        st.dataframe(variables, width="stretch", hide_index=True)
    with t3:
        st.dataframe(atributos, width="stretch", hide_index=True)

elif page == "Registro continuo":
    section_header("Registro continuo", "Captura subgrupos con trazabilidad para variables como peso, pH o Brix")
    p_opts = product_options(productos)
    if not p_opts:
        empty_state("Primero registra productos y variables en Catalogos.")
    else:
        with st.form("continuo_form"):
            producto_label = st.selectbox("Producto", list(p_opts.keys()))
            producto_id = p_opts[producto_label]
            v_opts = variable_options(variables, producto_id)
            fecha = st.date_input("Fecha", value=date.today())
            hora = st.time_input("Hora", value=datetime.now().time().replace(microsecond=0))
            analista = st.text_input("Analista")
            lote = st.text_input("Lote")
            tamano = st.number_input("Tamano de subgrupo", min_value=1, value=5, step=1)
            variable_label = st.selectbox("Variable", list(v_opts.keys())) if v_opts else None
            raw_values = st.text_area("Valores separados por coma", placeholder="150.2, 151.0, 149.8, 150.6, 150.1")
            submitted = st.form_submit_button("Guardar mediciones")
            if submitted and variable_label:
                if not analista.strip() or not lote.strip():
                    st.warning("Completa analista y lote para mantener trazabilidad.")
                    st.stop()
                try:
                    tokens = [token for token in re.split(r"[;,\s]+", raw_values.strip()) if token]
                    values = [float(token.replace(",", ".")) for token in tokens]
                except ValueError:
                    st.error("Revisa los valores: usa numeros separados por coma, punto y coma, espacio o salto de linea.")
                    st.stop()
                if not values:
                    st.warning("Ingresa al menos una medicion.")
                    st.stop()
                if len(values) != int(tamano):
                    st.warning(f"El tamano declarado es {int(tamano)}, pero ingresaste {len(values)} valores. Ajusta uno de los dos.")
                    st.stop()
                fecha_hora = datetime.combine(fecha, hora).isoformat()
                subgrupo = insert_row(
                    "subgrupos",
                    {"producto_id": producto_id, "fecha_hora": fecha_hora, "analista": analista.strip(), "lote": lote.strip(), "tamano_muestra": int(tamano)},
                ).data[0]
                insert_rows(
                    "mediciones",
                    [{"subgrupo_id": subgrupo["id"], "variable_id": v_opts[variable_label], "valor": value} for value in values],
                )
                clear_cache()
                st.success(f"Subgrupo guardado con {len(values)} mediciones.")
                st.rerun()

elif page == "Registro atributos":
    section_header("Registro por atributos", "Captura conformidad/no conformidad por lote, analista y fecha")
    p_opts = product_options(productos)
    if not p_opts:
        empty_state("Primero registra productos y atributos en Catalogos.")
    else:
        with st.form("atributos_registro_form"):
            producto_label = st.selectbox("Producto", list(p_opts.keys()))
            producto_id = p_opts[producto_label]
            a_opts = atributo_options(atributos, producto_id)
            fecha = st.date_input("Fecha", value=date.today())
            hora = st.time_input("Hora", value=datetime.now().time().replace(microsecond=0))
            analista = st.text_input("Analista")
            lote = st.text_input("Lote")
            unidades = st.number_input("Unidades inspeccionadas", min_value=1, value=10, step=1)
            atributo_label = st.selectbox("Atributo", list(a_opts.keys())) if a_opts else None
            no_conformes = st.number_input("Unidades no conformes / defectos", min_value=0, max_value=int(unidades), value=0, step=1)
            submitted = st.form_submit_button("Guardar inspeccion")
            if submitted and atributo_label:
                if not analista.strip() or not lote.strip():
                    st.warning("Completa analista y lote para mantener trazabilidad.")
                    st.stop()
                fecha_hora = datetime.combine(fecha, hora).isoformat()
                subgrupo = insert_row(
                    "subgrupos",
                    {"producto_id": producto_id, "fecha_hora": fecha_hora, "analista": analista.strip(), "lote": lote.strip(), "unidades_inspeccionadas": int(unidades)},
                ).data[0]
                insert_rows(
                    "inspecciones_atributos",
                    [
                        {"subgrupo_id": subgrupo["id"], "atributo_id": a_opts[atributo_label], "conforma": idx >= int(no_conformes)}
                        for idx in range(int(unidades))
                    ],
                )
                clear_cache()
                st.success("Inspeccion guardada.")
                st.rerun()

elif page == "Subir datos":
    section_header("Subir datos propios", "Importa base de datos tabular y adjunta archivos de soporte")
    note("Esta pantalla guarda tu archivo real en Supabase como una importacion cruda. No inventa producto, variable, subgrupo ni mediciones si el archivo no los trae.")
    tab_data, tab_files, tab_format = st.tabs(["Base de datos", "Archivos de soporte", "Formato requerido"])

    with tab_data:
        st.markdown(
            """
            <div class="cep-upload-panel">
                <h3>Carga una tabla real</h3>
                <p>Sube Excel, CSV, TSV o JSON tabular. La app guarda exactamente las columnas detectadas para analizarlas sin completar campos artificiales.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        modo_carga = st.radio("Clasificacion de la importacion", ["Continuos", "Atributos", "Libre"], horizontal=True)
        if modo_carga == "Continuos":
            template_df = template_continuous_df()
            ejemplo = """subgrupo,producto,tipo_producto,variable,unidad,fecha_hora,analista,lote,valor
1,Mango Tommy,Fruta,Peso,g,2026-05-19 08:00,Ana,L-001,421.4
1,Mango Tommy,Fruta,Peso,g,2026-05-19 08:00,Ana,L-001,419.8
1,Mango Tommy,Fruta,Peso,g,2026-05-19 08:00,Ana,L-001,423.1
2,Mango Tommy,Fruta,Peso,g,2026-05-19 09:00,Ana,L-002,420.6
2,Mango Tommy,Fruta,Peso,g,2026-05-19 09:00,Ana,L-002,418.9"""
            st.caption("Formato: cada fila es una medicion. Varias filas con el mismo subgrupo forman un subgrupo racional.")
        elif modo_carga == "Atributos":
            template_df = template_attributes_df()
            ejemplo = """subgrupo,producto,tipo_producto,atributo,tipo_inspeccion,fecha_hora,analista,lote,unidades_inspeccionadas,no_conformes
1,Mango Tommy,Fruta,Manchas,p,2026-05-19 08:00,Ana,L-001,30,3
2,Mango Tommy,Fruta,Manchas,p,2026-05-19 09:00,Ana,L-002,30,1
3,Mango Tommy,Fruta,Golpes,u,2026-05-19 10:00,Carlos,L-003,30,2"""
            st.caption("Formato: cada fila es un subgrupo de inspeccion.")
        else:
            template_df = pd.DataFrame(
                [
                    {"lote": "L-001", "calibre": "Grande", "peso_g": 421.4, "brix": 12.1},
                    {"lote": "L-002", "calibre": "Mediano", "peso_g": 419.8, "brix": 11.9},
                ]
            )
            ejemplo = """lote,calibre,peso_g,brix
L-001,Grande,421.4,12.1
L-002,Mediano,419.8,11.9"""
            st.caption("Formato libre: se guardan las columnas reales que trae el archivo.")
        col_tpl1, col_tpl2 = st.columns(2)
        col_tpl1.download_button(
            "Descargar plantilla Excel",
            file_bytes_for_df(template_df, "xlsx"),
            f"plantilla_{modo_carga.lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        col_tpl2.download_button(
            "Descargar plantilla CSV",
            file_bytes_for_df(template_df, "csv"),
            f"plantilla_{modo_carga.lower()}.csv",
            mime="text/csv",
        )
        with st.expander("Ver ejemplo de columnas y datos"):
            st.dataframe(template_df, width="stretch", hide_index=True)
            st.code(ejemplo, language="csv")
        uploaded = st.file_uploader(
            "Subir archivo de datos",
            type=["csv", "tsv", "txt", "xlsx", "xls", "json"],
            key=f"upload_{modo_carga}",
            help="Formatos admitidos para analisis: CSV, TSV, Excel XLSX/XLS y JSON tabular.",
        )
        sheet_name = None
        if uploaded is not None and uploaded.name.lower().endswith((".xlsx", ".xls")):
            try:
                uploaded.seek(0)
                excel = pd.ExcelFile(uploaded)
                sheet_name = st.selectbox("Hoja de Excel", excel.sheet_names)
            except Exception as exc:
                st.error("No se pudieron leer las hojas del Excel.")
                st.code(str(exc))
        pasted = st.text_area("O pega el CSV aqui", height=190, placeholder=ejemplo)
        preview = parse_data_input(uploaded, pasted, sheet_name)
        if not preview.empty:
            numeric_columns = [
                column for column in preview.columns
                if to_numeric_flexible(preview[column]).notna().any()
            ]
            st.success("Archivo listo para analizar. Solo se usaran las columnas reales detectadas.")
            cprev1, cprev2, cprev3 = st.columns(3)
            cprev1.metric("Filas detectadas", len(preview))
            cprev2.metric("Columnas reales", len(preview.columns))
            cprev3.metric("Formato", uploaded.name.split(".")[-1].upper() if uploaded is not None else "CSV pegado")
            if numeric_columns:
                st.caption("Columnas numericas detectadas: " + ", ".join(str(column) for column in numeric_columns))
            st.dataframe(preview.head(50), width="stretch", hide_index=True)
            render_uploaded_analysis(preview, modo_carga)
            with st.expander("Guardar una copia cruda en Supabase"):
                st.caption("El analisis anterior no depende de este guardado. Guardar es opcional y requiere que exista la tabla datos_importados.")
                confirm_load = st.checkbox("Confirmo que quiero guardar esta importacion cruda en Supabase")
                if st.button("Guardar copia en Supabase"):
                    if not confirm_load:
                        st.warning("Marca la confirmacion antes de guardar.")
                    else:
                        source_name = uploaded.name if uploaded is not None else "CSV pegado"
                        save_raw_import(preview, modo_carga, source_name, sheet_name)
                        st.rerun()
        else:
            st.info("Sube un archivo o pega un CSV para ver el analisis automatico.")

        if st.checkbox("Ver importaciones guardadas en Supabase"):
            importaciones = load_datos_importados()
            if not importaciones.empty:
                with st.expander("Importaciones guardadas en Supabase", expanded=True):
                    summary = importaciones[["created_at", "nombre_archivo", "tipo_carga", "filas", "columnas"]].copy()
                    summary["columnas"] = summary["columnas"].apply(lambda value: ", ".join(value) if isinstance(value, list) else str(value))
                    st.dataframe(summary.tail(20), width="stretch", hide_index=True)
            else:
                st.info("No hay importaciones guardadas.")

    with tab_files:
        st.markdown(
            """
            <div class="cep-upload-panel">
                <h3>Adjuntar archivos de soporte</h3>
                <p>Guarda evidencias, talleres, PDF, Word, PowerPoint, imagenes o anexos en Supabase. Estos archivos no alimentan los calculos; sirven como respaldo documental.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        support_files = st.file_uploader(
            "Subir cualquier archivo de soporte",
            accept_multiple_files=True,
            key="support_files",
            help="Puedes subir PDF, PPTX, DOCX, imagenes, TXT u otros. Limite recomendado: 8 MB por archivo.",
        )
        responsable = st.text_input("Responsable de la carga", value="")
        descripcion = st.text_area("Descripcion o nota del archivo", height=90)
        if support_files:
            files_df = pd.DataFrame(
                [
                    {
                        "archivo": f.name,
                        "tipo": f.type or "desconocido",
                        "tamano": human_size(len(f.getvalue())),
                    }
                    for f in support_files
                ]
            )
            st.dataframe(files_df, width="stretch", hide_index=True)
        confirm_files = st.checkbox("Confirmo que quiero guardar estos archivos de soporte en Supabase")
        if st.button("Guardar archivos de soporte"):
            if not support_files:
                st.warning("Selecciona uno o mas archivos.")
            elif not confirm_files:
                st.warning("Marca la confirmacion antes de guardar.")
            else:
                ok = 0
                for support_file in support_files:
                    ok += 1 if save_support_file(support_file, responsable, descripcion) else 0
                if ok:
                    st.success(f"Archivos guardados: {ok}.")

    with tab_format:
        st.info("La importacion cruda guarda tu archivo tal como llega. Estas plantillas solo sirven como referencia si quieres preparar datos para analisis CEP estructurado.")
        st.markdown("**Referencia para datos continuos**")
        st.dataframe(template_continuous_df().head(1), width="stretch", hide_index=True)
        st.markdown("**Referencia para atributos**")
        st.dataframe(template_attributes_df().head(1), width="stretch", hide_index=True)
        note("Para graficos de control se necesitan minimo 25 subgrupos por variable o atributo. Si una tabla libre no trae esa estructura, se conserva como importacion en Supabase sin forzarla a mediciones.")

elif page == "Inspeccion y muestreo":
    section_header("Inspeccion y muestreo", "Calcula un tamano de muestra base con correccion por poblacion finita")
    col1, col2, col3 = st.columns(3)
    poblacion = col1.number_input("Tamano del lote", min_value=1, value=1000, step=1)
    confianza = col2.selectbox("Confianza", [0.90, 0.95, 0.99], index=1)
    error = col3.number_input("Error maximo permitido", min_value=0.01, max_value=0.30, value=0.05, step=0.01)
    proporcion = st.slider("Proporcion esperada de no conformidad", 0.01, 0.50, 0.05, 0.01)
    z = norm.ppf(1 - (1 - confianza) / 2)
    n0 = (z**2 * proporcion * (1 - proporcion)) / (error**2)
    muestra = math.ceil(n0 / (1 + ((n0 - 1) / poblacion)))
    c1, c2, c3 = st.columns(3)
    c1.metric("Tamano de muestra sugerido", muestra)
    c2.metric("Nivel Z", f"{z:.3f}")
    c3.metric("Fraccion esperada", f"{proporcion:.2%}")
    note("Para variables se recomienda mantener subgrupos racionales y tamano estable. Para atributos, p/u aceptan tamanos variables; np/c requieren tamanos constantes.")

elif page == "Graficos de control":
    section_header("Graficos de control", "Graficos interactivos con limites, alarmas y decision de proceso")
    tipo = st.radio("Tipo de dato", ["Continuo", "Atributos"], horizontal=True)
    if tipo == "Continuo":
        if mediciones.empty:
            empty_state("No hay mediciones continuas.")
        else:
            variable = st.selectbox("Variable", sorted(mediciones["nombre_variable"].dropna().unique()))
            df = mediciones[mediciones["nombre_variable"] == variable]
            stats = subgroup_stats(df)
            c1, c2, c3 = st.columns(3)
            c1.metric("Subgrupos disponibles", len(stats))
            c2.metric("Tamano mediano", int(stats["n"].median()) if not stats.empty else 0)
            c3.metric("Mediciones", len(df))
            if len(stats) < MIN_SUBGROUPS:
                st.warning(f"Se requieren minimo {MIN_SUBGROUPS} subgrupos para graficar.")
            else:
                if stats["n"].nunique() > 1:
                    st.warning("Hay tamanos de subgrupo diferentes. Los limites X-R/X-S usan el tamano mediano; para analisis formal conviene mantener n constante.")
                section_header("Estadistica descriptiva")
                st.dataframe(descriptive_stats(df["valor"]).round(4), width="stretch")
                normality_card(df["valor"])
                limits_r = xbar_r_limits(stats)
                limits_s = xbar_s_limits(stats)
                tab_r, tab_s = st.tabs(["X-R", "X-S"])
                with tab_r:
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "media", limits_r["x_center"], limits_r["x_ucl"], limits_r["x_lcl"], "Grafico X barra", "Media"), width="stretch")
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "rango", limits_r["r_center"], limits_r["r_ucl"], limits_r["r_lcl"], "Grafico R", "Rango"), width="stretch")
                with tab_s:
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "media", limits_s["x_center"], limits_s["x_ucl"], limits_s["x_lcl"], "Grafico X barra (X-S)", "Media"), width="stretch")
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "s", limits_s["s_center"], limits_s["s_ucl"], limits_s["s_lcl"], "Grafico S", "Desviacion estandar"), width="stretch")
                section_header("Decision de control")
                violations = pd.concat(
                    [
                        detect_control_rules(stats, "media", limits_r["x_center"], limits_r["x_ucl"], limits_r["x_lcl"]),
                        detect_control_rules(stats, "rango", limits_r["r_center"], limits_r["r_ucl"], limits_r["r_lcl"]),
                    ],
                    ignore_index=True,
                )
                show_control_decision(violations)
    else:
        if inspecciones.empty:
            empty_state("No hay inspecciones por atributos.")
        else:
            atributo = st.selectbox("Atributo", sorted(inspecciones["nombre_atributo"].dropna().unique()))
            df = inspecciones[inspecciones["nombre_atributo"] == atributo]
            stats = attribute_stats(df)
            chart_type = df["tipo_inspeccion"].dropna().iloc[0] if not df["tipo_inspeccion"].dropna().empty else "p"
            c1, c2, c3 = st.columns(3)
            c1.metric("Subgrupos disponibles", len(stats))
            c2.metric("Tipo de grafico", chart_type)
            c3.metric("Inspecciones", len(df))
            if len(stats) < MIN_SUBGROUPS:
                st.warning(f"Se requieren minimo {MIN_SUBGROUPS} subgrupos para graficar.")
            else:
                if chart_type in ["np", "c"] and stats["inspeccionados"].nunique() > 1:
                    st.warning("np y c se recomiendan con tamano de subgrupo constante. Si el tamano varia, usa p o u.")
                if chart_type == "p":
                    pbar = stats["defectos"].sum() / stats["inspeccionados"].sum()
                    stats["ucl"] = pbar + 3 * np.sqrt((pbar * (1 - pbar)) / stats["inspeccionados"])
                    stats["lcl"] = np.maximum(0, pbar - 3 * np.sqrt((pbar * (1 - pbar)) / stats["inspeccionados"]))
                    stats["ucl"] = np.minimum(1, stats["ucl"])
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "p", pbar, stats["ucl"], stats["lcl"], "Grafico p", "Proporcion no conforme"), width="stretch")
                    show_control_decision(detect_control_rules(stats, "p", pbar, stats["ucl"], stats["lcl"]))
                elif chart_type == "np":
                    nbar = stats["inspeccionados"].mean()
                    pbar = stats["defectos"].sum() / stats["inspeccionados"].sum()
                    center = nbar * pbar
                    ucl = center + 3 * np.sqrt(nbar * pbar * (1 - pbar))
                    lcl = max(0, center - 3 * np.sqrt(nbar * pbar * (1 - pbar)))
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "defectos", center, ucl, lcl, "Grafico np", "No conformes"), width="stretch")
                    show_control_decision(detect_control_rules(stats, "defectos", center, ucl, lcl))
                elif chart_type == "c":
                    cbar = stats["defectos"].mean()
                    ucl = cbar + 3 * np.sqrt(cbar)
                    lcl = max(0, cbar - 3 * np.sqrt(cbar))
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "defectos", cbar, ucl, lcl, "Grafico c", "Defectos"), width="stretch")
                    show_control_decision(detect_control_rules(stats, "defectos", cbar, ucl, lcl))
                else:
                    ubar = stats["defectos"].sum() / stats["unidades_inspeccionadas"].sum()
                    stats["u"] = stats["defectos"] / stats["unidades_inspeccionadas"]
                    stats["ucl"] = ubar + 3 * np.sqrt(ubar / stats["unidades_inspeccionadas"])
                    stats["lcl"] = np.maximum(0, ubar - 3 * np.sqrt(ubar / stats["unidades_inspeccionadas"]))
                    st.plotly_chart(chart_with_limits(stats, "subgrupo", "u", ubar, stats["ucl"], stats["lcl"], "Grafico u", "Defectos por unidad"), width="stretch")
                    show_control_decision(detect_control_rules(stats, "u", ubar, stats["ucl"], stats["lcl"]))

elif page == "Capacidad":
    section_header("Capacidad de proceso", "Cp/Cpk para capacidad de corto plazo y Pp/Ppk para desempeno total")
    modo = st.radio("Tipo de capacidad", ["Variables", "Atributos"], horizontal=True)
    if modo == "Variables":
        if mediciones.empty:
            empty_state("No hay mediciones continuas.")
        else:
            variable = st.selectbox("Variable", sorted(mediciones["nombre_variable"].dropna().unique()))
            df = mediciones[mediciones["nombre_variable"] == variable]
            st.metric("Subgrupos", df["subgrupo_id"].nunique())
            if df["subgrupo_id"].nunique() < MIN_SUBGROUPS:
                st.warning(f"Se requieren minimo {MIN_SUBGROUPS} subgrupos para calcular capacidad.")
            col1, col2 = st.columns(2)
            lsl = col1.number_input("LIE", value=float(df["valor"].min()))
            usl = col2.number_input("LSE", value=float(df["valor"].max()))
            if usl <= lsl:
                st.error("LSE debe ser mayor que LIE.")
                st.stop()
            result = process_capability_from_subgroups(df.sort_values("fecha_hora"), lsl, usl)
            if result:
                result["Interpretacion Cp"] = capability_label(result["Cp"])
                result["Interpretacion Cpk"] = capability_label(result["Cpk"])
                result["Interpretacion Pp"] = capability_label(result["Pp"])
                result["Interpretacion Ppk"] = capability_label(result["Ppk"])
                st.dataframe(pd.DataFrame([result]).round(4), width="stretch", hide_index=True)
                g1, g2, g3, g4 = st.columns(4)
                g1.plotly_chart(capability_gauge(result["Cp"], "Cp"), width="stretch")
                g2.plotly_chart(capability_gauge(result["Cpk"], "Cpk"), width="stretch")
                g3.plotly_chart(capability_gauge(result["Pp"], "Pp"), width="stretch")
                g4.plotly_chart(capability_gauge(result["Ppk"], "Ppk"), width="stretch")
                fig = px.histogram(df, x="valor", nbins=30, marginal="box")
                fig.add_vline(x=lsl, line_dash="dash", line_color="#dc2626", annotation_text="LIE")
                fig.add_vline(x=usl, line_dash="dash", line_color="#dc2626", annotation_text="LSE")
                fig.update_layout(title=f"Distribucion de {variable}", xaxis_title=variable, yaxis_title="Frecuencia")
                st.plotly_chart(style_chart(fig), width="stretch")
    else:
        if inspecciones.empty:
            empty_state("No hay inspecciones por atributos.")
        else:
            atributo = st.selectbox("Atributo", sorted(inspecciones["nombre_atributo"].dropna().unique()))
            df = inspecciones[inspecciones["nombre_atributo"] == atributo].sort_values("fecha_hora")
            corto = st.number_input("Subgrupos para corto plazo", min_value=1, value=30, step=1)
            largo = attribute_capability(df)
            corto_result = attribute_capability(df, corto)
            result = pd.DataFrame(
                [
                    {"plazo": "Largo plazo", **largo},
                    {"plazo": "Corto plazo", **corto_result},
                ]
            )
            st.dataframe(result.round(4), width="stretch", hide_index=True)
            fig = px.bar(result, x="plazo", y="DPMO", color="plazo", text="DPMO")
            fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            fig.update_layout(title="DPMO por horizonte de estudio", xaxis_title="", yaxis_title="DPMO", showlegend=False)
            st.plotly_chart(style_chart(fig, height=360), width="stretch")
            st.caption("DPMO = defectos por millon de oportunidades. El nivel Z se calcula desde el rendimiento observado.")

elif page == "Pareto":
    section_header("Diagrama de Pareto", "Prioriza defectos por frecuencia y porcentaje acumulado")
    if inspecciones.empty:
        empty_state("No hay datos de atributos.")
    else:
        pareto = inspecciones.groupby("nombre_atributo", as_index=False)["no_conforma"].sum()
        pareto = pareto.sort_values("no_conforma", ascending=False)
        total = pareto["no_conforma"].sum()
        pareto["porcentaje_acumulado"] = pareto["no_conforma"].cumsum() / total * 100 if total else 0
        fig = go.Figure()
        fig.add_bar(x=pareto["nombre_atributo"], y=pareto["no_conforma"], name="Frecuencia")
        fig.add_trace(go.Scatter(x=pareto["nombre_atributo"], y=pareto["porcentaje_acumulado"], yaxis="y2", mode="lines+markers", name="% acumulado"))
        fig.update_layout(title="Diagrama de Pareto", yaxis_title="No conformidades", yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 110]))
        st.plotly_chart(style_chart(fig), width="stretch")
        st.dataframe(pareto, width="stretch", hide_index=True)

elif page == "Trazabilidad":
    section_header("Panel de trazabilidad", "Filtra registros por fuente, analista, lote y fecha")
    fuente = st.radio("Fuente", ["Mediciones", "Inspecciones"], horizontal=True)
    df = mediciones if fuente == "Mediciones" else inspecciones
    if df.empty:
        empty_state("No hay datos para filtrar.")
    else:
        c1, c2, c3 = st.columns(3)
        analistas = ["Todos"] + sorted(df["analista"].dropna().unique())
        lotes = ["Todos"] + sorted(df["lote"].dropna().unique())
        analista = c1.selectbox("Analista", analistas)
        lote = c2.selectbox("Lote", lotes)
        rango = c3.date_input("Rango de fechas", value=(df["fecha_hora"].min().date(), df["fecha_hora"].max().date()))
        filtered = df.copy()
        if analista != "Todos":
            filtered = filtered[filtered["analista"] == analista]
        if lote != "Todos":
            filtered = filtered[filtered["lote"] == lote]
        if isinstance(rango, tuple) and len(rango) == 2:
            start = pd.Timestamp(datetime.combine(rango[0], time.min), tz=filtered["fecha_hora"].dt.tz)
            end = pd.Timestamp(datetime.combine(rango[1], time.max), tz=filtered["fecha_hora"].dt.tz)
            filtered = filtered[(filtered["fecha_hora"] >= start) & (filtered["fecha_hora"] <= end)]
        st.metric("Registros filtrados", len(filtered))
        st.dataframe(filtered, width="stretch", hide_index=True)

elif page == "Informe IA":
    section_header("Informe con IA", "Genera una interpretacion tecnica del estado del proceso")
    note("La IA es opcional: analiza resumenes estadisticos y ayuda a redactar conclusiones. Puedes usar OpenAI, Gemini o un proveedor compatible.")
    provider = st.radio("Proveedor IA", ["Gemini", "OpenAI", "OpenRouter / compatible"], horizontal=True)
    default_models = {
        "Gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "OpenAI": ["gpt-5.5", "gpt-5.2"],
        "OpenRouter / compatible": ["google/gemini-2.5-flash", "openai/gpt-5.2", "anthropic/claude-sonnet-4.5"],
    }
    env_names = {
        "Gemini": "GEMINI_API_KEY",
        "OpenAI": "OPENAI_API_KEY",
        "OpenRouter / compatible": "OPENROUTER_API_KEY",
    }
    env_name = env_names[provider]
    try:
        secret_key = st.secrets.get(env_name, "")
    except Exception:
        secret_key = ""
    api_key = secret_key or os.getenv(env_name, "")
    base_url = "https://openrouter.ai/api/v1"
    with st.expander("Configurar clave del proveedor"):
        st.caption(f"Variable recomendada: {env_name}. Tambien puedes pegar la clave aqui solo para esta sesion.")
        typed_key = st.text_input(env_name, type="password", value="")
        if typed_key:
            api_key = typed_key
        if provider == "OpenRouter / compatible":
            base_url = st.text_input("Base URL compatible", value="https://openrouter.ai/api/v1")
        if provider == "Gemini":
            st.markdown("[Crear clave de Gemini en Google AI Studio](https://aistudio.google.com/app/apikey)")
        elif provider == "OpenAI":
            st.markdown("[Crear clave de OpenAI](https://platform.openai.com/api-keys)")
        else:
            st.markdown("[Crear clave de OpenRouter](https://openrouter.ai/keys)")
    model = st.selectbox("Modelo", default_models[provider], index=0)
    context = build_ai_context()
    c1, c2, c3 = st.columns(3)
    c1.metric("Productos", context["productos"])
    c2.metric("Mediciones", context["mediciones"])
    c3.metric("Inspecciones", context["inspecciones"])
    question = st.text_area(
        "Enfoque del informe",
        value="Analiza el estado general del proceso, indica si hay datos suficientes para graficos de control y redacta recomendaciones para el informe final.",
        height=120,
    )
    if st.button("Generar informe IA"):
        if not api_key:
            st.warning(f"Configura {env_name} para generar el informe automaticamente.")
            st.code(
                f"En PowerShell:\n$env:{env_name}=\"tu_api_key\"\n\nO en .streamlit/secrets.toml:\n{env_name} = \"tu_api_key\"",
                language="powershell",
            )
        else:
            with st.spinner("Generando analisis..."):
                try:
                    report = generate_ai_report(provider, api_key, model, context, question, base_url)
                    st.markdown(report)
                    st.download_button("Descargar informe IA", report, file_name="informe_ia_cep.md", mime="text/markdown")
                except Exception as exc:
                    st.error(friendly_ai_error(exc))
                    with st.expander("Detalle tecnico"):
                        st.code(str(exc))
    with st.expander("Ver resumen enviado a la IA"):
        st.json(context)

elif page == "Exportar":
    section_header("Exportacion a Excel", "Descarga catalogos, mediciones, inspecciones, importaciones y datos planos")
    importaciones = load_datos_importados()
    frames = {
        "productos": productos,
        "variables": variables,
        "atributos": atributos,
        "mediciones": mediciones,
        "inspecciones": inspecciones,
        "datos_importados": importaciones,
    }
    st.download_button(
        "Descargar Excel",
        data=excel_bytes(frames),
        file_name="cep_frutas_hortalizas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
