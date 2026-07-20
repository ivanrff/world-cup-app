# %%
from pathlib import Path
import json
import pandas as pd
import sqlite3
import countryflag as cf
from rich.progress import track

def to_br_timezone(column):
    converted_col = column.dt.tz_convert(
    "America/Sao_Paulo").dt.tz_localize(None)

    return converted_col

fifa_ranking_df = pd.read_csv('../data/etc/fifa_ranking_pre_wc.csv', encoding='utf-8')
fixture_files = sorted([f.name for f in Path('../data/opta/fixture_jsons').iterdir() if f.is_file()])

live_predictions_dfs_list = []

matches_list = []
event_dfs_list = []
played_matches_ids = set() # saves the ids of played matches that were already processed
i = 0
for file in track(fixture_files, description="Processing files"):

    snapshot = file.split('f')[0][1:][:-1]
    with open(f"../data/opta/fixture_jsons/{file}", 'r', encoding='utf-8') as f:
        data = json.load(f)

    for match_id in data.keys():

        match_data = data[match_id]

        matchInfo = match_data.get("matchInfo")

        if not matchInfo:
            # checker['match_status'] = 'TBD'
            # matches.append(checker)
            continue
        if (match_data['liveData']['matchDetails']['matchStatus'] == 'Played') & (match_id in played_matches_ids):
            continue

        checker = {
            'opta_match_id': match_id,
            'snapshot_br': pd.to_datetime(snapshot, format="%Y%m%d%H%M%S"),
            'match_datetime': pd.to_datetime(matchInfo['date'] + matchInfo['time'], format="%Y-%m-%dZ%H:%M:%S%z"),
            'stage': matchInfo['stage'].get('name')
        }

        if checker['stage'].lower() == 'group stage':
            checker['group'] = matchInfo['series'].get('name')
        
        for team in range(2):
            position = matchInfo['contestant'][team].get('position')
            team_code = matchInfo['contestant'][team].get('code')
            team_name = matchInfo['contestant'][team].get('name')
            
            checker[f'{position}_code'] = team_code
            checker[f'{position}_name'] = team_name
            # checker[f'{position}_official_name'] = matchInfo['contestant'][team].get('officialName')
            # checker[f'{position}_short_name'] = matchInfo['contestant'][team].get('shortName')
            checker[f'{position}_name_br'] = fifa_ranking_df.loc[fifa_ranking_df['IdCountry'] == team_code, "TeamName"].to_list()[0]
            
            try:
                checker[f'{position}_flag'] = cf.getflag([team_name])
            # Scotland doesn't exist in the countryflag library, so we have to force it:
            except:
                if checker[f'{position}_name'] == 'Scotland':
                   checker[f'{position}_flag'] = "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
            if checker[f'{position}_name'] == 'England':
                checker[f'{position}_flag'] = "🏴󠁧󠁢󠁥󠁮󠁧󠁿"

        preMatchPredictions = match_data['liveData']['preMatchPredictions']

        for prediction in preMatchPredictions:
            for type in prediction['prediction']:
                checker[f"{type['type'].lower()}_proba"] = type['probability']

        match_results = match_data['liveData']['matchDetails']

        checker['match_status'] = match_results['matchStatus']

        if (checker['match_status'] == 'Played') & (match_id not in played_matches_ids):
            i = i + 1
            for period in match_results['period']:
                if period['id'] == len(match_results['period']):
                    checker['final_whistle'] = pd.to_datetime(period['end'])

            scores = match_results.get('scores', {})
            score_data = scores.get('et') or scores.get('ft', {})
            
            checker['home_score'] = score_data.get('home')
            checker['away_score'] = score_data.get('away')

            if checker['home_score'] > checker['away_score']:
                checker['result'] = 'Home Win'
                checker['home_outcome'] = 1
                checker['draw_outcome'] = 0
                checker['away_outcome'] = 0
            elif checker['home_score'] < checker['away_score']:
                checker['result'] = 'Away Win'
                checker['home_outcome'] = 0
                checker['draw_outcome'] = 0
                checker['away_outcome'] = 1
            else:
                checker['result'] = 'Draw'
                checker['home_outcome'] = 0
                checker['draw_outcome'] = 1
                checker['away_outcome'] = 0

            # i guess make a for for each qualifier inside each event
            events_data = match_data['liveData'].get('event', [])
            if events_data:
                df_events = pd.json_normalize(
                    events_data,
                    record_path=['qualifier'],
                    meta=['id', 'eventId', 'typeId', 'periodId', 'timeMin', 'timeSec', 
                          'playerId', 'playerName', 'contestantId', 'outcome', 'x', 'y', 
                          'timeStamp', 'lastModified'],
                    record_prefix='qualifier_', 
                    errors='ignore'
                )
                df_events['opta_match_id'] = match_id
                event_dfs_list.append(df_events)

            live_predictions_data = match_data['liveData'].get('livePredictions', [])
            if live_predictions_data:
                df_live_predictions = pd.json_normalize(
                    live_predictions_data,
                    record_path=['prediction'],
                    meta=["timeMin", "timeSec", "periodId"]
                )
                df_live_predictions['opta_match_id'] = match_id
                live_predictions_dfs_list.append(df_live_predictions)

            played_matches_ids.add(match_id) # .add() para sets, .append para listas
        matches_list.append(checker)

# SNAPSHOTS DATAFRAME
snapshots_df = pd.DataFrame(matches_list)
print(i)
# EVENTS DATAFRAME
match_events_df = pd.concat(event_dfs_list, ignore_index=True) if event_dfs_list else pd.DataFrame()

# LIVE PREDICTIONS DATAFRAME
match_live_predictions_df = pd.concat(live_predictions_dfs_list, ignore_index=True) if live_predictions_dfs_list else pd.DataFrame()
match_live_predictions_df = match_live_predictions_df.drop_duplicates(subset=["type", "timeMin", "timeSec", "periodId", "opta_match_id"], keep='last')
match_live_predictions_df = match_live_predictions_df.pivot(
    index=["timeMin", "timeSec", "periodId", "opta_match_id"],
    columns="type",
    values="probability"
).reset_index()
match_live_predictions_df.columns.name = None
match_live_predictions_df[['Home', 'Away', 'Draw']] = match_live_predictions_df[['Home', 'Away', 'Draw']].apply(pd.to_numeric)

# Conversão do tempo que está separado em duas colunas (minuto, segundo) em uma coluna só continua em (min)
for df in [match_events_df, match_live_predictions_df]:
    df['time'] = df['timeMin'] + df['timeSec']/60
    df = df.drop(columns=['timeMin', 'timeSec'])

# deixando as colunas lower case para consistencia
snapshots_df.columns = [col.lower() for col in snapshots_df.columns]

# colocando as coluans numéricas como números
snapshots_df = snapshots_df.astype({
    "home_proba": float,
    "away_proba": float,
    "draw_proba": float,
    "home_score": "Int64",  # Int64 (com I maiúsculo) aceita valores nulos (NaN) para jogos futuros
    "away_score": "Int64",
})

# Convertendo as datas para horario de brasilia
snapshots_df['match_datetime_br'] = to_br_timezone(snapshots_df["match_datetime"])
snapshots_df['final_whistle_br'] = to_br_timezone(snapshots_df["final_whistle"])
snapshots_df = snapshots_df.drop(columns=['match_datetime', 'final_whistle'])

# removendo as linhas TBD
# snapshots_df = snapshots_df[snapshots_df['match_status'] != 'TBD'].copy()

# removendo as linhas repetidas de partidas já jogadas
# played_df = snapshots_df[snapshots_df['match_status'] == 'Played'].copy()
# not_played_df = snapshots_df[snapshots_df['match_status'] != 'Played'].copy()
# played_df_clean = played_df.drop_duplicates(subset=[col for col in snapshots_df.columns if col not in ['snapshot_br', 'final_whistle_br']], keep='last')
# snapshots_df = pd.concat([played_df_clean, not_played_df])

# adicionando os resultados das partidas em todas linhas (até as no futuro do snapshot)
played_df = snapshots_df[snapshots_df['match_status'] == 'Played'].copy()
snapshots_df = snapshots_df.drop(columns=['home_score', 'away_score', 'result', 'final_whistle_br', 'home_outcome', 'draw_outcome', 'away_outcome'])
played_subdf = played_df[['opta_match_id', 'final_whistle_br', 'home_score', 'away_score', 'result', 'home_outcome', 'draw_outcome', 'away_outcome']]
# print(played_df.shape)
final_snapshots_df = snapshots_df.merge(played_subdf, how='left', on=['opta_match_id'])


# criando a coluna de handles. Ex.: 'BRA x FRA'
final_snapshots_df['match_handle'] = final_snapshots_df['home_flag'] \
                                + " " \
                                + final_snapshots_df['home_code'] \
                                + ' x ' \
                                + final_snapshots_df['away_code'] \
                                + " " \
                                + final_snapshots_df['away_flag']

final_snapshots_df['match_handle_results'] = final_snapshots_df['home_flag'] \
                                + " " \
                                + final_snapshots_df['home_code'] \
                                + " " \
                                + final_snapshots_df['home_score'].astype(str) \
                                + ' x ' \
                                + final_snapshots_df['away_score'].astype(str) \
                                + " " \
                                + final_snapshots_df['away_code'] \
                                + " " \
                                + final_snapshots_df['away_flag']

# calculando o desempenho do modelo
final_snapshots_df['home_error'] = (final_snapshots_df['home_proba'] / 100 - final_snapshots_df['home_outcome']) ** 2
final_snapshots_df['draw_error'] = (final_snapshots_df['draw_proba'] / 100 - final_snapshots_df['draw_outcome']) ** 2
final_snapshots_df['away_error'] = (final_snapshots_df['away_proba'] / 100 - final_snapshots_df['away_outcome']) ** 2

final_snapshots_df['brier_score'] = final_snapshots_df['home_error'] + final_snapshots_df['draw_error'] + final_snapshots_df['away_error']
final_snapshots_df['model_grade'] = (1 - (final_snapshots_df['brier_score'] / 2)) * 100
final_snapshots_df = final_snapshots_df.drop(columns=['home_outcome', 'draw_outcome', 'away_outcome', 'home_error', 'draw_error', 'away_error'])

final_snapshots_df['prediction_time'] = final_snapshots_df.apply(
    lambda row: 'past' if row['final_whistle_br'] < row['snapshot_br'] else 'future', 
    axis=1
)

# ---- calculando o desempenho minuto-a-minuto
outcome_subdf = played_df[['opta_match_id', 'home_outcome', 'draw_outcome', 'away_outcome']]
match_live_predictions_df = match_live_predictions_df.merge(outcome_subdf, how='right', on=['opta_match_id'])
match_live_predictions_df['home_error'] = (match_live_predictions_df['Home'] / 100 - match_live_predictions_df['home_outcome']) ** 2
match_live_predictions_df['draw_error'] = (match_live_predictions_df['Draw'] / 100 - match_live_predictions_df['draw_outcome']) ** 2
match_live_predictions_df['away_error'] = (match_live_predictions_df['Away'] / 100 - match_live_predictions_df['away_outcome']) ** 2

match_live_predictions_df['brier_score'] = match_live_predictions_df['home_error'] + match_live_predictions_df['draw_error'] + match_live_predictions_df['away_error']
match_live_predictions_df['model_grade'] = (1 - (match_live_predictions_df['brier_score'] / 2)) * 100
match_live_predictions_df = match_live_predictions_df.drop(columns=['home_outcome', 'draw_outcome', 'away_outcome', 'home_error', 'draw_error', 'away_error'])

# salvando para visualizar em csv
final_snapshots_df.sort_values(by=['match_datetime_br', 'final_whistle_br', 'snapshot_br']).to_csv("../test.csv", index=False)

conn = sqlite3.connect("../data/db/world_cup.db")

final_snapshots_df.to_sql(
    name="opta_snapshots",  # Nome da tabela dentro do SQLite
    con=conn,  # A conexão que abrimos acima
    if_exists="replace",  # 'append' adiciona os dados novos. 'replace' reconstrói a tabela do zero.
    index=False,  # Não salva o índice do Pandas como uma coluna no banco
)

final_snapshots_df.to_csv("../snapshots.csv", index=False)

match_events_df.to_sql(
    name="match_events",  # Nome da tabela dentro do SQLite
    con=conn,  # A conexão que abrimos acima
    if_exists="replace",  # 'append' adiciona os dados novos. 'replace' reconstrói a tabela do zero.
    index=False,  # Não salva o índice do Pandas como uma coluna no banco
)

match_events_df.to_csv("../events.csv", index=False)

match_live_predictions_df.to_sql(
    name="live_predictions",  # Nome da tabela dentro do SQLite
    con=conn,  # A conexão que abrimos acima
    if_exists="replace",  # 'append' adiciona os dados novos. 'replace' reconstrói a tabela do zero.
    index=False,  # Não salva o índice do Pandas como uma coluna no banco
)

match_live_predictions_df.to_csv("../live_predictions.csv", index=False)

conn.close()
# %%
