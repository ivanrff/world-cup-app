# %%
from pathlib import Path
import json
import pandas as pd
import sqlite3
import countryflag as cf
from rich.progress import track

fifa_ranking_df = pd.read_csv('../data/etc/fifa_ranking_pre_wc.csv', encoding='utf-8')
qualify_files = sorted([f.name for f in Path('../data/opta/qualify_jsons').iterdir() if f.is_file()])

dfs_list = []
for file in track(qualify_files, description="Processing files"):

    snapshot = file.split('q')[0][1:][:-1]
    with open(f"../data/opta/qualify_jsons/{file}", 'r', encoding='utf-8') as f:
        data = json.load(f)

    # print(snapshot)

    stages = data['stages']['stage']

    # probabilityOfQualifying 1
    # probabilityOfWinning 2
    # averagePoints 3
    # pointsDistribution 4
    # rankDistribution 5

    for i, stage in enumerate(stages):
        if stage['name'] == "Group Stage":
            stages.pop(i)
            break

    df = pd.json_normalize(
        data["stages"]["stage"],
        record_path=["contestants", "contestant", "predictions", "predicted"],
        meta=[
            "name",
            "id",
            ["contestants", "contestant", "id"],
            ["contestants", "contestant", "name"],
            ["contestants", "contestant", "predictions", "lastUpdated"],
        ],
        # record_prefix="pred_",
        # meta_prefix="stage_",
        # errors="ignore",
    )

    # 1. Colunas que NÃO vão para o índice (as que viram colunas/valores ou a original desdobrada)
    df['snapshot_br'] = pd.to_datetime(snapshot, format="%Y%m%d%H%M%S")

    dfs_list.append(df)
    
df = pd.concat(dfs_list, ignore_index=True)

df['typeId'] = "typeId_" + df['typeId'].astype(str)
cols_to_exclude = ['typeId', 'value']

# 2. Pega todas as colunas do DataFrame, exceto as da lista acima
index_cols = [col for col in df.columns if col not in cols_to_exclude]

df['value'] = pd.to_numeric(df['value'].str.replace("%", ""))
# 3. Faz o pivot normalmente
df = df.pivot(
    index=index_cols,
    columns='typeId',
    values='value'
).reset_index()

df.columns.name = None

# for snapshot in df['snapshot_br'].unique():
#     print(snapshot)
#     print(df.loc[df['snapshot_br'] == snapshot, "contestants.contestant.predictions.lastUpdated"].nunique())

df.columns = ['stage_name', 'stage_id', "contestant_id", 'contestant_name', 'last_updated', 'snapshot_br', 'typeId_1', 'typeId_2']

test_df = df
test_df.to_csv("../test.csv", index=False)
# %%
