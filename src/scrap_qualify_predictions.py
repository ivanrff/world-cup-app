#%%%
import json
import re
import time
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
from rich.progress import track
from pathlib import Path
from collections import Counter
from utils.get_played_match_ids import get_played_match_ids

# # Funções auxiliares
# def log(message):
#     global run_log
#     global run_id
#     entry = f"[{run_id}][{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {message}"
#     print(entry)

#     run_log = run_log + "\n" + entry

# def timestamp_suffix():
#     return datetime.now().strftime("%Y%m%d%H%M%S")
# def day_suffix():
#     return datetime.now().strftime("%Y%m%d")

# def end_run(message=""):
#     if len(message) > 0:
#         log(message)
#         log("Ending the application...")
#         raise SystemExit("Ending the application")
#     else:
#         raise SystemExit("No ending message set. Ending the application")

# run_log = ""
# run_id = timestamp_suffix()

def save_qualify_predictions_json(log, end_run, timestamp_suffix, run_id):
    # headers para o request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Sec-Fetch-Storage-Access': 'none',
        'Alt-Used': 'api.performfeeds.com',
        'Connection': 'keep-alive',
        'Referer': 'https://theanalyst.com/',
        'Sec-Fetch-Dest': 'script',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }

    params = {
        'tmcl': '873cbl9cd9butm4air0mugxzo',
        '_fmt': 'jsonp',
        '_rt': 'c',
        '_clbk': 'TM18_873cbl9cd9butm4air0mugxzo_df2cbce48b194b7ebf70b98b0668037f',
    }

    # ID da competição (mantenha o que funcionou)
    tournament_id = "1mjq6w6ezkxe611ykkj8rgz7f1"

    # CAPTURANDO OS IDS DOS JOGOS (Via HTML da página principal)
    log(f"Accessing Opta's fixtures page...")
    try:
        qualify_url = f"https://api.performfeeds.com/soccerdata/seasonandtournamentsimulations/{tournament_id}"
        
        qualify_response = requests.get(qualify_url, params=params, headers=headers)

        if qualify_response.status_code == 200:
            if qualify_response:
                qualify_json_filepath = f'../data/opta/qualify_jsons/[{run_id}]qualify_json_{timestamp_suffix()}.json'
                log(f"Response acquired, saving to {qualify_json_filepath}")

                qualify_response_clean = re.search(r'\((.*)\)', qualify_response.text) # busca tudo que está dentro de parêntesess
                qualify_json = json.loads(qualify_response_clean.group(1))

                with open(qualify_json_filepath, 'w', encoding='utf-8') as file:
                    json.dump(qualify_json, file, indent=4, ensure_ascii=False)

            else:
                end_run("Got an empty a response from Opta.")
        else:        
            end_run("Failed to get a 200 status response.")
        
    except Exception as e:
        end_run(f"Failed to access Opta's qualifying predictions. Error: {e}")
# %%