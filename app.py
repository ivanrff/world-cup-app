import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# Configuração da página para ficar larga e aproveitar melhor o espaço
st.set_page_config(layout="wide", page_title="Dashboard Copa 2026")

# Função com cache para ler o banco de dados
# O @st.cache_data evita que o app leia o arquivo o tempo todo ao interagir com o site
@st.cache_data
def load_data():
    conn = sqlite3.connect("data/db/world_cup.db")
    df = pd.read_sql("SELECT * FROM opta_snapshots", conn)
    conn.close()
    
    # Garantir que a coluna de snapshot seja datetime
    df['snapshot_br'] = pd.to_datetime(df['snapshot_br'])
    df['final_whistle_br'] = pd.to_datetime(df['final_whistle_br'])
    return df

df = load_data().sort_values(by='final_whistle_br')
df = df[(df['match_status'] != "TBD")].copy()
# df_future = df[(df['match_status'] != "TBD") & (df['match_status'] != "Played")]
# df_past = df[df['match_status'] == "Played"]

# --- Sidebar para filtros ---
st.sidebar.header("Filtros")
selected_snapshot = st.sidebar.selectbox("Selecione o snapshot:", (df['snapshot_br'].sort_values().unique()))

if selected_snapshot:
    # df_filtered = df[df['snapshot_br'] == selected_snapshot]
    df_past = df[(df['final_whistle_br'] <= selected_snapshot) & (df['match_status'] == 'Played')]
    df_future = df[(df['prediction_time'] == 'future') & (df['snapshot_br'] == selected_snapshot)]
    df_filtered = pd.concat([df_past, df_future])
else:
    df_filtered = df


meses_pt = {
    1: "de Janeiro", 2: "de Fevereiro", 3: "de Março", 4: "de Abril",
    5: "de Maio", 6: "de Junho", 7: "de Julho", 8: "de Agosto",
    9: "de Setembro", 10: "de Outubro", 11: "de Novembro", 12: "de Dezembro"
}

# Cria a string no formato: "dd de [Mês Extenso] hh:mm"
df_filtered['data_extenso'] = (
    df_filtered['final_whistle_br'].dt.strftime('%d ') + 
    df_filtered['final_whistle_br'].dt.month.map(meses_pt) + 
    df_filtered['final_whistle_br'].dt.strftime(', %H:%M')
)

# --- Layout Principal ---
st.title("Painel de Previsões da Opta")

# Exibir os dados em tabela (usando o data_editor para permitir ordenação)
# st.subheader("Resultados futuros do snapshot")
# st.dataframe(df_filtered[['snapshot_br', 'match_status', 'match_handle', 'final_whistle_br', 'prediction_time']].sort_values(by='final_whistle_br'))

# --- Exemplo de Gráfico: Evolução das Probabilidades ---
# cores_map = {'Realizado': '#1f77b4', 'Futuro': '#ff7f0e'}
# Criar um gráfico de linhas simples com Plotly
fig = px.line(
    df_filtered, 
    x='final_whistle_br', 
    y='model_grade',
    color='prediction_time',
    # color_discrete_map=cores_map,
    markers=True,
    title="Desempenho do modelo",
    custom_data=['home_code', 'away_code', 'home_proba', 'away_proba', 'draw_proba', 'match_handle', 'brier_score', 'home_score', 'away_score', 'data_extenso', 'stage']
)

fig.add_vrect(
    x0="2026-06-11", x1="2026-06-28 11:00", # Ajuste a data inicial de acordo com o seu primeiro jogo
    fillcolor="rgba(255, 255, 255, 0.08)", # Um toque sutil de brilho no fundo
    layer="below", line_width=0, # Garante que fica ATRÁS da linha do gráfico
    annotation_text="Fase de Grupos", annotation_position="bottom left",
    annotation_font=dict(size=14, color="gray")
)

fig.add_vrect(
    x0="2026-06-28 12:00", x1="2026-07-15", # Ajuste a data final com o último jogo mapeado
    fillcolor="rgba(31, 119, 180, 0.12)", # Um tom levemente azulado ao fundo para diferenciar
    layer="below", line_width=0,
    annotation_text="Eliminatórias", annotation_position="bottom left",
    annotation_font=dict(size=14, color="#1f77b4")
)

fig.update_traces(
    hovertemplate="<b>%{customdata[5]}</b><br>" +
                "<b>%{customdata[10]}</b><br>" +
                "-<br>" +
                "<b>%{customdata[0]} Vence:</b> %{customdata[2]}%<br>" +
                "<b>%{customdata[1]} Vence:</b> %{customdata[3]}%<br>" +
                "<b>Empate:</b> %{customdata[4]}%<br>" +
                "-<br>" +
                "<b>Resultado Final:</b> %{customdata[0]} %{customdata[7]}-%{customdata[8]} %{customdata[1]}<br>" +
                "<b>Data do Fim:</b> %{customdata[9]}<br>" +
                "<b>Brier Score:</b> %{customdata[6]:.4f}<br>" +
                "<b>Desempenho da Opta:</b> %{y:.2f}%<br>" +
                "<extra></extra>" # Esse <extra> vazio serve para sumir com a caixa lateral com o nome da coluna
)

fig.update_layout(
    xaxis_title="",
    yaxis_title="Desempenho (0 a 100%)",
    showlegend=False
)

fig.update_xaxes(range=["2026-06-11", datetime.now().strftime(format="%Y-%m-%d")], tickformat="%d/%m")
fig.update_yaxes(range=[0, 100])

st.plotly_chart(fig, use_container_width=True, width='stretch')

## -- AVG SCORES -- 

# Injeta o CSS para centralizar o rótulo (label) e o valor (value) do st.metric
st.html(
    """
    <style>
        /* Mira no bloco completo da métrica e centraliza todos os filhos flex */
        [data-testid="stMetric"] {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        
        /* Garante que o texto do label também obedeça ao centro */
        [data-testid="stMetricLabel"] {
            width: 100%;
            display: flex;
            justify-content: center;
        }
    </style>
    """
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Brier Score Médio", 
        value=f"{df_filtered['brier_score'].mean():.4f}"
    )

with col2:
    st.metric(
        label="Desempenho Médio", 
        value=f"{df_filtered['model_grade'].mean():.2f}%"
    )

# # --- Exemplo de Gráfico: Evolução das Probabilidades ---
# st.subheader("Evolução das Previsões por Jogo")
# match_ids = df_filtered['match_handle'].unique()
# selected_match = st.selectbox("Escolha um jogo para ver a tendência:", match_ids)

# if selected_match:
#     match_data = df_filtered[df_filtered['match_handle'] == selected_match]
    
#     # Criar um gráfico de linhas simples com Plotly
#     fig = px.line(
#         match_data, 
#         x='snapshot_br', 
#         y=['home_proba', 'away_proba', 'draw_proba'],
#         title=f"Tendência de probabilidade - Jogo {selected_match}"
#     )
#     st.plotly_chart(fig, use_container_width=True)