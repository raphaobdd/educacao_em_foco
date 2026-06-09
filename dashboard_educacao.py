"""
Dashboard — Educação Superior · Região de Campinas/SP
Baseado no projeto integrado com MongoDB Atlas
Execute: streamlit run dashboard_educacao.py
"""

import math
import unicodedata
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pymongo import MongoClient

warnings.filterwarnings("ignore")

# ─── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Educação Superior em Foco",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Paleta de cores ───────────────────────────────────────────────────────────
COR_PUBLICA  = "#1D9E75"
COR_PRIVADA  = "#7F77DD"
COR_ACCENT   = "#EF9F27"
COR_DANGER   = "#D85A30"
CORES_REDE   = [COR_PUBLICA, COR_PRIVADA]
CORES_CUSTO  = {"Gratuito": COR_PUBLICA, "Moderado": COR_ACCENT, "Alto": COR_DANGER}

# ─── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    [data-testid="stSidebar"] { background-color: #1a1d2e; }
    .metric-card {
        background: linear-gradient(135deg, #1a1d2e 0%, #252840 100%);
        border: 1px solid #2d3153;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #1D9E75; }
    .metric-label { font-size: 0.85rem; color: #8a8fa8; margin-top: 4px; }
    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #c8cbdf;
        border-left: 3px solid #1D9E75; padding-left: 10px;
        margin: 12px 0;
    }
    .stPlotlyChart { border-radius: 12px; }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1d2e, #252840);
        border: 1px solid #2d3153;
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Helpers ───────────────────────────────────────────────────────────────────
def rm_acc(s: str) -> str:
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().upper()

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c8cbdf", family="Inter, sans-serif"),
    margin=dict(l=16, r=16, t=50, b=16),
    title_font=dict(size=15, color="#e8eaf6"),
)

# ─── Conexão MongoDB (cached) ─────────────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando ao MongoDB…")
def get_db():
    if "MONGO_URI" in st.session_state:
        uri = st.session_state["MONGO_URI"]
    else:
        try:
            uri = st.secrets["MONGO_URI"]
        except Exception:
            raise Exception(
                "MONGO_URI não encontrada nem na Sidebar nem no secrets.toml"
            )

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=8000
    )
    return client["educacao_superior"]

# ─── Carregamento de dados (TTL = 5 min para simular "tempo real") ─────────────
@st.cache_data(ttl=300, show_spinner="Carregando dados…")
def carregar_dados():
    db = get_db()
    col_ies      = db["ies_info"]
    col_docentes = db["docentes_indicadores"]
    col_cursos   = db["cursos_relacionados"]
    col_perfil   = db["ies_perfil_estudante"]

    df_ies      = pd.DataFrame(list(col_ies.find({}, {"_id": 0})))
    df_docentes = pd.DataFrame(list(col_docentes.find({}, {"_id": 0})))
    df_cursos   = pd.DataFrame(list(col_cursos.find({}, {"_id": 0})))
    df_perfil   = pd.DataFrame(list(col_perfil.find({}, {"_id": 0})))

    # Normaliza localização embutida
    if "localizacao" in df_ies.columns:
        df_ies["uf"]        = df_ies["localizacao"].apply(lambda x: x.get("uf")   if isinstance(x, dict) else None)
        df_ies["municipio"] = df_ies["localizacao"].apply(lambda x: x.get("municipio") if isinstance(x, dict) else None)
        df_ies.drop(columns=["localizacao"], inplace=True)

    for df in [df_ies, df_docentes, df_cursos, df_perfil]:
        if "co_ies" in df.columns:
            df["co_ies"] = pd.to_numeric(df["co_ies"], errors="coerce")

    # Percentuais: converte 0-1 → 0-100 se necessário
    for col in ["perc_doutores", "perc_qualificados"]:
        if col in df_docentes.columns:
            df_docentes[col] = pd.to_numeric(df_docentes[col], errors="coerce")
            if df_docentes[col].max() <= 1.01:
                df_docentes[col] = (df_docentes[col] * 100).round(2)

    return df_ies, df_docentes, df_cursos, df_perfil

# ─── Coordenadas base ──────────────────────────────────────────────────────────
COORDS = {
    "CAMPINAS": (-22.9056, -47.0608), "AMERICANA": (-22.7388, -47.3310),
    "SUMARE": (-22.8218, -47.2671), "SANTA BARBARA D'OESTE": (-22.7539, -47.4144),
    "NOVA ODESSA": (-22.7803, -47.2956), "HORTOLÂNDIA": (-22.8584, -47.2200),
    "HORTOLANDIA": (-22.8584, -47.2200), "INDAIATUBA": (-23.0905, -47.2189),
    "VALINHOS": (-22.9733, -46.9939), "VINHEDO": (-23.0300, -46.9165),
    "JAGUARIUNA": (-22.6956, -46.9853), "HOLAMBRA": (-22.6400, -47.0608),
    "COSMOPOLIS": (-22.6453, -47.1967), "ARTHUR NOGUEIRA": (-22.5656, -47.0058),
    "ENGENHEIRO COELHO": (-22.4867, -47.1783), "PAULINIA": (-22.7642, -47.1528),
    "ITATIBA": (-23.0026, -46.8383), "ATIBAIA": (-23.1178, -46.5539),
    "BRAGANCA PAULISTA": (-22.9514, -46.5412), "AMPARO": (-22.7014, -46.7672),
    "MONTE MOR": (-22.9364, -47.3189), "CAPIVARI": (-22.9961, -47.5083),
    "CHARQUEADA": (-22.5086, -47.7767), "PIRACICABA": (-22.7253, -47.6492),
    "LIMEIRA": (-22.4456, -47.4014), "ARARAS": (-22.3219, -47.3839),
    "LEME": (-22.1897, -47.3897), "RIO CLARO": (-22.4149, -47.5647),
    "SAO PEDRO": (-22.5494, -47.9136), "MOGI MIRIM": (-22.4322, -46.9567),
    "MOGI GUACU": (-22.3703, -46.9428), "ESPIRITO SANTO DO PINHAL": (-22.1942, -46.7431),
    "JUNDIAI": (-23.1861, -46.8844), "ITAPIRA": (-22.4361, -46.8239),
    "PEDREIRA": (-22.7414, -46.9011), "MORUNGABA": (-22.8961, -46.8650),
    "SAO PAULO": (-23.5505, -46.6333), "SOROCABA": (-23.5015, -47.4526),
}

REF_LAT, REF_LON = -22.9056, -47.0608

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

def get_coords(municipio):
    if not municipio or pd.isna(municipio):
        return None, None
    key = rm_acc(str(municipio)).strip()
    for ck, coords in COORDS.items():
        if ck == key or ck in key or key in ck:
            return coords
    return None, None

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## 🎓 Educação Superior")
st.sidebar.markdown("**Região de Campinas / SP**")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🔄 Atualização")
auto_refresh = st.sidebar.checkbox("Auto-refresh (5 min)", value=False)
if st.sidebar.button("🔁 Atualizar dados agora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Conexão MongoDB")
mongo_uri = st.sidebar.text_input(
    "URI (opcional)",
    type="password",
    placeholder="mongodb+srv://…",
    help="Deixe em branco para usar a URI padrão do projeto",
)
if mongo_uri:
    st.session_state["MONGO_URI"] = mongo_uri

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Fonte dos Dados")
st.sidebar.markdown(
    "- **INEP** — Censo da Educação Superior 2022–2024\n"
    "- **SEADE** — Dados socioeconômicos\n"
    "- **ODS 4** — Educação de Qualidade"
)

# ─── Carrega dados ─────────────────────────────────────────────────────────────
try:
    df_ies, df_docentes, df_cursos, df_perfil = carregar_dados()
    db_ok = True
except Exception as e:
    st.error(f"❌ Não foi possível conectar ao MongoDB: {e}")
    st.info("Verifique a URI de conexão na barra lateral ou em `st.secrets`.")
    st.stop()

# ─── Merge auxiliar ────────────────────────────────────────────────────────────
mun_col = next((c for c in ["municipio", "no_municipio_ies"] if c in df_ies.columns), None)

df_merge = df_ies.merge(
    df_docentes[["co_ies", "perc_doutores", "perc_qualificados", "total_docentes"]]
    .groupby("co_ies").mean().reset_index(),
    on="co_ies", how="left"
) if "co_ies" in df_ies.columns and "co_ies" in df_docentes.columns else df_ies.copy()

# ── Filtros da Sidebar ─────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros")

redes_disp = sorted(df_ies["rede"].dropna().unique().tolist()) if "rede" in df_ies.columns else []
redes_sel  = st.sidebar.multiselect("Rede", redes_disp, default=redes_disp)

orgs_disp  = sorted(df_ies["organizacao"].dropna().unique().tolist()) if "organizacao" in df_ies.columns else []
orgs_sel   = st.sidebar.multiselect("Organização acadêmica", orgs_disp, default=orgs_disp)

if "score_atratividade" in df_perfil.columns:
    score_min, score_max = st.sidebar.slider(
        "Score de Atratividade", 0.0, 100.0, (0.0, 100.0), step=1.0
    )
else:
    score_min, score_max = 0.0, 100.0

# Aplica filtros
mask = pd.Series(True, index=df_ies.index)
if redes_sel and "rede" in df_ies.columns:
    mask &= df_ies["rede"].isin(redes_sel)
if orgs_sel and "organizacao" in df_ies.columns:
    mask &= df_ies["organizacao"].isin(orgs_sel)

df_f = df_ies[mask].copy()
df_perf_f = df_perfil[df_perfil["co_ies"].isin(df_f["co_ies"])] if "co_ies" in df_perfil.columns else df_perfil

# ══════════════════════════════════════════════════════════════════════════════
# CABEÇALHO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# 🎓 Dashboard — Educação Superior")
st.markdown("### Região de Campinas / SP &nbsp;|&nbsp; Censo INEP 2022–2024")
st.markdown("---")

# ─── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

total_ies      = df_f["co_ies"].nunique() if "co_ies" in df_f else len(df_f)
total_cursos   = len(df_cursos[df_cursos["co_ies"].isin(df_f["co_ies"])]) if "co_ies" in df_cursos.columns else len(df_cursos)
perc_pub       = (df_f["rede"].value_counts(normalize=True).get("Pública", 0) * 100) if "rede" in df_f else 0
med_dout       = df_docentes["perc_doutores"].mean() if "perc_doutores" in df_docentes.columns else 0
med_score      = df_perf_f["score_atratividade"].mean() if "score_atratividade" in df_perf_f.columns else 0

k1.metric("🏛️ Instituições", f"{total_ies:,}")
k2.metric("📚 Cursos", f"{total_cursos:,}")
k3.metric("🏛️ % Pública", f"{perc_pub:.1f}%")
k4.metric("🎓 % Doutores (média)", f"{med_dout:.1f}%")
k5.metric("⭐ Score Médio", f"{med_score:.1f}")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# LINHA 1 — Pizza + Barras grau
# ══════════════════════════════════════════════════════════════════════════════
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-title">Distribuição por Rede</div>', unsafe_allow_html=True)
    if "rede" in df_f.columns:
        df_g1 = df_f["rede"].value_counts().reset_index()
        df_g1.columns = ["Rede", "Quantidade"]
        fig1 = px.pie(
            df_g1, names="Rede", values="Quantidade",
            color_discrete_sequence=CORES_REDE, hole=0.42,
        )
        fig1.update_traces(textposition="outside", textinfo="percent+label+value", pull=[0.05] * len(df_g1))
        fig1.update_layout(**LAYOUT_BASE)
        st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown('<div class="section-title">Cursos por Grau Acadêmico</div>', unsafe_allow_html=True)
    if "grau_academico" in df_cursos.columns:
        df_g2 = df_cursos[df_cursos["co_ies"].isin(df_f["co_ies"])]["grau_academico"].value_counts().reset_index()
        df_g2.columns = ["Grau", "Quantidade"]
        fig2 = px.bar(
            df_g2, x="Grau", y="Quantidade", color="Grau",
            color_discrete_sequence=[COR_PRIVADA, COR_PUBLICA, COR_ACCENT], text="Quantidade",
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(**LAYOUT_BASE, showlegend=False,
                           xaxis=dict(gridcolor="#2a2d3e"), yaxis=dict(gridcolor="#2a2d3e"))
        st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# LINHA 2 — Grau × Rede + Top 15 cursos
# ══════════════════════════════════════════════════════════════════════════════
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="section-title">Graus Acadêmicos por Rede</div>', unsafe_allow_html=True)
    if "grau_academico" in df_cursos.columns and "rede" in df_ies.columns:
        df_gc = df_cursos.merge(df_ies[["co_ies", "rede"]], on="co_ies", how="left")
        df_g3 = df_gc.groupby(["grau_academico", "rede"]).size().reset_index(name="Quantidade")
        df_g3.columns = ["Grau", "Rede", "Quantidade"]
        fig3 = px.bar(df_g3, x="Grau", y="Quantidade", color="Rede", barmode="group",
                      color_discrete_sequence=CORES_REDE, text="Quantidade")
        fig3.update_traces(textposition="outside")
        fig3.update_layout(**LAYOUT_BASE, xaxis=dict(gridcolor="#2a2d3e"), yaxis=dict(gridcolor="#2a2d3e"))
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown('<div class="section-title">Top 15 IES com Mais Cursos</div>', unsafe_allow_html=True)
    if "co_ies" in df_cursos.columns:
        top15 = (df_cursos[df_cursos["co_ies"].isin(df_f["co_ies"])]
                 .groupby("co_ies").size().reset_index(name="total_cursos")
                 .nlargest(15, "total_cursos")
                 .merge(df_ies[["co_ies", "nome", "rede"]], on="co_ies", how="left")
                 .sort_values("total_cursos"))
        fig4 = px.bar(top15, x="total_cursos", y="nome", color="rede", orientation="h",
                      color_discrete_sequence=CORES_REDE, text="total_cursos",
                      labels={"total_cursos": "Nº de Cursos", "nome": "IES"})
        fig4.update_traces(textposition="outside")
        fig4.update_layout(**LAYOUT_BASE, height=480,
                           yaxis={"categoryorder": "total ascending"},
                           xaxis=dict(gridcolor="#2a2d3e"))
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# LINHA 3 — Scatter qualificação docente + Top 20 Score
# ══════════════════════════════════════════════════════════════════════════════
col5, col6 = st.columns(2)

with col5:
    st.markdown('<div class="section-title">Qualificação Docente × Porte da IES</div>', unsafe_allow_html=True)
    df_g5 = df_docentes.merge(df_ies[["co_ies", "nome", "rede"]], on="co_ies", how="left")
    df_g5 = df_g5[df_g5["co_ies"].isin(df_f["co_ies"])]
    if "perc_doutores" in df_g5.columns and "total_docentes" in df_g5.columns:
        df_g5 = df_g5.dropna(subset=["perc_doutores", "total_docentes"])
        fig5 = px.scatter(
            df_g5, x="total_docentes", y="perc_doutores", color="rede",
            size="perc_qualificados" if "perc_qualificados" in df_g5.columns else None,
            hover_name="nome", opacity=0.8,
            color_discrete_sequence=CORES_REDE,
            labels={"total_docentes": "Total de Docentes", "perc_doutores": "% com Doutorado"},
        )
        fig5.update_layout(**LAYOUT_BASE,
                           xaxis=dict(gridcolor="#2a2d3e"), yaxis=dict(gridcolor="#2a2d3e"))
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("Dados de docentes insuficientes para este gráfico.")

with col6:
    st.markdown('<div class="section-title">Top 20 IES — Score de Atratividade</div>', unsafe_allow_html=True)
    if "score_atratividade" in df_perf_f.columns:
        df_g6 = (df_perf_f[df_perf_f["score_atratividade"] > 0]
                 .nlargest(20, "score_atratividade")
                 .sort_values("score_atratividade"))
        fig6 = px.bar(
            df_g6, x="score_atratividade", y="nome", color="rede", orientation="h",
            color_discrete_sequence=CORES_REDE, text="score_atratividade",
            hover_data=["categoria_custo"] if "categoria_custo" in df_g6.columns else None,
            labels={"score_atratividade": "Score (0–100)", "nome": "IES"},
        )
        fig6.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig6.update_layout(**LAYOUT_BASE, height=540, xaxis_range=[0, 115],
                           yaxis={"categoryorder": "total ascending"},
                           xaxis=dict(gridcolor="#2a2d3e"))
        st.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# LINHA 4 — Custo por Rede + Radar
# ══════════════════════════════════════════════════════════════════════════════
col7, col8 = st.columns(2)

with col7:
    st.markdown('<div class="section-title">Categorias de Custo por Rede</div>', unsafe_allow_html=True)
    if "categoria_custo" in df_perf_f.columns and "rede" in df_perf_f.columns:
        df_g7 = df_perf_f.groupby(["rede", "categoria_custo"]).size().reset_index(name="Total")
        df_g7.columns = ["Rede", "Custo", "Total"]
        fig7 = px.bar(
            df_g7, x="Rede", y="Total", color="Custo", barmode="group",
            color_discrete_map={"Gratuito": COR_PUBLICA, "Moderado": COR_ACCENT, "Alto": "#D85A30"},
            text="Total",
        )
        fig7.update_traces(textposition="outside")
        fig7.update_layout(**LAYOUT_BASE, yaxis=dict(gridcolor="#2a2d3e"))
        st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.markdown('<div class="section-title">Radar — Perfil Médio por Rede</div>', unsafe_allow_html=True)
    df_docentes_ag = (
        df_docentes
        .groupby("co_ies")
        .agg({
            "perc_doutores": "mean",
            "perc_qualificados": "mean"
        })
        .reset_index()
    )
    categorias_radar = ["Score Atrativ.", "% Doutores", "% Qualificados", "Score Custo", "Score Distância"]
    fig8 = go.Figure()
    for rede, cor in [("Pública", COR_PUBLICA), ("Privada", COR_PRIVADA)]:
        sub = df_perf_f[df_perf_f["rede"] == rede] if "rede" in df_perf_f.columns else pd.DataFrame()
        sub_doc = df_docentes_ag[df_docentes_ag["co_ies"].isin(sub["co_ies"])] if not sub.empty else pd.DataFrame()
        vals = [
            sub["score_atratividade"].mean()   if "score_atratividade" in sub.columns  and not sub.empty else 0,
            sub_doc["perc_doutores"].mean()     if "perc_doutores" in sub_doc.columns   and not sub_doc.empty else 0,
            sub_doc["perc_qualificados"].mean() if "perc_qualificados" in sub_doc.columns and not sub_doc.empty else 0,
            sub["score_custo"].mean()           if "score_custo" in sub.columns          and not sub.empty else 0,
            sub["score_distancia"].mean()       if "score_distancia" in sub.columns      and not sub.empty else 0,
        ]
        vals = [round(v, 1) if not (isinstance(v, float) and math.isnan(v)) else 0 for v in vals]
        fig8.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=categorias_radar + [categorias_radar[0]],
            fill="toself", name=rede, line_color=cor, fillcolor=cor, opacity=0.45,
        ))
    fig8.update_layout(
        **LAYOUT_BASE,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#2a2d3e", tickfont=dict(color="#8a8fa8")),
            angularaxis=dict(gridcolor="#2a2d3e"),
        ),
    )
    st.plotly_chart(fig8, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# LINHA 5 — Heatmap
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Heatmap — Score Médio de Atratividade (Rede × Custo)</div>', unsafe_allow_html=True)
if all(c in df_perf_f.columns for c in ["rede", "categoria_custo", "score_atratividade"]):
    df_heat = (df_perf_f.groupby(["rede", "categoria_custo"])["score_atratividade"]
               .mean().round(1).reset_index())
    df_pivot = pd.pivot_table(
        df_heat,
        index="rede",
        columns="categoria_custo",
        values="score_atratividade",
        aggfunc="mean"
    )
    fig9 = px.imshow(df_pivot, text_auto=True, color_continuous_scale="Viridis",
                     labels=dict(color="Score Médio"))
    fig9.update_layout(**LAYOUT_BASE, coloraxis_colorbar=dict(title="Score"))
    st.plotly_chart(fig9, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAPA GEOGRÁFICO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">🗺️ Mapa — IES por Município</div>', unsafe_allow_html=True)

mun_col = next((c for c in ["municipio", "no_municipio_ies"] if c in df_perf_f.columns), None)
if mun_col:
    df_mapa = df_perf_f.copy()
    df_mapa["mun_key"] = df_mapa[mun_col].apply(lambda m: rm_acc(str(m)).strip() if pd.notna(m) else "")

    def busca_coords(k):
        for ck, c in COORDS.items():
            if ck == k or ck in k or k in ck:
                return c[0], c[1]
        return None, None

    df_mapa[["lat", "lon"]] = df_mapa["mun_key"].apply(
        lambda k: pd.Series(busca_coords(k))
    )
    df_plot = df_mapa.dropna(subset=["lat", "lon"])

    if not df_plot.empty:
        n_cursos_map = (df_cursos.groupby("co_ies").size().reset_index(name="n_cursos")
                        if "co_ies" in df_cursos.columns else pd.DataFrame())
        if not n_cursos_map.empty:
            df_plot = df_plot.merge(n_cursos_map, on="co_ies", how="left")
            df_plot["n_cursos"] = df_plot["n_cursos"].fillna(1)
        else:
            df_plot["n_cursos"] = 1

        hover_cols = {c: True for c in ["municipio", "n_cursos", "score_atratividade", "categoria_custo",
                                         "distancia_campinas_km"] if c in df_plot.columns}
        hover_cols.update({"lat": False, "lon": False})

        fig_mapa = px.scatter_map(
            df_plot, lat="lat", lon="lon", color="rede", size="n_cursos",
            hover_name="nome", hover_data=hover_cols,
            map_style="carto-darkmatter",
            zoom=8, center={"lat": REF_LAT, "lon": REF_LON},
            color_discrete_sequence=CORES_REDE,
            size_max=28, opacity=0.85,
        )
        layout_mapa = LAYOUT_BASE.copy()
        layout_mapa["margin"] = {
            "r": 0,
            "t": 10,
            "l": 0,
            "b": 0
        }
        fig_mapa.update_layout(
            **layout_mapa,
            height=520,
            legend_title="Rede",
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.info("Coordenadas não encontradas para as IES filtradas.")
else:
    st.info("Coluna de município não disponível para o mapa.")

# ══════════════════════════════════════════════════════════════════════════════
# TABELA DETALHADA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📋 Tabela de Instituições")

cols_show = [c for c in ["nome", "sigla", "rede", "organizacao", "municipio",
                           "score_atratividade", "categoria_custo", "distancia_campinas_km",
                           "perc_doutores", "perc_qualificados"] if c in df_perf_f.columns]
df_tabela = df_perf_f[cols_show].copy() if cols_show else df_perf_f.copy()

col_busca, col_ord = st.columns([3, 1])
busca = col_busca.text_input("🔎 Buscar instituição", placeholder="Nome ou sigla…")
ordenar = col_ord.selectbox("Ordenar por", [c for c in ["score_atratividade", "nome", "distancia_campinas_km"] if c in df_tabela.columns], index=0)

if busca:
    mask_b = df_tabela["nome"].str.contains(busca, case=False, na=False)
    if "sigla" in df_tabela.columns:
        mask_b |= df_tabela["sigla"].str.contains(busca, case=False, na=False)
    df_tabela = df_tabela[mask_b]

if ordenar in df_tabela.columns:
    df_tabela = df_tabela.sort_values(ordenar, ascending=False)

st.dataframe(
    df_tabela.reset_index(drop=True),
    use_container_width=True,
    height=380,
    column_config={
        "score_atratividade": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
        "perc_doutores":      st.column_config.NumberColumn("% Doutores", format="%.1f%%"),
        "perc_qualificados":  st.column_config.NumberColumn("% Qualificados", format="%.1f%%"),
        "distancia_campinas_km": st.column_config.NumberColumn("Dist. (km)", format="%.0f km"),
    },
)

# ─── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "📊 **ODS 4 — Educação de Qualidade** | "
    "Dados: INEP · Censo da Educação Superior 2022–2024 · SEADE | "
    "Banco: MongoDB Atlas · 4 coleções | "
    "Dashboard: Streamlit + Plotly"
)

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(300)
    st.rerun()
