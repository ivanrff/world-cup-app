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

# Funções auxiliares
def log(message):
    global run_log
    global run_id
    entry = f"[{run_id}][{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {message}"
    print(entry)

    run_log = run_log + "\n" + entry

def timestamp_suffix():
    return datetime.now().strftime("%Y%m%d%H%M%S")
def day_suffix():
    return datetime.now().strftime("%Y%m%d")

def end_run(message=""):
    if len(message) > 0:
        log(message)
        log("Ending the application...")
        raise SystemExit("Ending the application")
    else:
        raise SystemExit("No ending message set. Ending the application")

run_log = ""
run_id = timestamp_suffix()

# headers para o request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Referer': 'https://theanalyst.com/competition/fifa-world-cup/fixtures',
}

# ID da competição (mantenha o que funcionou)
tournament_id = "1mjq6w6ezkxe611ykkj8rgz7f1"

fixtures_html_filepath = f'data/opta/fixture_htmls/[{run_id}]fixtures_{timestamp_suffix()}.html'

# CAPTURANDO OS IDS DOS JOGOS (Via HTML da página principal)
log(f"Accessing Opta's fixtures page...")
try:
    fixtures_url = "https://theanalyst.com/competition/fifa-world-cup/fixtures"
    fixtures_html_response = requests.get(fixtures_url, headers=headers)

    if fixtures_html_response:
        log(f"Response acquired, saving to {fixtures_html_filepath}")

        fixtures_html = fixtures_html_response.text
        with open(fixtures_html_filepath, 'w', encoding='utf-8') as file:
            file.write(fixtures_html)

    else:
        end_run("Got an empty a response from Opta.")
    
except Exception as e:
    end_run("Failed to connect to Opta's fixtures page")

soup = BeautifulSoup(fixtures_html, 'html.parser')

# Pegando o conteúdo JSON dentro de uma tag <script class="data" type="application/json">.
container = soup.find('script', class_='data', type='application/json')

if container:
    log("BeautifulSoup found the tag with the JSON containing the match ids. Extracting the data...")
    # Converte o texto do script em um dicionário Python
    try:
        page_data = json.loads(container.string)
    except Exception as e:
        end_run("Failed to convert the JSON into a Python dictionary")


match_ids = []

# Varre cada data do calendário
for date_block in page_data.get("matchDate", []):
    # Varre cada jogo que acontece naquela data
    for match in date_block.get("match", []):
        match_id = match.get("id")
        if match_id:
            match_ids.append(match_id)

log(f"Found a total of {len(match_ids)} match ids")

# Checar se a lista é igual à anterior
fixture_id_files = [f.name for f in Path('data/opta/fixture_ids').iterdir() if f.is_file()]
latest_fixture_id_file = max(fixture_id_files) if fixture_id_files else None

# comparar a lista de match_ids com o conteúdo do arquivo mais recente
if latest_fixture_id_file:
    log("Found a list of fixture ids in data/opta/fixture_ids")
    with open(f'data/opta/fixture_ids/{latest_fixture_id_file}', 'r', encoding='utf-8') as file:
        previous_match_ids = json.load(file)

    if Counter(match_ids) != Counter(previous_match_ids):
        log("The match ids are different from the previous ones. Saving the new list...")
        with open(f'data/opta/fixture_ids/[{run_id}]fixture_ids_{timestamp_suffix()}.json', 'w', encoding='utf-8') as file:
            json.dump(match_ids, file, indent=4, ensure_ascii=False)
    else:
        log("The match ids are the same from the recorded list. No need to save a new list.")
else:
    log("No previous fixture ids file found. Saving the new list...")
    with open(f'data/opta/fixture_ids/[{run_id}]fixture_ids_{timestamp_suffix()}.json', 'w', encoding='utf-8') as file:
        json.dump(match_ids, file, indent=4, ensure_ascii=False)

# Loop de coleta das probabilidades
final_data = {}

for match_id in track(match_ids, description="Processing match ids"):
    log(f"Collecting match: {match_id}...")
    
    url_api = f"https://api.performfeeds.com/soccerdata/matchlivewinprobability/{tournament_id}/{match_id}"
    
    # O parâmetro _clbk pode ser o mesmo, a API aceita qualquer string ali
    params = {
        '_rt': 'c',
        '_fmt': 'jsonp',
        '_clbk': '_33a835a45b8f4360977d3aa6bc55a6d6',
    }
    
    try:
        response = requests.get(url_api, params=params, headers=headers)
        
        if response.status_code == 200:
            match = re.search(r'\((.*)\)', response.text)
            if match:
                jogo_json = json.loads(match.group(1))
                
                # Salva o resultado no dicionário central usando o ID do jogo como chave
                final_data[match_id] = jogo_json
                
        else:
            log(f"Erro {response.status_code} no jogo {match_id}")
            
    except Exception as e:
        log(f"Falha ao processar jogo {match_id}: {e}")
    
    # descanso de 1 segundo para não tomar block de IP
    time.sleep(1)

# Salva todos os jogos juntos
fixtures_json_filepath = f'data/opta/fixture_jsons/[{run_id}]fixtures_json_{timestamp_suffix()}.json'
with open(fixtures_json_filepath, 'w', encoding='utf-8') as file:
    json.dump(final_data, file, indent=4, ensure_ascii=False)

log(f"Successfully finished processing. Saved data to '{fixtures_json_filepath}'")

Path(fixtures_html_filepath).unlink(missing_ok=True)

log(f"Deleted original html file.")

# Salvar o log no diretorio log/
log_filepath = f'log/[{run_id}]opta_scrapper_log_{timestamp_suffix()}.txt'
with open(log_filepath, 'w', encoding='utf-8') as log_file:
    log_file.write(run_log)