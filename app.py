import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

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
    return df

df = load_data().sort_values(by='final_whistle_br')
df = df[(df['match_status'] != "TBD")].copy()
# df_future = df[(df['match_status'] != "TBD") & (df['match_status'] != "Played")]
# df_past = df[df['match_status'] == "Played"]

# --- Sidebar para filtros ---
st.sidebar.header("Filtros")
selected_snapshot = st.sidebar.selectbox("Selecione o snapshot:", (df['snapshot_br'].sort_values().unique()))

if selected_snapshot:
    df_filtered = df[df['snapshot_br'] <= selected_snapshot]
else:
    df_filtered = df

# --- Layout Principal ---
st.title("📊 Painel de Previsões da Opta")

# Exibir os dados em tabela (usando o data_editor para permitir ordenação)
st.subheader("Snapshot mais recente")
st.dataframe(df_filtered.sort_values(by='final_whistle_br'))

# --- Exemplo de Gráfico: Evolução das Probabilidades ---
    
# Criar um gráfico de linhas simples com Plotly
fig = px.line(
    df_filtered, 
    x='final_whistle_br', 
    y=['model_grade'],
    title=f"Desempenho do modelo"
)
st.plotly_chart(fig, use_container_width=True)

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