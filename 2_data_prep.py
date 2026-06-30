
# %%
import pandas as pd

matches = pd.read_csv("archive/matches.csv")
teams = pd.read_csv("archive/teams.csv")

matches['timestamp'] = pd.to_datetime(matches['date'] + " " + matches['kickoff_time_utc'], format="%Y-%m-%d %H:%M", errors='raise')

matches = matches[['timestamp', 'home_team_id', 'away_team_id', 'status']]
teams = teams[['team_id', 'team_name', 'fifa_code', 'fifa_ranking_pre_tournament']]

df = matches.merge(teams.add_prefix('home_'), on='home_team_id', how='left')
df = df.merge(teams.add_prefix('away_'), on='away_team_id', how='left')

df['rank_diff'] = df['home_fifa_ranking_pre_tournament'] - df['away_fifa_ranking_pre_tournament']

def whos_favorite(x):
    if x < 0:
        return 'home'
    elif x > 0:
        return 'away'

df['favorite'] = df['rank_diff'].apply(whos_favorite)

df['balance'] = df['rank_diff'].apply(lambda x: 'evenly_matched' if abs(x) <= 5 else 'one_sided')

view = df[[
    'home_team_name',
    'away_team_name',
    'home_fifa_ranking_pre_tournament',
    'away_fifa_ranking_pre_tournament',
    'rank_diff',
    'favorite',
    'balance'
    ]]
# %%