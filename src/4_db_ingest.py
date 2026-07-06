# %%
from pathlib import Path
import json
import pandas as pd
import sqlite3


def to_br_timezone(column):
    converted_col = column.dt.tz_convert(
    "America/Sao_Paulo").dt.tz_localize(None)

    return converted_col

fixture_files = [f.name for f in Path('../data/opta/fixture_jsons').iterdir() if f.is_file()]
fixture_files.sort()

dfs_list = []
for file in fixture_files:

    snapshot = file.split('f')[0][1:][:-1]
    with open(f"../data/opta/fixture_jsons/{file}", 'r', encoding='utf-8') as f:
        data = json.load(f)

    matches = []
    for i, id in enumerate(data.keys()):

        match_id = id

        match = data[match_id]

        checker = {}

        checker['opta_match_id'] = id
        checker['snapshot_br'] = pd.to_datetime(snapshot, format="%Y%m%d%H%M%S")

        matchInfo = match.get("matchInfo", None)

        if not matchInfo:
            checker['match_status'] = 'TBD'
            matches.append(checker)
            continue

        checker['match_datetime'] = pd.to_datetime(matchInfo['date'] + matchInfo['time'], format="%Y-%m-%dZ%H:%M:%S%z")

        checker['stage'] = matchInfo['stage'].get('name')

        if checker['stage'].lower() == 'group stage':
            checker['group'] = matchInfo['series'].get('name')
        
        for team in range(2):
            position = matchInfo['contestant'][team].get('position')
            team_code = matchInfo['contestant'][team].get('code')

            checker[f'{position}_code'] = team_code

        preMatchPredictions = match['liveData']['preMatchPredictions']

        for prediction in preMatchPredictions:
            for type in prediction['prediction']:
                checker[f"{type['type'].lower()}_proba"] = type['probability']

        match_results = match['liveData']['matchDetails']

        checker['match_status'] = match_results['matchStatus']

        if checker['match_status'] == 'Played':

            for period in match_results['period']:
                if period['id'] == len(match_results['period']):
                    checker['final_whistle'] = pd.to_datetime(period['end'])


            checker['home_score'] = match_results['scores']['ft']['home']
            checker['away_score'] = match_results['scores']['ft']['away']
            if checker['home_score'] > checker['away_score']:
                checker['result'] = 'Home Win'
                home_outcome, draw_outcome, away_outcome = 1, 0, 0
            elif checker['home_score'] < checker['away_score']:
                checker['result'] = 'Away Win'
                home_outcome, draw_outcome, away_outcome = 0, 0, 1
            else:
                checker['result'] = 'Draw'
                home_outcome, draw_outcome, away_outcome = 0, 1, 0

            home_error = (float(checker['home_proba']) / 100 - home_outcome) ** 2
            draw_error = (float(checker['draw_proba']) / 100 - draw_outcome) ** 2
            away_error = (float(checker['away_proba']) / 100 - away_outcome) ** 2

            checker['brier_score'] = home_error + draw_error + away_error
            checker['model_grade'] = (1 - (checker['brier_score'] / 2)) * 100

        matches.append(checker)
    
    dataframe = pd.DataFrame(matches)
    dfs_list.append(dataframe)

final_df = pd.concat(dfs_list, ignore_index=True)

# deixando as colunas lower case para consistencia
final_df.columns = [col.lower() for col in final_df.columns]

# colocando as coluans numéricas como números
for col in ['home_proba', 'away_proba', 'draw_proba', 'home_score', 'away_score']:
    final_df[col] = pd.to_numeric(final_df[col])

# Convertendo as datas para horario de brasilia
final_df['match_datetime_br'] = to_br_timezone(final_df["match_datetime"])
final_df['final_whistle_br'] = to_br_timezone(final_df["final_whistle"])
final_df = final_df.drop(columns=['match_datetime', 'final_whistle'])

# criando a coluna de handles. Ex.: 'BRA x FRA'
final_df['match_handle'] = final_df['home_code'] + ' x ' + final_df['away_code']

# removendo as linhas repetidas de partidas já jogadas
played_df = final_df[final_df['match_status'].isin(['Played', 'TBD'])]
other_df = final_df[~final_df['match_status'].isin(['Played', 'TBD'])]
final_df_clean = played_df.drop_duplicates(subset=[col for col in final_df.columns if col not in ['snapshot_br', 'final_whistle_br']], keep='last')
final_df_clean = pd.concat([final_df_clean, other_df])

# salvando para visualizar em csv
final_df_clean.sort_values(by=['match_datetime_br', 'final_whistle_br', 'snapshot_br']).to_csv("../test.csv", index=False)

conn = sqlite3.connect("../data/db/world_cup.db")

final_df_clean.to_sql(
    name="opta_snapshots",  # Nome da tabela dentro do SQLite
    con=conn,  # A conexão que abrimos acima
    if_exists="replace",  # 'append' adiciona os dados novos. 'replace' reconstrói a tabela do zero.
    index=False,  # Não salva o índice do Pandas como uma coluna no banco
)

conn.close()

final_df_clean.head(5)
# %%
