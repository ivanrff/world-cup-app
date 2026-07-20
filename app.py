import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, timedelta
import locale

# locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Configuração da página para ficar larga e aproveitar melhor o espaço
st.set_page_config(layout="wide", page_title="Previsões do \"Supercomputador\" Opta")

def round_nearest_n(num, n=5):
    return n * round(num / n)

line_sep = " --- "

# Função com cache para ler o banco de dados
# O @st.cache_data evita que o app leia o arquivo o tempo todo ao interagir com o site
# @st.cache_data
def load_data():
    conn = sqlite3.connect("data/db/world_cup.db")
    df = pd.read_sql("SELECT * FROM opta_snapshots", conn)
    df_events = pd.read_sql("SELECT * FROM match_events", conn)
    df_live_predictions = pd.read_sql("SELECT * FROM live_predictions", conn).sort_values(by=['opta_match_id', 'periodId', 'time'])
    conn.close()
    
    # Garantir que a coluna de snapshot seja datetime
    df['snapshot_br'] = pd.to_datetime(df['snapshot_br'])
    df['final_whistle_br'] = pd.to_datetime(df['final_whistle_br'])
    df['match_datetime_br'] = pd.to_datetime(df['match_datetime_br'])
    df = df.sort_values(by='final_whistle_br')

    return df, df_events, df_live_predictions

df, df_events, df_live_predictions = load_data()

# st.dataframe(df_live_predictions)
# st.dataframe(df)

# -------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------------

# --- Sidebar para filtros ---
st.sidebar.header("Filtros")

# Selecione um snapshot
snapshots = df['snapshot_br'].sort_values().unique()
selected_snapshot = st.sidebar.selectbox(label="Escolha o snapshot:", options=snapshots, index=None, placeholder="Snapshot")

# Selecione uma nação
home_nations = df[['home_name_br', 'home_flag']]
away_nations = df[['away_name_br', 'away_flag']]
home_nations.columns = ['nation_name_br', 'nation_flag']
away_nations.columns = ['nation_name_br', 'nation_flag']

nations_and_emojis = pd.concat([home_nations, away_nations], ignore_index=True, axis=0).drop_duplicates(keep='first').sort_values(by='nation_name_br', key=lambda x: x.map(locale.strxfrm))
nations_and_emojis['name_and_emoji'] = nations_and_emojis['nation_flag'] + " " + nations_and_emojis['nation_name_br']
# st.dataframe(nations_and_emojis)
nations = nations_and_emojis['name_and_emoji'] # lista de nações
selected_nation = st.sidebar.selectbox(label="Escolha a Seleção", options=nations, index=None, placeholder="Seleção") # caixa de seleção

if selected_snapshot:
    latest_snapshot = selected_snapshot
else:
    # If no selected snapshot, get the most recent one
    latest_snapshot = df['snapshot_br'].sort_values().unique().max()

# filtering snapshots so they dont overlap
df_past = df[(df['final_whistle_br'] <= latest_snapshot) & (df['match_status'] == 'Played')]
df_future = df[(df['prediction_time'] == 'future') & (df['snapshot_br'] == latest_snapshot)]
df_filtered = pd.concat([df_past, df_future])

if selected_nation:
    selected_nation = selected_nation.split(" ", 1)[1]
    df_filtered = df_filtered[(df_filtered['home_name_br'] == selected_nation) | (df_filtered['away_name_br'] == selected_nation)]

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


# -------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------

# --- Layout Principal ---

svg = """
<svg width="228" height="43" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 228 41.33"><defs><linearGradient id="a" x1="-190.63" y1="415.84" x2="-190.73" y2="415.94" gradientTransform="matrix(239.02 0 0 -239.02 45608.9 99438.71)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#6327c6"></stop><stop offset=".48" stop-color="#b225c3"></stop><stop offset="1" stop-color="#e62c4a"></stop></linearGradient></defs>
<path fill="#fff" d="m136.37 8.79 9.51 24.05h-2.7l-2.7-7.02h-10.63l-2.77 7.02h-2.53l9.51-24.05h2.29Zm3.34 15.01-4.52-11.67-4.55 11.67h9.07Zm12.6-6.53c-.74.12-1.46.31-2.16.56l-.51.2v14.81h-2.29V16.68l1.28-.54c1.91-.76 4-1.15 6.27-1.15 4.47 0 6.71 2.2 6.71 6.61v11.23h-2.26V21.66c0-3.06-1.57-4.59-4.72-4.59-.81 0-1.59.06-2.33.19Zm20.37 5.67c.74.06 1.62.14 2.63.25v-1.55c0-1.46-.33-2.6-1-3.41-.66-.81-1.85-1.21-3.56-1.21-2.23 0-3.8.82-4.72 2.46l-.27.51-2.06-.84.34-.61c1.28-2.36 3.54-3.54 6.78-3.54 1.26 0 2.32.16 3.17.47.85.32 1.55.76 2.07 1.33.53.57.91 1.28 1.15 2.11.24.83.35 1.75.35 2.77v10.25l-1.21.51c-1.3.58-3.17.88-5.6.88-1.39 0-2.56-.1-3.49-.3-.93-.2-1.68-.52-2.24-.94-.56-.43-.96-.97-1.2-1.64-.24-.66-.35-1.44-.35-2.34 0-.94.13-1.75.4-2.41.27-.66.7-1.2 1.3-1.62.6-.42 1.36-.72 2.29-.91.93-.19 2.07-.29 3.42-.29.45 0 1.05.03 1.79.08Zm2.63 7.74v-5.63c-2.02-.2-3.58-.3-4.66-.3-1.78 0-3.03.26-3.76.78s-1.1 1.36-1.1 2.53c0 .56.07 1.06.22 1.48.15.43.4.78.78 1.06.37.28.86.49 1.47.62s1.38.2 2.33.2c1.73 0 3.09-.18 4.08-.54l.64-.2Zm4.75-22.8h2.26v24.96h-2.26V7.88Zm19.11 26.01c0 4.86-2.39 7.29-7.19 7.29-3.17 0-5.41-1.19-6.71-3.58l-.37-.71 2.02-1.01.3.57c.97 1.78 2.54 2.66 4.72 2.66 3.28 0 4.92-1.71 4.92-5.13v-1.99c-1.01.32-1.95.54-2.82.67-.87.13-1.69.2-2.48.2-4.45 0-6.68-2.19-6.68-6.58V15.5h2.26v10.69c0 3.08 1.57 4.62 4.72 4.62 1.44 0 3.1-.3 4.99-.91V15.5h2.29v18.38Zm14-5.64c0-.54-.1-.99-.29-1.35-.19-.36-.48-.65-.88-.88-.39-.22-.9-.4-1.52-.54-.62-.13-1.36-.25-2.21-.34-.85-.09-1.69-.2-2.5-.34-.81-.13-1.53-.38-2.18-.73-.64-.35-1.16-.84-1.55-1.47-.39-.63-.59-1.48-.59-2.56 0-1.57.56-2.81 1.69-3.71 1.12-.9 2.78-1.35 4.96-1.35 3.49 0 5.77 1.23 6.85 3.68h.03l.27.64-2.02.88-.24-.57h-.03c-.38-.85-.93-1.5-1.65-1.92-.72-.43-1.78-.64-3.17-.64-2.95 0-4.42.98-4.42 2.93 0 .74.17 1.33.51 1.77.34.44.84.75 1.52.93.25.07.48.12.69.17.21.05.43.08.66.12.22.03.48.06.76.08.28.02.6.06.96.1.81.09 1.61.21 2.39.35.79.15 1.49.4 2.11.76.62.36 1.12.84 1.5 1.45.38.61.57 1.42.57 2.43 0 1.62-.59 2.88-1.75 3.79-1.17.91-2.89 1.37-5.16 1.37-3.78 0-6.21-1.39-7.29-4.18-.02-.02-.03-.04-.03-.05s-.01-.03-.03-.05l-.17-.44 2.02-.88.27.67v.03c.74 1.93 2.46 2.9 5.16 2.9 3.17 0 4.76-1.02 4.76-3.07Zm9.88 4.64c-.81-.26-1.46-.67-1.96-1.23-.49-.56-.84-1.27-1.05-2.13-.2-.85-.3-1.89-.3-3.1v-8.84h-3.81V15.5h3.81v-4.05H222v4.05h5.5v2.09H222v8.77c0 .94.07 1.73.22 2.34.15.62.4 1.11.76 1.47.36.36.85.61 1.48.76.63.15 1.42.22 2.36.22h.61v2.16h-1.32c-1.24-.02-2.26-.16-3.07-.42ZM81.06 14.81c-2.74 0-5.01.35-6.81 1.05l-1.38.51v23.91h5.09v-7.22c1.01.2 1.9.3 2.66.3 2.58 0 4.53-.62 5.83-1.87 1.3-1.25 1.96-3.06 1.96-5.45v-4.25c0-2.25-.6-3.97-1.8-5.18-1.2-1.2-3.05-1.8-5.55-1.8Zm2.23 11.23c0 1.84-1.02 2.76-3.07 2.76-.65 0-1.41-.07-2.26-.2v-8.97l.2-.03c.38-.09.76-.15 1.15-.19.38-.03.76-.05 1.15-.05 1.89 0 2.83.82 2.83 2.46v4.21Zm16.47-6.21 1.5-4.52h-4.22v-4.05h-5.09v4.05h-3.03v4.52h3.03v5.87c0 1.53.16 2.78.47 3.76.31.98.8 1.75 1.45 2.33.65.57 1.5.97 2.55 1.2s2.29.34 3.73.34h.8v-4.69h-.8c-.58 0-1.07-.04-1.47-.13-.39-.09-.71-.25-.96-.49s-.42-.56-.52-.96c-.1-.4-.15-.92-.15-1.55v-5.66h2.72Zm10.08-5.02c-3.55 0-5.96 1.17-7.22 3.51l-.51.98 4.21 1.75.54-.71c.63-.83 1.56-1.25 2.8-1.25 1.73 0 2.6.83 2.6 2.49v.74c-.36-.02-.74-.04-1.13-.05-.39-.01-.82-.02-1.26-.02-1.42 0-2.62.1-3.62.29-1 .19-1.81.5-2.43.93-.62.43-1.07.99-1.37 1.7-.29.71-.44 1.58-.44 2.61 0 .94.13 1.77.39 2.48s.69 1.29 1.28 1.74c.6.45 1.39.79 2.38 1.01.99.22 2.21.34 3.68.34 2.9 0 5.02-.3 6.37-.91.04-.02.13-.06.25-.12s.26-.12.42-.19c.18-.09.37-.18.57-.27v-9.95c0-4.74-2.51-7.11-7.52-7.11Zm2.43 14.43-.3.03c-.29.05-.65.08-1.08.1-.43.02-.93.03-1.52.03-.88 0-1.47-.14-1.79-.42-.32-.28-.47-.69-.47-1.23s.16-.92.49-1.2c.33-.28.94-.42 1.84-.42.13 0 .34 0 .62.02.28.01.57.02.88.02s.58 0 .84.02c.26.01.42.02.49.02v3.03ZM68.71 10.8c-1.73-1.59-4.19-2.39-7.37-2.39s-5.61.8-7.34 2.39c-1.73 1.59-2.59 3.81-2.59 6.66v6.8c0 2.85.86 5.07 2.59 6.66 1.73 1.59 4.17 2.39 7.34 2.39s5.64-.8 7.37-2.39c1.73-1.59 2.59-3.81 2.59-6.66v-6.8c0-2.85-.86-5.07-2.59-6.66Zm-2.89 13.56c0 2.63-1.49 3.94-4.48 3.94-1.44 0-2.54-.33-3.3-.99-.76-.66-1.14-1.64-1.14-2.95v-7c0-1.3.38-2.28 1.14-2.95.76-.66 1.86-.99 3.3-.99 2.98 0 4.48 1.31 4.48 3.94v7Z"></path>
<path d="M40.25 0c.59 0 1.08.48 1.08 1.08v9.95c0 .59-.48 1.08-1.08 1.08h-9.57c-.59 0-1.42.34-1.84.76l-1.28 1.28c-.42.42-.76 1.24-.76 1.84v7.15c0 .59-.48 1.08-1.08 1.08h-7.15c-.59 0-1.42.34-1.84.76l-1.28 1.28c-.42.42-.76 1.24-.76 1.84v4.73c0 .59-.48 1.08-1.08 1.08H8.88c-.59 0-1.42.34-1.84.76l-1.28 1.28c-.42.42-.76 1.24-.76 1.84v2.31c0 .59-.48 1.08-1.08 1.08H1.24c-.59 0-1.08-.48-1.08-1.08h.01v-2.69c0-.59.48-1.08 1.08-1.08h2.3c.59 0 1.42-.34 1.84-.76l1.28-1.28c.42-.42.76-1.24.76-1.84v-4.73c0-.59.48-1.08 1.08-1.08h4.73c.59 0 1.42-.34 1.84-.76l1.28-1.28c.42-.42.76-1.24.76-1.84v-7.15c0-.59.48-1.08 1.08-1.08h7.15c.59 0 1.42-.34 1.84-.76l1.28-1.28c.42-.42.76-1.24.76-1.84V1.08c0-.59.48-1.08 1.08-1.08h9.95Zm0 14.51c.59 0 1.08.48 1.08 1.08v7.54c0 .59-.48 1.08-1.08 1.08h-7.16c-.59 0-1.42.34-1.84.76l-1.28 1.28c-.42.42-.76 1.24-.76 1.84v4.73c0 .59-.48 1.08-1.08 1.08H23.4c-.59 0-1.42.34-1.84.76l-1.28 1.28c-.42.42-.76 1.24-.76 1.84v2.31c0 .59-.48 1.08-1.08 1.08h-2.69c-.59 0-1.08-.48-1.08-1.08V37.4c0-.59.48-1.08 1.08-1.08h2.31c.59 0 1.42-.34 1.84-.76l1.28-1.28c.42-.42.76-1.24.76-1.84v-4.73c0-.59.48-1.08 1.08-1.08h4.73c.59 0 1.42-.34 1.84-.76l1.28-1.28c.42-.42.76-1.24.76-1.84v-7.16c0-.59.48-1.08 1.08-1.08h7.54Zm0 12.14c.59 0 1.07.48 1.07 1.07v5.1c0 .59-.48 1.07-1.07 1.07h-4.72c-.59 0-1.41.34-1.83.76l-1.28 1.28c-.42.42-.76 1.24-.76 1.83v2.31c0 .59-.48 1.07-1.07 1.07H27.9c-.59 0-1.07-.48-1.07-1.07v-2.69c0-.59.48-1.07 1.07-1.07h2.31c.59 0 1.41-.34 1.83-.76l1.28-1.28c.42-.42.76-1.24.76-1.83v-4.72c0-.59.48-1.07 1.07-1.07h5.1Zm-.01 9.61c.6 0 1.09.47 1.09 1.05v2.62c0 .58-.49 1.05-1.09 1.05h-2.72c-.6 0-1.09-.47-1.09-1.05v-2.62c0-.58.49-1.05 1.09-1.05h2.72Z" fill="url(#a)"></path>
</svg>
"""

st.iframe(svg, height=50)
st.title("Previsões da Copa do Mundo FIFA")
# -------------------------------------------------------------------------------------------------------
st.markdown(line_sep)
# -------------------------------------------------------------------------------------------------------

# st.dataframe(df_future)
# st.dataframe(df_past)
# -------------------------------------------------------------------------------------------------------
# st.markdown(line_sep)
# -------------------------------------------------------------------------------------------------------

# st.title("Próximas Partidas")

next_matches = []
for index, row in df_future.iterrows():
    next_matches.append(row.to_dict())

if len(next_matches) != 0:
    # print(next_matches)
    # 2. Injetamos o CSS para criar a "esteira rolável" horizontal
    st.html(
        """
        <style>
            /* Configura o container pai para renderizar os filhos lado a lado e permitir rolagem */
            [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-wrap: nowrap !important;
                overflow-x: auto !important;
                padding-bottom: 15px; /* Espaço para a barra de rolagem não cortar o conteúdo */
                gap: 16px;
            }
            
            /* Define uma largura fixa para cada retângulo de partida não espremer */
            [data-testid="stHorizontalBlock"] > div {
                min-width: 220px !important;
                max-width: 220px !important;
                flex-shrink: 0 !important;
            }
            
            /* Customização opcional da barra de rolagem para ficar mais sutil */
            [data-testid="stHorizontalBlock"]::-webkit-scrollbar {
                height: 8px;
            }
            [data-testid="stHorizontalBlock"]::-webkit-scrollbar-thumb {
                background: #b225c3; 
                border-radius: 4px;
            }
            [data-testid="stHorizontalBlock"]::-webkit-scrollbar-track {
                background: transparent;
            }
            /* Reduz o espaçamento lateral interno das sub-colunas dentro dos cards */
            [data-testid="stColumn"] {
                padding-left: 2px !important;
                padding-right: 2px !important;
            }
            
            /* Remove o padding excessivo dentro das divs de markdown */
            div[data-testid="stMarkdownContainer"] > p {
                margin-bottom: 0px !important;
            }
        </style>
        """
    )

    # 3. Criamos as colunas dinamicamente baseado no número de partidas
    # Passamos uma lista de 1s com o tamanho das partidas para criar colunas iguais
    colunas = st.columns([1] * len(next_matches))

    for i, next_match in enumerate(next_matches):
        with colunas[i]:
            with st.container(border=True):
                # 1. Data/Hora no topo usando componente nativo
                st.caption(f"{next_match['match_datetime_br'].strftime("%d/%m, %H:%M")}")
                
                # 2. String HTML limpa
                card_layout = f"""
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; font-family: "Source Sans", sans-serif;">
                    
                    <!-- Linha Time da Casa -->
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-weight: bold; width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {next_match['home_flag']} {next_match['home_name_br']}
                        </span>
                        <span style="font-weight: 600;">
                            {next_match['home_proba']:.1f}%
                        </span>
                    </div>
                    
                    <!-- Linha Time Visitante -->
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-weight: bold; width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {next_match['away_flag']} {next_match['away_name_br']}
                        </span>
                        <span style="font-weight: 600;">
                            {next_match['away_proba']:.1f}%
                        </span>
                    </div>

                    <!-- Linha Empate -->
                    <div style="display: flex; align-items: center; gap: 15px; margin-top: 4px;">
                        <span style="color: #888; width: 140px;">
                            Empate
                        </span>
                        <span style="color: #888;">
                            {next_match['draw_proba']:.1f}%
                        </span>
                    </div>

                </div>
                """
                
                # 3. Renderizando via st.html() para garantir a execução do HTML
                st.html(card_layout)

        # Você ainda pode continuar escrevendo abaixo das colunas, 
        # mas ainda dentro do retângulo se quiser:
        # st.caption("Última atualização: agora mesmo")
    # with st.container(border=True):
    #     st.markdown("### Próximas Partidas")
    #     # st.write("Este retângulo agrupa várias informações de forma organizada.")
        
    #     # Adding metrics inside the container
    #     total_sales = 15400
    #     st.metric(label="Faturamento Total", value=f"${total_sales:,}")
        
    #     # Adding a button inside the container
    #     if st.button("Ver Detalhes", key="details_btn"):
    #         st.info("Botão clicado dentro do container!")
    # Exibir os dados em tabela (usando o data_editor para permitir ordenação)
    # st.subheader("Resultados futuros do snapshot")
    # st.dataframe(df_filtered[['opta_match_id', 'match_handle_results']])
    # st.dataframe(df_live_predictions.head(df_live_predictions.shape[0]//2))

    # --- Exemplo de Gráfico: Evolução das Probabilidades ---
    # cores_map = {'Realizado': '#1f77b4', 'Futuro': '#ff7f0e'}
    # Criar um gráfico de linhas simples com Plotly

    # -------------------------------------------------------------------------------------------------------
    st.markdown(line_sep)
    # -------------------------------------------------------------------------------------------------------

st.subheader("Desempenho do Modelo em cada Partida")
df_filtered['cum_mean'] = df_filtered['model_grade'].expanding().mean()
fig = px.line(
    df_filtered, 
    x='final_whistle_br', 
    y='model_grade',
    color='prediction_time',
    # color_discrete_map=cores_map,
    markers=True,
    # title="Desempenho do modelo",
    custom_data=[
                'home_name_br', # 0
                'away_name_br', # 1
                'stage', # 2
                'home_proba', # 3
                'away_proba', # 4
                'draw_proba', # 5
                'home_score', # 6
                'away_score', # 7
                'data_extenso', # 8
                'brier_score', # 9
                'home_flag',
                'away_flag',
                'cum_mean'
            ]
)
# fig.add_scatter(
#     x=df_filtered['final_whistle_br'], 
#     y=df_filtered['cum_mean'],
#     mode='lines'
# )

# https://api.fifa.com/api/v3/picture/flags-sq-2/{}

fig.update_traces(
    hovertemplate="<b>%{customdata[10]} %{customdata[0]} x %{customdata[11]} %{customdata[1]}</b><br>" +
                "<b>%{customdata[2]}</b><br>" +
                "-<br>" +
                "<b>%{customdata[0]} Vence:</b> %{customdata[3]:.0f}%<br>" +
                "<b>%{customdata[1]} Vence:</b> %{customdata[4]:.0f}%<br>" +
                "<b>Empate:</b> %{customdata[5]:.0f}%<br>" +
                "-<br>" +
                "<b>Resultado Final:</b> %{customdata[10]} %{customdata[6]}-%{customdata[7]} %{customdata[11]}<br>" +
                "<b>Data do Fim:</b> %{customdata[8]}<br>" +
                "<b>Brier Score:</b> %{customdata[9]:.4f}<br>" +
                "<b>Desempenho da Opta:</b> %{y:.2f}%<br>" +
                "-<br>" +
                "<b>Desempenho Médio:</b> %{customdata[12]:.2f}%" +
                "<extra></extra>" # Esse <extra> vazio serve para sumir com a caixa lateral com o nome da coluna
)

fig.add_vrect(
    x0="2026-06-11", x1="2026-06-28 11:00", # Ajuste a data inicial de acordo com o seu primeiro jogo
    fillcolor="rgba(255, 255, 255, 0.08)", # Um toque sutil de brilho no fundo
    layer="below", line_width=0, # Garante que fica ATRÁS da linha do gráfico
    annotation_text="Fase de Grupos", annotation_position="bottom left",
    annotation_font=dict(size=14, color="gray")
)

fig.add_vrect(
    x0="2026-06-28 12:00", x1="2026-07-20", # Ajuste a data final com o último jogo mapeado
    fillcolor="rgba(31, 119, 180, 0.12)", # Um tom levemente azulado ao fundo para diferenciar
    layer="below", line_width=0,
    annotation_text="Eliminatórias", annotation_position="bottom left",
    annotation_font=dict(size=14, color="#1f77b4")
)

# fig.add_vline(x=latest_snapshot, line_color="red")

fig.update_layout(
    xaxis_title="",
    yaxis_title="Desempenho (0 a 100%)",
    showlegend=False,
    hoverlabel=dict(
        bgcolor="rgba(0, 0, 0, 0.5)",  # 60% opacity white background
        font_size=14
    )
)

fig.update_xaxes(range=["2026-06-11", "2026-07-20"], tickformat="%d/%m")
fig.update_yaxes(range=[0, 100])

st.plotly_chart(fig, width='stretch')

# -------------------------------------------------------------------------------------------------------
st.markdown(line_sep)
# -------------------------------------------------------------------------------------------------------

# --- Exemplo de Gráfico: Evolução das Probabilidades ---
st.subheader("Dados Minuto-a-Minuto")
df_filtered_played = df_filtered[df_filtered['match_status'] == "Played"]
match_ids = df_filtered_played['match_handle_results'].unique()
selected_match = st.selectbox("Selecione uma partida:", match_ids, index=len(match_ids)-1)

if selected_match:
    # 1. Merge and initial filtering
    df_live_predictions = df_live_predictions.merge(
        df_filtered_played[['opta_match_id', 'match_handle_results', 'home_name_br', 'away_name_br']], 
        how='right', 
        on='opta_match_id'
    )
    df_events = df_events.merge(
        df_filtered_played[['opta_match_id', 'match_handle_results', 'home_name_br', 'away_name_br']], 
        how='right', 
        on='opta_match_id'
    )
    
    # Filter the selected match and sort chronologically by period and time
    match_data = df_live_predictions[
        (df_live_predictions['match_handle_results'] == selected_match) & 
        (df_live_predictions['periodId'] != 14)
    ].copy()
    match_events = df_events[
        (df_events['match_handle_results'] == selected_match)
    ]
    match_confirmed_goals = match_events[
        (match_events['qualifier_qualifierId'] == 56)
        & (match_events['typeId'] == 16)
    ]
    
    match_data = match_data.sort_values(by=['periodId', 'time'])

    if not match_data.empty:
        # 2. Create the continuous timeline
        timeline_x = []
        hover_labels = []
        tick_positions = []
        tick_labels = []
        
        # Calculate the exact end time for each period to stack them continuously
        p1_data = match_data[match_data['periodId'] == 1]
        p1_end_time = p1_data['time'].max() if not p1_data.empty else 45
        
        p2_data = match_data[match_data['periodId'] == 2]
        p2_max_real = p2_data['time'].max() if not p2_data.empty else 90
        p2_end_time = p1_end_time + max(0, p2_max_real - 45)
        
        p3_data = match_data[match_data['periodId'] == 3]
        p3_max_real = p3_data['time'].max() if not p3_data.empty else 105
        p3_end_time = p2_end_time + max(0, p3_max_real - 90)

        p4_data = match_data[match_data['periodId'] == 4]

        # Map real times to create the X-axis marks beautifully
        for index, row in match_data.iterrows():
            period = row['periodId']
            t_real = row['time']
            t_real_int = int(round(t_real))
            
            if period == 1:
                t_continuous = t_real
                label_hover = f"{t_real_int}' (1T)"
            elif period == 2:
                time_into_period = max(0, t_real - 45)
                t_continuous = p1_end_time + time_into_period
                label_hover = f"{t_real_int}' (2T)"
            elif period == 3:
                time_into_period = max(0, t_real - 90)
                t_continuous = p2_end_time + time_into_period
                label_hover = f"{t_real_int}' (PROR1)"
            elif period == 4:
                time_into_period = max(0, t_real - 105)
                t_continuous = p3_end_time + time_into_period
                label_hover = f"{t_real_int}' (PROR2)"
            else:
                t_continuous = t_real
                label_hover = f"{t_real_int}'"
                
            timeline_x.append(t_continuous)
            hover_labels.append(label_hover)
            
            # Create nice ticks for the X-axis (every 10 minutes of real match time)
            if t_real_int % 10 == 0:
                # Avoid duplicate ticks for the same minute across periods
                if f"{t_real_int}'" not in tick_labels:
                    if (period == 1 and t_real <= 45) or \
                       (period == 2 and 45 <= t_real <= 90) or \
                       (period == 3 and 90 <= t_real <= 105) or \
                       (period == 4 and 105 <= t_real <= 120):
                        tick_positions.append(t_continuous)
                        tick_labels.append(f"{t_real_int}'")

        match_data['timeline_x'] = timeline_x
        match_data['display_time'] = hover_labels

        # Team names for the chart
        home_name = match_data['home_name_br'].iloc[0] if 'home_name_br' in match_data.columns else 'Home'
        away_name = match_data['away_name_br'].iloc[0] if 'away_name_br' in match_data.columns else 'Away'

        rename_dict = {
            'Home': home_name,
            'Away': away_name,
            'Draw': 'Empate'
        }

        match_data = match_data.rename(columns=rename_dict)
        y_columns = [
            home_name,
            'Empate',
            away_name
        ]

        # ---------------------------------------
        cols_not_needed = [
            "periodId",
            "timeMin",
            "timeSec",
            "opta_match_id",
            "time",
            "match_handle_results",
            "home_name_br",
            "away_name_br"
            ]
        match_data_to_plot = match_data.drop(columns=cols_not_needed)
        match_data_to_plot = match_data_to_plot.groupby("display_time").mean().reset_index().sort_values(by="timeline_x")
        # match_data = match_data.groupby([])
        # ---------------------------------------
        # 3. Generate the single chart
        fig_1 = px.area(
            match_data_to_plot, 
            x='display_time', 
            y=y_columns, 
            title="Distribuição de Probabilidade em Tempo Real"
        )          
            
        fig_1.update_traces(hovertemplate="")
        
        # 4. Customize the X-axis to hide the artificial timeline
        fig_1.update_layout(
            xaxis=dict(
                title="Tempo de Jogo",
                tickvals=tick_positions,
                ticktext=tick_labels
            ),
            yaxis=dict(
                title="Probabilidade",
                tickformat=".0f",
                ticksuffix='%'
            ),
            legend=dict(
                title="Resultado",
                traceorder="reversed" # <--- INVERTE A ORDEM DA LEGENDA
            ),
            hovermode="x unified" 
        )
        
        # Add dotted vertical lines dividing the periods
        # Use Streamlit's native CSS variable to dynamically match the current theme background
        dynamic_bg_color = bg = (
            fig_1.layout.plot_bgcolor
            or fig_1.layout.paper_bgcolor
            or "#FFFFFF"
        )
        line_thickness = 1
        annot_bg_color = "#706F6F"
        
        fig_1.add_shape(
            type="line",
            x0="45' (2T)",    # Posição no eixo X (início)
            x1="45' (2T)",    # Posição no eixo X (fim) - igual ao x0 para ser vertical
            y0=0,  # Início no eixo Y
            y1=100,  # Fim no eixo Y
            line=dict(
                color=dynamic_bg_color,
                width=line_thickness,
                dash="dash"  # Opcional: "solid", "dot", "dash", "dashdot"
            )
        )

        # 2. Add the text explicitly controlling the coordinates
        fig_1.add_annotation(
            x="0' (1T)", 
            y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
            # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
            text="1º Tempo",
            showarrow=False,
            font=dict(color="white", size=12),
            xanchor="left",
            yanchor="bottom",
            bgcolor=annot_bg_color,
        )
        # 2. Add the text explicitly controlling the coordinates
        fig_1.add_annotation(
            x="45' (2T)", 
            y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
            # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
            text="2º Tempo",
            showarrow=False,
            font=dict(color="white", size=12),
            xanchor="left",
            yanchor="bottom",
            bgcolor=annot_bg_color,
        )

        if not p3_data.empty:
            fig_1.add_shape(
                type="line",
                x0="90' (PROR1)",    # Posição no eixo X (início)
                x1="90' (PROR1)",    # Posição no eixo X (fim) - igual ao x0 para ser vertical
                y0=0,  # Início no eixo Y
                y1=100,  # Fim no eixo Y
                line=dict(
                    color=dynamic_bg_color,
                    width=line_thickness,
                    dash="dash"  # Opcional: "solid", "dot", "dash", "dashdot"
                )
            )
            
            fig_1.add_shape(
                type="line",
                x0="105' (PROR2)",    # Posição no eixo X (início)
                x1="105' (PROR2)",    # Posição no eixo X (fim) - igual ao x0 para ser vertical
                y0=0,  # Início no eixo Y
                y1=100,  # Fim no eixo Y
                line=dict(
                    color=dynamic_bg_color,
                    width=line_thickness,
                    dash="dash"  # Opcional: "solid", "dot", "dash", "dashdot"
                )
            )


            fig_1.add_annotation(
                x="90' (PROR1)", 
                y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
                # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
                text="1ºT. Pror.",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor="left",
                yanchor="bottom",
                bgcolor=annot_bg_color,
            )

            fig_1.add_annotation(
                x="105' (PROR2)", 
                y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
                # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
                text="2ºT. Pror.",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor="left",
                yanchor="bottom",
                bgcolor=annot_bg_color,
            )

        for index, row in match_confirmed_goals.iterrows():
            if row['periodId'] in {1, 2}:
                goal_time = f"{int(round(row['time']))}' ({row['periodId']}T)"
            elif row['periodId'] in {3, 4}:
                goal_time = f"{int(round(row['time']))}' (PROR{row['periodId'] - 2})"

            scorer_name = row['playerName']
            # print(scorer_name)
            # print(goal_time)
            # fig_1.add_vline(
            #     x=goal_time, 
            #     line_color="white", 
            #     line_width=2,
            #     # annotation_text="a",
            #     # annotation_position="top"
            # )

            fig_1.add_shape(
                type="line",
                x0=goal_time,    # Posição no eixo X (início)
                x1=goal_time,    # Posição no eixo X (fim) - igual ao x0 para ser vertical
                y0=100,  # Início no eixo Y
                y1=105 + (index % 2)*5,  # Fim no eixo Y
                line=dict(
                    color="white",
                    width=2
                )
            )
            # 2. Add the text explicitly controlling the coordinates
            fig_1.add_annotation(
                x=goal_time, 
                y=110 + (index % 2)*5, # Position on the Y axis (1.02 pushes it slightly above the chart)
                text=f"⚽{scorer_name} {int(round(row['time']))}'",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor="center"
            )

        st.plotly_chart(fig_1, width='stretch', key="single_match_trend")
        
        # -------------------------------------------------------------------------------------------------------
        
        fig_2 = px.line(
            match_data_to_plot, 
            x='display_time', 
            y='model_grade',
            title="Desempenho de acordo com o resultado final"
        )

        fig_2.update_traces(hovertemplate="")
        
        # 4. Customize the X-axis to hide the artificial timeline
        fig_2.update_layout(
            xaxis=dict(
                title="Tempo de Jogo",
                tickvals=tick_positions,
                ticktext=tick_labels
            ),
            yaxis=dict(
                title="Desempenho",
                tickformat=".0f",
                ticksuffix='%'
            ),
            hovermode="x unified" 
        )
        dynamic_bg_color = bg = (
            fig_2.layout.plot_bgcolor
            or fig_2.layout.paper_bgcolor
            or "#FFFFFF"
        )
        line_thickness = 1
        annot_bg_color = "#706F6F"
        
        fig_2.add_shape(
            type="line",
            x0="45' (2T)",    # Posição no eixo X (início)
            x1="45' (2T)",    # Posição no eixo X (fim) - igual ao x0 para ser vertical
            y0=0,  # Início no eixo Y
            y1=100,  # Fim no eixo Y
            line=dict(
                color=dynamic_bg_color,
                width=line_thickness,
                dash="dash"  # Opcional: "solid", "dot", "dash", "dashdot"
            )
        )

        # 2. Add the text explicitly controlling the coordinates
        fig_2.add_annotation(
            x="0' (1T)", 
            y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
            # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
            text="1º Tempo",
            showarrow=False,
            font=dict(color="white", size=12),
            xanchor="left",
            yanchor="bottom",
            bgcolor=annot_bg_color,
        )
        # 2. Add the text explicitly controlling the coordinates
        fig_2.add_annotation(
            x="45' (2T)", 
            y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
            # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
            text="2º Tempo",
            showarrow=False,
            font=dict(color="white", size=12),
            xanchor="left",
            yanchor="bottom",
            bgcolor=annot_bg_color,
        )

        if not p3_data.empty:
            fig_2.add_shape(
                type="line",
                x0="90' (PROR1)",    # Posição no eixo X (início)
                x1="90' (PROR1)",    # Posição no eixo X (fim) - igual ao x0 para ser vertical
                y0=0,  # Início no eixo Y
                y1=100,  # Fim no eixo Y
                line=dict(
                    color=dynamic_bg_color,
                    width=line_thickness,
                    dash="dash"  # Opcional: "solid", "dot", "dash", "dashdot"
                )
            )
            
            fig_2.add_shape(
                type="line",
                x0="105' (PROR2)",    # Posição no eixo X (início)
                x1="105' (PROR2)",    # Posição no eixo X (fim) - igual ao x0 para ser vertical
                y0=0,  # Início no eixo Y
                y1=100,  # Fim no eixo Y
                line=dict(
                    color=dynamic_bg_color,
                    width=line_thickness,
                    dash="dash"  # Opcional: "solid", "dot", "dash", "dashdot"
                )
            )


            fig_2.add_annotation(
                x="90' (PROR1)", 
                y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
                # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
                text="1ºT. Pror.",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor="left",
                yanchor="bottom",
                bgcolor=annot_bg_color,
            )

            fig_2.add_annotation(
                x="105' (PROR2)", 
                y=0, # Position on the Y axis (1.02 pushes it slightly above the chart)
                # yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
                text="2ºT. Pror.",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor="left",
                yanchor="bottom",
                bgcolor=annot_bg_color,
            )

        for index, row in match_confirmed_goals.iterrows():
            if row['periodId'] in {1, 2}:
                goal_time = f"{int(round(row['time']))}' ({row['periodId']}T)"
            elif row['periodId'] in {3, 4}:
                goal_time = f"{int(round(row['time']))}' (PROR{row['periodId'] - 2})"

            scorer_name = row['playerName']
            # print(scorer_name)
            # print(goal_time)
            # fig_2.add_vline(
            #     x=goal_time, 
            #     line_color="white", 
            #     line_width=2,
            #     # annotation_text="a",
            #     # annotation_position="top"
            # )

            fig_2.add_shape(
                type="line",
                x0=goal_time,    # Posição no eixo X (início)
                x1=goal_time,    # Posição no eixo X (fim) - igual ao x0 para ser vertical
                y0=100,  # Início no eixo Y
                y1=105 + (index % 2)*5,  # Fim no eixo Y
                line=dict(
                    color="white",
                    width=2
                )
            )
            # 2. Add the text explicitly controlling the coordinates
            fig_2.add_annotation(
                x=goal_time, 
                y=110 + (index % 2)*5, # Position on the Y axis (1.02 pushes it slightly above the chart)
                text=f"⚽{scorer_name} {int(round(row['time']))}'",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor="center"
            )
        st.plotly_chart(fig_2, width='stretch', key="single_match_eval")
        # st.dataframe(match_data_to_plot)
    else:
        st.info("Nenhum dado de período válido encontrado para este jogo.")

# -------------------------------------------------------------------------------------------------------
st.markdown(line_sep)
# -------------------------------------------------------------------------------------------------------




# st.dataframe(match_events)