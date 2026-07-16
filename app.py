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

# Função com cache para ler o banco de dados
# O @st.cache_data evita que o app leia o arquivo o tempo todo ao interagir com o site
@st.cache_data
def load_data():
    conn = sqlite3.connect("data/db/world_cup.db")
    df = pd.read_sql("SELECT * FROM opta_snapshots", conn)
    df_events = pd.read_sql("SELECT * FROM match_events", conn)
    df_live_predictions = pd.read_sql("SELECT * FROM live_predictions", conn).sort_values(by=['opta_match_id', 'periodId', 'time'])
    conn.close()
    
    # Garantir que a coluna de snapshot seja datetime
    df['snapshot_br'] = pd.to_datetime(df['snapshot_br'])
    df['final_whistle_br'] = pd.to_datetime(df['final_whistle_br'])
    df = df.sort_values(by='final_whistle_br')

    return df, df_events, df_live_predictions

df, df_events, df_live_predictions = load_data()

# df_future = df[(df['match_status'] != "TBD") & (df['match_status'] != "Played")]
# df_past = df[df['match_status'] == "Played"]

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

# --- Layout Principal ---
st.title("Previsões do \"Supercomputador\" Opta")

# Exibir os dados em tabela (usando o data_editor para permitir ordenação)
st.subheader("Resultados futuros do snapshot")
# st.dataframe(df_filtered[['opta_match_id', 'match_handle_results']])
# st.dataframe(df_live_predictions.head(df_live_predictions.shape[0]//2))

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
                'away_flag'
            ]
)

# https://api.fifa.com/api/v3/picture/flags-sq-2/{}

fig.update_traces(
    hovertemplate="<b>%{customdata[10]} %{customdata[0]} x %{customdata[11]} %{customdata[1]}</b><br>" +
                "<b>%{customdata[2]}</b><br>" +
                "-<br>" +
                "<b>%{customdata[0]} Vence:</b> %{customdata[3]}%<br>" +
                "<b>%{customdata[1]} Vence:</b> %{customdata[4]}%<br>" +
                "<b>Empate:</b> %{customdata[5]}%<br>" +
                "-<br>" +
                "<b>Resultado Final:</b> %{customdata[10]} %{customdata[6]}-%{customdata[7]} %{customdata[11]}<br>" +
                "<b>Data do Fim:</b> %{customdata[8]}<br>" +
                "<b>Brier Score:</b> %{customdata[9]:.4f}<br>" +
                "<b>Desempenho da Opta:</b> %{y:.2f}%<br>" +
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

fig.add_vline(x=latest_snapshot, line_color="red")

fig.update_layout(
    xaxis_title="",
    yaxis_title="Desempenho (0 a 100%)",
    showlegend=False
)

fig.update_xaxes(range=["2026-06-11", (datetime.now() + timedelta(days=1)).strftime(format="%Y-%m-%d")], tickformat="%d/%m")
fig.update_yaxes(range=[0, 100])

st.plotly_chart(fig, width='stretch')

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

# --- Exemplo de Gráfico: Evolução das Probabilidades ---
st.subheader("Evolução das Previsões por Jogo")
match_ids = df_filtered['match_handle_results'].unique()
selected_match = st.selectbox("Escolha um jogo para ver a tendência:", match_ids)

if selected_match:
    # 1. Merge and initial filtering
    df_live_predictions = df_live_predictions.merge(
        df_filtered[['opta_match_id', 'match_handle_results', 'home_name_br', 'away_name_br']], 
        how='right', 
        on='opta_match_id'
    )
    df_events = df_events.merge(
        df_filtered[['opta_match_id', 'match_handle_results', 'home_name_br', 'away_name_br']], 
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
        & (df_events['qualifier_qualifierId'] == 56)
        & (df_events['typeId'] == 16)
    ].reset_index(drop=True).copy()
    
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
        y_columns = [home_name, 'Empate', away_name]

        # 3. Generate the single chart
        fig = px.area(
            match_data, 
            x='display_time', 
            y=y_columns, 
            title="Distribuição de Probabilidade em Tempo Real",
            custom_data=['display_time'],
        )
        
        # Update the hover for each trace individually
        for i, trace in enumerate(fig.data):
            original_name = trace.name 
            display_name = rename_dict.get(original_name, original_name)
            
            trace.name = display_name
            invisible_x = "<span style='font-size: 1px; color: transparent;'>%{{x}}</span>"
            
            # Adiciona a informação do tempo (customdata) APENAS na primeira linha da legenda
            if i == 0:
                trace.hovertemplate = (
                    f"<b>%{{customdata[0]}}</b><br>" # O título customizado
                    f"<b>{display_name}:</b> %{{y:.1%}}<br>"
                    f"{invisible_x}<extra></extra>"
                )
            else:
                trace.hovertemplate = ("<br>"
                    f"<b>{display_name}:</b> %{{y:.1%}}<br>"
                    f"{invisible_x}<extra></extra>"
                )
            
        fig.update_traces(hovertemplate="")
        
        # 4. Customize the X-axis to hide the artificial timeline
        fig.update_layout(
            xaxis=dict(
                title="Tempo de Jogo",
                tickmode='array',
                tickvals=tick_positions,
                ticktext=tick_labels,
                gridcolor='rgba(200, 200, 200, 0.2)'
            ),
            yaxis=dict(
                title="Probabilidade",
                tickformat='.0%'
            ),
            legend_title="Resultado",
            hovermode="x unified" 
        )
        
        # Add dotted vertical lines dividing the periods
        # Use Streamlit's native CSS variable to dynamically match the current theme background
        dynamic_bg_color = bg = (
            fig.layout.plot_bgcolor
            or fig.layout.paper_bgcolor
            or "#0E1117"
        )
        line_thickness = 2
        
        # Add dashed vertical lines dividing the periods
        fig.add_vline(
            x=p1_end_time, 
            line_color=dynamic_bg_color, 
            line_width=line_thickness
        )
        
        if not p3_data.empty:
            fig.add_vline(
                x=p2_end_time,  
                line_color=dynamic_bg_color,
                line_width=line_thickness
            )
            
        if not p4_data.empty:
            fig.add_vline(
                x=p3_end_time,  
                line_color=dynamic_bg_color,
                line_width=line_thickness
            )
        
        for index, row in match_events.iterrows():
            goal_time = f"{int(round(row['time']))}' ({row['periodId']}T)"
            scorer_name = row['playerName']
            # print(scorer_name)
            # print(goal_time)
            fig.add_vline(
                x=goal_time, 
                line_color="white", 
                line_width=2,
                # annotation_text="a",
                # annotation_position="top"
        )
            # 2. Add the text explicitly controlling the coordinates
            fig.add_annotation(
                x=goal_time, 
                y=1.00 + (index % 2)/30, # Position on the Y axis (1.02 pushes it slightly above the chart)
                yref="paper", # "paper" means 0 is the bottom of the chart and 1 is the top
                text=f"⚽{scorer_name} {int(round(row['time']))}'",
                showarrow=False,
                font=dict(color="white", size=12),
                xanchor="center",
                yanchor="bottom"
            )

        st.plotly_chart(fig, width='stretch', key="single_match_trend")
    else:
        st.info("Nenhum dado de período válido encontrado para este jogo.")

# st.dataframe(match_events)