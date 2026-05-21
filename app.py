import io
import math
import os
import re
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
        .stApp {
            background:
                linear-gradient(180deg, #f7fafc 0%, #eef4f7 42%, #f8fafc 100%);
        }
        .cep-welcome {
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: grid;
            place-items: center;
            background:
                linear-gradient(135deg, #071827 0%, #0b3552 54%, #0f6b73 100%);
            animation: cepIntro 2.4s ease forwards;
            pointer-events: none;
        }
        .cep-welcome-card {
            width: min(520px, calc(100vw - 42px));
            padding: 2.2rem 2rem;
            text-align: center;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, .24);
            background: rgba(255, 255, 255, .08);
            box-shadow: 0 28px 80px rgba(0, 0, 0, .28);
            backdrop-filter: blur(14px);
        }
        .cep-welcome-card img {
            width: 108px;
            height: 108px;
            object-fit: contain;
            background: rgba(255, 255, 255, .96);
            padding: .7rem;
            border-radius: 50%;
            margin-bottom: 1rem;
        }
        .cep-welcome-card h2 {
            margin: 0;
            color: #ffffff;
            font-size: 1.55rem;
            letter-spacing: 0;
        }
        .cep-welcome-card p {
            margin: .55rem 0 1.35rem;
            color: rgba(255, 255, 255, .78);
        }
        .cep-loader {
            width: 100%;
            height: 4px;
            border-radius: 99px;
            background: rgba(255, 255, 255, .18);
            overflow: hidden;
        }
        .cep-loader::after {
            content: "";
            display: block;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, #f5c451, #54d39a, #75c8ff);
            transform-origin: left center;
            animation: cepLoad 1.8s ease-out forwards;
        }
        @keyframes cepIntro {
            0%, 72% { opacity: 1; visibility: visible; }
            100% { opacity: 0; visibility: hidden; }
        }
        @keyframes cepLoad {
            from { transform: scaleX(.08); }
            to { transform: scaleX(1); }
        }
        .cep-hero {
            background:
                linear-gradient(135deg, #082033 0%, #0b4f74 58%, #19736f 100%);
            border-radius: 8px;
            padding: 1.35rem 1.45rem;
            box-shadow: 0 20px 50px rgba(8, 32, 51, .18);
        }
        .cep-hero::after {
            display: none;
        }
        .cep-hero-badge {
            border-radius: 8px;
            color: #082033;
            box-shadow: 0 8px 20px rgba(0, 0, 0, .08);
        }
        .cep-nav {
            border-radius: 8px;
            background: rgba(255, 255, 255, .96);
            box-shadow: 0 16px 34px rgba(8, 32, 51, .08);
        }
        .cep-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .9rem;
            margin: .65rem 0 1rem;
        }
        .cep-kpi {
            min-height: 116px;
            background: #ffffff;
            border: 1px solid #d9e4ec;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 12px 26px rgba(8, 32, 51, .06);
        }
        .cep-kpi-label {
            color: #64748b;
            font-size: .82rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .06em;
        }
        .cep-kpi-value {
            margin-top: .45rem;
            color: #0f172a;
            font-size: 2rem;
            line-height: 1;
            font-weight: 900;
        }
        .cep-kpi-detail {
            margin-top: .6rem;
            color: #475569;
            font-size: .9rem;
        }
        .cep-surface {
            background: rgba(255, 255, 255, .94);
            border: 1px solid #d9e4ec;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 14px 32px rgba(8, 32, 51, .06);
            margin-bottom: 1rem;
        }
        .cep-status-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .75rem;
        }
        .cep-status {
            border: 1px solid #d9e4ec;
            border-radius: 8px;
            padding: .85rem;
            background: #f8fafc;
        }
        .cep-status strong {
            display: block;
            color: #0f172a;
            font-size: .96rem;
        }
        .cep-status span {
            display: block;
            color: #64748b;
            margin-top: .25rem;
            font-size: .88rem;
        }
        .cep-status.ok {
            border-color: #9bd6b5;
            background: #f0fbf5;
        }
        .cep-status.warn {
            border-color: #f0c36d;
            background: #fff8e8;
        }
        .cep-action-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .75rem;
            margin: .55rem 0 1rem;
        }
        .cep-progress {
            height: 9px;
            border-radius: 99px;
            background: #e5edf3;
            overflow: hidden;
            margin-top: .55rem;
        }
        .cep-progress span {
            display: block;
            height: 100%;
            width: var(--progress);
            background: linear-gradient(90deg, #0b4f74, #20a06b);
        }
        .cep-table-note {
            color: #64748b;
            font-size: .88rem;
            margin-top: -.35rem;
            margin-bottom: .6rem;
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
            .cep-kpi-grid,
            .cep-status-grid,
            .cep-action-grid {
                grid-template-columns: 1fr;
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


def welcome_screen():
    if st.session_state.get("welcome_seen"):
        return
    st.session_state.welcome_seen = True
    st.markdown(
        f"""
        <div class="cep-welcome">
            <div class="cep-welcome-card">
                <img src="{UNIMAG_ESCUDO_URL}" alt="Escudo Universidad del Magdalena">
                <h2>Universidad del Magdalena</h2>
                <p>Control Estadistico de Procesos para frutas y hortalizas</p>
                <div class="cep-loader"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_header():
    st.markdown(
        f"""
        <div class="cep-hero">
            <img src="{UNIMAG_ESCUDO_URL}" alt="Escudo Universidad del Magdalena">
            <div>
                <h1>Control Estadistico de Procesos</h1>
                <p>Operacion academica y tecnica para monitoreo de calidad, trazabilidad, capacidad, Pareto e informes asistidos por IA.</p>
            </div>
            <div class="cep-hero-badge">Universidad del Magdalena</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, detail):
    st.markdown(
        f"""
        <div class="cep-kpi">
            <div class="cep-kpi-label">{label}</div>
            <div class="cep-kpi-value">{value}</div>
            <div class="cep-kpi-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_card(title, detail, ok=True):
    klass = "ok" if ok else "warn"
    st.markdown(
        f"""
        <div class="cep-status {klass}">
            <strong>{title}</strong>
            <span>{detail}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def progress_bar(value):
    bounded = max(0, min(100, float(value)))
    st.markdown(f"<div class='cep-progress' style='--progress:{bounded:.0f}%'><span></span></div>", unsafe_allow_html=True)


def secret_or_env(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return value or os.getenv(name, "")


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


def query_table(table, columns="*", order=None):
    q = sb.table(table).select(columns)
    if order:
        q = q.order(order)
    try:
        return q.execute().data or []
    except Exception as exc:
        st.error(f"No se pudo leer la tabla '{table}'. Ejecuta primero schema_supabase.sql en Supabase SQL Editor.")
        st.exception(exc)
        st.stop()


def insert_row(table, payload):
    try:
        return sb.table(table).insert(payload).execute()
    except Exception as exc:
        st.error(f"No se pudo guardar en la tabla '{table}'. Revisa las politicas RLS y que el SQL del esquema este aplicado.")
        st.exception(exc)
        st.stop()


def insert_rows(table, payloads):
    if not payloads:
        return None
    try:
        return sb.table(table).insert(payloads).execute()
    except Exception as exc:
        st.error(f"No se pudo guardar en la tabla '{table}'. Revisa las politicas RLS y que el SQL del esquema este aplicado.")
        st.exception(exc)
        st.stop()


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


def ensure_producto(nombre, tipo, productos_df):
    nombre = str(nombre).strip()
    tipo = str(tipo).strip() if str(tipo).strip() in ["Fruta", "Hortaliza", "Otro"] else "Otro"
    match = productos_df[productos_df["nombre"].str.lower() == nombre.lower()] if not productos_df.empty else pd.DataFrame()
    if not match.empty:
        return match.iloc[0]["id"], productos_df
    row = insert_row("productos", {"nombre": nombre, "tipo": tipo}).data[0]
    productos_df = pd.concat([productos_df, pd.DataFrame([row])], ignore_index=True)
    return row["id"], productos_df


def ensure_variable(producto_id, nombre_variable, unidad, variables_df):
    nombre_variable = str(nombre_variable).strip()
    unidad = str(unidad).strip()
    match = variables_df[
        (variables_df["producto_id"] == producto_id)
        & (variables_df["nombre_variable"].str.lower() == nombre_variable.lower())
    ] if not variables_df.empty else pd.DataFrame()
    if not match.empty:
        return match.iloc[0]["id"], variables_df
    row = insert_row(
        "variables_continuas",
        {"producto_id": producto_id, "nombre_variable": nombre_variable, "unidad": unidad},
    ).data[0]
    variables_df = pd.concat([variables_df, pd.DataFrame([row])], ignore_index=True)
    return row["id"], variables_df


def ensure_atributo(producto_id, nombre_atributo, tipo_inspeccion, atributos_df):
    nombre_atributo = str(nombre_atributo).strip()
    tipo_inspeccion = str(tipo_inspeccion).strip().lower()
    tipo_inspeccion = tipo_inspeccion if tipo_inspeccion in ["p", "np", "c", "u"] else "p"
    match = atributos_df[
        (atributos_df["producto_id"] == producto_id)
        & (atributos_df["nombre_atributo"].str.lower() == nombre_atributo.lower())
    ] if not atributos_df.empty else pd.DataFrame()
    if not match.empty:
        return match.iloc[0]["id"], atributos_df
    row = insert_row(
        "atributos",
        {"producto_id": producto_id, "nombre_atributo": nombre_atributo, "tipo_inspeccion": tipo_inspeccion},
    ).data[0]
    atributos_df = pd.concat([atributos_df, pd.DataFrame([row])], ignore_index=True)
    return row["id"], atributos_df


def parse_csv_input(uploaded_file, pasted_text):
    if uploaded_file is not None:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)
    if pasted_text and pasted_text.strip():
        return pd.read_csv(io.StringIO(pasted_text.strip()))
    return pd.DataFrame()


def bulk_load_continuous(df):
    required = {"subgrupo", "producto", "tipo_producto", "variable", "unidad", "fecha_hora", "analista", "lote", "valor"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Faltan columnas: {', '.join(sorted(missing))}")
        return
    productos_df = load_productos().copy()
    variables_df = load_variables().copy()
    created_subgroups = 0
    created_values = 0
    group_cols = ["subgrupo", "producto", "tipo_producto", "variable", "unidad", "fecha_hora", "analista", "lote"]
    for keys, group in df.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, keys))
        producto_id, productos_df = ensure_producto(record["producto"], record["tipo_producto"], productos_df)
        variable_id, variables_df = ensure_variable(producto_id, record["variable"], record["unidad"], variables_df)
        values = pd.to_numeric(group["valor"], errors="coerce").dropna().tolist()
        if not values:
            continue
        subgrupo = insert_row(
            "subgrupos",
            {
                "producto_id": producto_id,
                "fecha_hora": pd.to_datetime(record["fecha_hora"]).isoformat(),
                "analista": str(record["analista"]).strip(),
                "lote": str(record["lote"]).strip(),
                "tamano_muestra": len(values),
            },
        ).data[0]
        insert_rows(
            "mediciones",
            [{"subgrupo_id": subgrupo["id"], "variable_id": variable_id, "valor": float(value)} for value in values],
        )
        created_subgroups += 1
        created_values += len(values)
    clear_cache()
    st.success(f"Carga continua completada: {created_subgroups} subgrupos y {created_values} mediciones.")


def bulk_load_attributes(df):
    required = {
        "subgrupo",
        "producto",
        "tipo_producto",
        "atributo",
        "tipo_inspeccion",
        "fecha_hora",
        "analista",
        "lote",
        "unidades_inspeccionadas",
        "no_conformes",
    }
    missing = required - set(df.columns)
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
        unidades = int(row["unidades_inspeccionadas"])
        no_conformes = int(row["no_conformes"])
        no_conformes = max(0, min(no_conformes, unidades))
        subgrupo = insert_row(
            "subgrupos",
            {
                "producto_id": producto_id,
                "fecha_hora": pd.to_datetime(row["fecha_hora"]).isoformat(),
                "analista": str(row["analista"]).strip(),
                "lote": str(row["lote"]).strip(),
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


apply_design()

welcome_screen()
hero_header()

productos = load_productos()
variables = load_variables()
atributos = load_atributos()
mediciones = flatten_mediciones(load_mediciones())
inspecciones = flatten_inspecciones(load_inspecciones())

pages = [
    "Panel",
    "Catalogos",
    "Registro continuo",
    "Registro atributos",
    "Graficos de control",
    "Capacidad",
    "Pareto",
    "Inspeccion y muestreo",
    "Carga masiva",
    "Trazabilidad",
    "Exportar",
    "Informe IA",
]
st.markdown("<div class='cep-nav'>", unsafe_allow_html=True)
if "current_page" not in st.session_state:
    st.session_state.current_page = "Panel"
if "nav_target" in st.session_state:
    st.session_state.current_page = st.session_state.pop("nav_target")
if hasattr(st, "pills"):
    selected_page = st.pills(
        "Modulo",
        pages,
        default=st.session_state.current_page if st.session_state.current_page in pages else "Panel",
        selection_mode="single",
        label_visibility="collapsed",
        key=f"nav_{st.session_state.current_page}",
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
    section_header("Centro de control", "Estado operativo, cobertura analitica y accesos principales")
    productos_filtro = ["Todos"] + sorted(productos["nombre"].dropna().unique()) if not productos.empty else ["Todos"]
    producto_filtro = st.selectbox("Producto en dashboard", productos_filtro)
    mediciones_dash = mediciones.copy()
    inspecciones_dash = inspecciones.copy()
    if producto_filtro != "Todos":
        mediciones_dash = mediciones_dash[mediciones_dash["producto"] == producto_filtro] if not mediciones_dash.empty else mediciones_dash
        inspecciones_dash = inspecciones_dash[inspecciones_dash["producto"] == producto_filtro] if not inspecciones_dash.empty else inspecciones_dash

    subgrupos_df = load_subgrupos()
    subgrupos_continuos = mediciones_dash["subgrupo_id"].nunique() if not mediciones_dash.empty else 0
    subgrupos_atributos = inspecciones_dash["subgrupo_id"].nunique() if not inspecciones_dash.empty else 0
    no_conformes = int(inspecciones_dash["no_conforma"].sum()) if not inspecciones_dash.empty else 0
    tasa_no_conforme = no_conformes / max(len(inspecciones_dash), 1)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Productos", len(productos), f"{len(variables)} variables y {len(atributos)} atributos")
    with k2:
        kpi_card("Subgrupos", len(subgrupos_df), f"{subgrupos_continuos} continuos / {subgrupos_atributos} atributos")
    with k3:
        kpi_card("Mediciones", len(mediciones_dash), "Registros continuos filtrados")
    with k4:
        kpi_card("No conformidad", f"{tasa_no_conforme:.1%}", f"{no_conformes} eventos sobre {len(inspecciones_dash)} inspecciones")

    st.markdown("<div class='cep-surface'>", unsafe_allow_html=True)
    section_header("Salud de la plataforma", "APIs, graficas y navegacion")
    supabase_ok = bool(secret_or_env("SUPABASE_URL") and secret_or_env("SUPABASE_KEY"))
    ai_keys = [name for name in ["OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"] if secret_or_env(name)]
    st.markdown("<div class='cep-status-grid'>", unsafe_allow_html=True)
    status_card("Supabase conectado", "URL y key disponibles para lectura/escritura" if supabase_ok else "Falta SUPABASE_URL o SUPABASE_KEY", supabase_ok)
    status_card("Graficas activas", "Plotly cargado y listo para control, capacidad y Pareto", True)
    status_card("IA opcional", f"{len(ai_keys)} proveedor(es) configurado(s)" if ai_keys else "Sin API key IA; el resto de la app funciona", bool(ai_keys))
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='cep-action-grid'>", unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    if a1.button("Registrar continuo", use_container_width=True):
        st.session_state.nav_target = "Registro continuo"
        st.rerun()
    if a2.button("Registrar atributos", use_container_width=True):
        st.session_state.nav_target = "Registro atributos"
        st.rerun()
    if a3.button("Ver graficos", use_container_width=True):
        st.session_state.nav_target = "Graficos de control"
        st.rerun()
    if a4.button("Exportar Excel", use_container_width=True):
        st.session_state.nav_target = "Exportar"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if productos.empty:
        note("La base esta conectada, pero todavia no hay datos. Puedes crear catalogos manualmente o cargar un conjunto demo para probar todos los analisis.")
        if st.button("Cargar datos demo para verificar analisis"):
            seed_demo_dataset()
            st.rerun()

    ready_frames = []
    if not mediciones_dash.empty:
        ready_frames.append(
            mediciones_dash.groupby(["producto", "nombre_variable"], dropna=False)["subgrupo_id"]
            .nunique()
            .reset_index(name="subgrupos")
            .rename(columns={"nombre_variable": "analisis"})
            .assign(tipo="Variable")
        )
    if not inspecciones_dash.empty:
        ready_frames.append(
            inspecciones_dash.groupby(["producto", "nombre_atributo"], dropna=False)["subgrupo_id"]
            .nunique()
            .reset_index(name="subgrupos")
            .rename(columns={"nombre_atributo": "analisis"})
            .assign(tipo="Atributo")
        )
    ready_all = pd.concat(ready_frames, ignore_index=True) if ready_frames else pd.DataFrame()
    if not ready_all.empty:
        ready_all["avance"] = (ready_all["subgrupos"] / MIN_SUBGROUPS * 100).clip(upper=100)
        ready_all["estado"] = np.where(ready_all["subgrupos"] >= MIN_SUBGROUPS, "Listo", "Faltan datos")
        coverage = float((ready_all["estado"] == "Listo").mean() * 100)
    else:
        coverage = 0

    c5, c6 = st.columns([1.08, .92])
    with c5:
        section_header("Preparacion analitica", f"Meta minima: {MIN_SUBGROUPS} subgrupos por grafico")
        if not ready_all.empty:
            fig = px.bar(
                ready_all.sort_values("subgrupos", ascending=True),
                x="subgrupos",
                y="analisis",
                color="tipo",
                orientation="h",
                text="estado",
            )
            fig.add_vline(x=MIN_SUBGROUPS, line_dash="dash", line_color="#D17900", annotation_text="Meta")
            fig.update_layout(title="Cobertura por variable y atributo", xaxis_title="Subgrupos", yaxis_title="")
            st.plotly_chart(style_chart(fig, height=390), width="stretch")
            st.markdown(f"<div class='cep-table-note'>Cobertura lista para analisis formal: {coverage:.0f}%</div>", unsafe_allow_html=True)
            progress_bar(coverage)
        else:
            empty_state("Aun no hay datos para calcular preparacion analitica.")
    with c6:
        section_header("Actividad reciente", "Ultimos registros capturados")
        recent_frames = []
        if not mediciones_dash.empty:
            recent_frames.append(
                mediciones_dash[["fecha_hora", "producto", "nombre_variable", "analista", "lote"]]
                .drop_duplicates()
                .assign(fuente="Medicion", detalle=lambda d: d["nombre_variable"])
                [["fecha_hora", "fuente", "producto", "detalle", "analista", "lote"]]
            )
        if not inspecciones_dash.empty:
            recent_frames.append(
                inspecciones_dash[["fecha_hora", "producto", "nombre_atributo", "analista", "lote"]]
                .drop_duplicates()
                .assign(fuente="Inspeccion", detalle=lambda d: d["nombre_atributo"])
                [["fecha_hora", "fuente", "producto", "detalle", "analista", "lote"]]
            )
        recent = pd.concat(recent_frames, ignore_index=True).sort_values("fecha_hora", ascending=False).head(8) if recent_frames else pd.DataFrame()
        if not recent.empty:
            st.dataframe(recent, width="stretch", hide_index=True)
        else:
            empty_state("Aun no hay actividad reciente.")

    c7, c8 = st.columns(2)
    with c7:
        section_header("Volumen continuo", "Mediciones por producto y variable")
        if not mediciones_dash.empty:
            fig = px.histogram(mediciones_dash, x="producto", color="nombre_variable", barmode="group")
            fig.update_layout(title="Mediciones continuas capturadas", xaxis_title="Producto", yaxis_title="Mediciones")
            st.plotly_chart(style_chart(fig), width="stretch")
        else:
            empty_state("Aun no hay mediciones continuas.")
    with c8:
        section_header("No conformidades", "Defectos priorizados por atributo")
        if not inspecciones_dash.empty:
            pareto = inspecciones_dash.groupby("nombre_atributo", as_index=False)["no_conforma"].sum().sort_values("no_conforma", ascending=False)
            fig = px.bar(pareto, x="nombre_atributo", y="no_conforma", color="nombre_atributo")
            fig.update_layout(title="Frecuencia de no conformidades", xaxis_title="Atributo", yaxis_title="No conformidades", showlegend=False)
            st.plotly_chart(style_chart(fig), width="stretch")
        else:
            empty_state("Aun no hay inspecciones por atributos.")

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

elif page == "Carga masiva":
    section_header("Carga masiva", "Agrega datos a Supabase desde CSV sin entrar registro por registro")
    note("Esta pantalla inserta datos directamente en las mismas tablas de Supabase. Si el producto, variable o atributo no existe, la app lo crea automaticamente.")
    modo_carga = st.radio("Tipo de carga", ["Continuos", "Atributos"], horizontal=True)
    if modo_carga == "Continuos":
        ejemplo = """subgrupo,producto,tipo_producto,variable,unidad,fecha_hora,analista,lote,valor
1,Mango Tommy,Fruta,Peso,g,2026-05-19 08:00,Ana,L-001,421.4
1,Mango Tommy,Fruta,Peso,g,2026-05-19 08:00,Ana,L-001,419.8
1,Mango Tommy,Fruta,Peso,g,2026-05-19 08:00,Ana,L-001,423.1
2,Mango Tommy,Fruta,Peso,g,2026-05-19 09:00,Ana,L-002,420.6
2,Mango Tommy,Fruta,Peso,g,2026-05-19 09:00,Ana,L-002,418.9"""
        st.caption("Formato: cada fila es una medicion. Varias filas con el mismo subgrupo forman un subgrupo racional.")
    else:
        ejemplo = """subgrupo,producto,tipo_producto,atributo,tipo_inspeccion,fecha_hora,analista,lote,unidades_inspeccionadas,no_conformes
1,Mango Tommy,Fruta,Manchas,p,2026-05-19 08:00,Ana,L-001,30,3
2,Mango Tommy,Fruta,Manchas,p,2026-05-19 09:00,Ana,L-002,30,1
3,Mango Tommy,Fruta,Golpes,u,2026-05-19 10:00,Carlos,L-003,30,2"""
        st.caption("Formato: cada fila es un subgrupo de inspeccion.")
    with st.expander("Ver ejemplo de CSV"):
        st.code(ejemplo, language="csv")
    uploaded = st.file_uploader("Subir archivo CSV", type=["csv"], key=f"upload_{modo_carga}")
    pasted = st.text_area("O pega el CSV aqui", height=190, placeholder=ejemplo)
    preview = parse_csv_input(uploaded, pasted)
    if not preview.empty:
        st.dataframe(preview.head(30), width="stretch", hide_index=True)
    if st.button("Cargar a Supabase"):
        data = parse_csv_input(uploaded, pasted)
        if data.empty:
            st.warning("Sube o pega un CSV antes de cargar.")
        elif modo_carga == "Continuos":
            bulk_load_continuous(data)
            st.rerun()
        else:
            bulk_load_attributes(data)
            st.rerun()

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
    section_header("Exportacion a Excel", "Descarga catalogos, mediciones, inspecciones y datos planos")
    frames = {
        "productos": productos,
        "variables": variables,
        "atributos": atributos,
        "mediciones": mediciones,
        "inspecciones": inspecciones,
    }
    st.download_button(
        "Descargar Excel",
        data=excel_bytes(frames),
        file_name="cep_frutas_hortalizas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
