# %%
from pathlib import Path
import json
import pandas as pd
import sqlite3
import countryflag as cf
from rich.progress import track

fifa_ranking_df = pd.read_csv('../data/etc/fifa_ranking_pre_wc.csv', encoding='utf-8')


def to_br_timezone(column):
    converted_col = column.dt.tz_convert(
    "America/Sao_Paulo").dt.tz_localize(None)

    return converted_col

fixture_files = [f.name for f in Path('../data/opta/fixture_jsons').iterdir() if f.is_file()]
fixture_files.sort()

dfs_list = []
event_dfs_list = []
live_predictions_dfs_list = []
match_events = {}
played_matches_ids = [] # saves the ids of played matches that were already processed
for file in track(fixture_files, description="Processing files"):

    snapshot = file.split('f')[0][1:][:-1]
    with open(f"../data/opta/fixture_jsons/{file}", 'r', encoding='utf-8') as f:
        data = json.load(f)

    matches = []
    for match_id in data.keys():

        match_data = data[match_id]

        matchInfo = match_data.get("matchInfo")

        if not matchInfo:
            # checker['match_status'] = 'TBD'
            # matches.append(checker)
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

        preMatchPredictions = match_data['liveData']['preMatchPredictions']

        for prediction in preMatchPredictions:
            for type in prediction['prediction']:
                checker[f"{type['type'].lower()}_proba"] = type['probability']

        match_results = match_data['liveData']['matchDetails']

        checker['match_status'] = match_results['matchStatus']

        if (checker['match_status'] == 'Played') & (match_id not in played_matches_ids):

            for period in match_results['period']:
                if period['id'] == len(match_results['period']):
                    checker['final_whistle'] = pd.to_datetime(period['end'])

            final_time = match_results['scores'].get('ft')
            extra_time = match_results['scores'].get('et')
            # penalties = match_results['scores'].get('pen')

            if extra_time:
                checker['home_score'] = extra_time['home']
                checker['away_score'] = extra_time['away']
            else:
                checker['home_score'] = final_time['home']
                checker['away_score'] = final_time['away']

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
            for event in match_data['liveData']['event']:
                for qualifier in event['qualifier']:
                    match_events.setdefault('opta_match_id', []).append(checker['opta_match_id'])
                    match_events.setdefault("event_id", []).append(event["id"])
                    match_events.setdefault("eventId", []).append(event["eventId"])
                    match_events.setdefault("typeId", []).append(event["typeId"])
                    match_events.setdefault("periodId", []).append(event["periodId"])
                    match_events.setdefault("timeMin", []).append(event["timeMin"])
                    match_events.setdefault("timeSec", []).append(event["timeSec"])
                    match_events.setdefault("playerId", []).append(event.get("playerId"))
                    match_events.setdefault("playerName", []).append(event.get("playerName"))
                    match_events.setdefault("contestantId", []).append(event["contestantId"])
                    match_events.setdefault("outcome", []).append(event["outcome"])
                    match_events.setdefault("x", []).append(event["x"])
                    match_events.setdefault("y", []).append(event["y"])
                    match_events.setdefault("timeStamp", []).append(event["timeStamp"])
                    match_events.setdefault("lastModified", []).append(event["lastModified"])
                    match_events.setdefault("qualifier_id", []).append(qualifier["id"])
                    match_events.setdefault("qualifierId", []).append(qualifier["qualifierId"])
                    match_events.setdefault("value", []).append(qualifier.get("value"))

            played_matches_ids.append(match_id)
        matches.append(checker)

    dataframe = pd.DataFrame(matches)
    dfs_list.append(dataframe)

match_events_df = pd.DataFrame(match_events)
# del match_events
# match_events_df = match_events_df.drop_duplicates()

snapshots_df = pd.concat(dfs_list, ignore_index=True)

# deixando as colunas lower case para consistencia
snapshots_df.columns = [col.lower() for col in snapshots_df.columns]

# colocando as coluans numéricas como números
for col in ['home_proba', 'away_proba', 'draw_proba', 'home_score', 'away_score']:
    snapshots_df[col] = pd.to_numeric(snapshots_df[col])

# Convertendo as datas para horario de brasilia
snapshots_df['match_datetime_br'] = to_br_timezone(snapshots_df["match_datetime"])
snapshots_df['final_whistle_br'] = to_br_timezone(snapshots_df["final_whistle"])
snapshots_df = snapshots_df.drop(columns=['match_datetime', 'final_whistle'])

# criando a coluna de handles. Ex.: 'BRA x FRA'
snapshots_df['match_handle'] = snapshots_df['home_code'] + ' x ' + snapshots_df['away_code']

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
played_subdf = played_df[['opta_match_id', 'match_handle', 'final_whistle_br', 'home_score', 'away_score', 'result', 'home_outcome', 'draw_outcome', 'away_outcome']]

final_snapshots_df = snapshots_df.merge(played_subdf, how='left', on=['opta_match_id', 'match_handle'])

# calculando o desempenho do modelo
final_snapshots_df['home_error'] = (final_snapshots_df['home_proba'] / 100 - final_snapshots_df['home_outcome']) ** 2
final_snapshots_df['draw_error'] = (final_snapshots_df['draw_proba'] / 100 - final_snapshots_df['draw_outcome']) ** 2
final_snapshots_df['away_error'] = (final_snapshots_df['away_proba'] / 100 - final_snapshots_df['away_outcome']) ** 2

final_snapshots_df['brier_score'] = final_snapshots_df['home_error'] + final_snapshots_df['draw_error'] + final_snapshots_df['away_error']
final_snapshots_df['model_grade'] = (1 - (final_snapshots_df['brier_score'] / 2)) * 100
final_snapshots_df = final_snapshots_df.drop(columns=['home_outcome', 'draw_outcome', 'away_outcome', 'home_error', 'draw_error', 'away_error'])

final_snapshots_df['prediction_time'] = final_snapshots_df.apply(
    lambda row: 'future' if row['final_whistle_br'] > row['snapshot_br'] else 'past', 
    axis=1
)

# salvando para visualizar em csv
final_snapshots_df.sort_values(by=['match_datetime_br', 'final_whistle_br', 'snapshot_br']).to_csv("../test.csv", index=False)

conn = sqlite3.connect("../data/db/world_cup.db")

final_snapshots_df.to_sql(
    name="opta_snapshots",  # Nome da tabela dentro do SQLite
    con=conn,  # A conexão que abrimos acima
    if_exists="replace",  # 'append' adiciona os dados novos. 'replace' reconstrói a tabela do zero.
    index=False,  # Não salva o índice do Pandas como uma coluna no banco
)

conn.close()
# %%
