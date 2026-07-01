# %%
from pathlib import Path
import json

fixture_files = [f.name for f in Path('data/opta/fixture_jsons').iterdir() if f.is_file()]

# print(fixture_files)
file = max(fixture_files)
# for file in fixture_files:
    # print(file)
with open(f"data/opta/fixture_jsons/{file}", 'r', encoding='utf-8') as f:
    data = json.load(f)

dictionary = {}
for i, id in enumerate(data.keys()):

    match_id = id

    # if match_id == 'b083yrj18tbck1z0og2evbhuc':
    #     break

    match = data[match_id]

    checker = {}
    checker['opta_match_id'] = id
    # checker['match_id'] = i + 1

    matchInfo = match.get("matchInfo", None)

    if not matchInfo:
        break

    checker['match_date'] = matchInfo['date']
    checker['match_time'] = matchInfo['time']

    checker['stage'] = matchInfo['stage'].get('name')

    if checker['stage'].lower() == 'group stage':
        checker['group'] = matchInfo['series'].get('name')
    else:
        checker['group'] = None
    
    checker['team_1'] = matchInfo['contestant'][0].get('code')
    checker['team_1_pos'] = matchInfo['contestant'][0].get('position')
    checker['team_2'] = matchInfo['contestant'][1].get('code')
    checker['team_2_pos'] = matchInfo['contestant'][1].get('position')

    preMatchPredictions = match['liveData']['preMatchPredictions']

    for k, prediction in enumerate(preMatchPredictions):
        for type in prediction['prediction']:
            checker[f"{type['type']}_{k}"] = type['probability']


    dictionary[i + 1] = checker
# %%
