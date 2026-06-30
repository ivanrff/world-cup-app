import json
import re
import time
import requests
from bs4 import BeautifulSoup
import os

# 1. PREPARANDO AS CREDENCIAIS (O que você já validou que funciona)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Referer': 'https://theanalyst.com/competition/fifa-world-cup/fixtures',
}

# ID da competição (mantenha o que funcionou)
id_competicao = "1mjq6w6ezkxe611ykkj8rgz7f1"

if os.path.exists('fixtures.html'):
    with open('fixtures.html', 'r', encoding='utf-8') as file:
        fixtures_html = file.read()
else:
    # 2. CAPTURANDO OS IDS DOS JOGOS (Via HTML da página principal)
    print("Buscando a lista de jogos...")
    url_principal = "https://theanalyst.com/competition/fifa-world-cup/fixtures"
    res_principal = requests.get(url_principal, headers=headers)

    print(res_principal.text)

    with open('fixtures.html', 'w', encoding='utf-8') as file:
        file.write(res_principal.text)

    fixtures_html = res_principal.text

soup = BeautifulSoup(fixtures_html, 'html.parser')


# Aqui pegamos os IDs das divs que contêm os confrontos.
# Baseado no seu HTML anterior, eles ficam dentro da AnnotationLayer
container = soup.find('script', class_='data', type='application/json')

if container:
    # 2. Converte o texto do script em um dicionário Python
    dados_da_pagina = json.loads(container.string)

ids_jogos = []

# Varre cada data do calendário
for bloco_data in dados_da_pagina.get("matchDate", []):
    # Varre cada jogo que acontece naquela data
    for jogo in bloco_data.get("match", []):
        id_partida = jogo.get("id")
        if id_partida:
            ids_jogos.append(id_partida)

print(f"Total de IDs de partidas encontrados: {len(ids_jogos)}")
print("Exemplo dos primeiros IDs:", ids_jogos[:5])

# 3. LOOP DE COLETA DAS PROBABILIDADES
dados_finais = {}

for id_jogo in ids_jogos:
    print(f"Coletando dados do jogo: {id_jogo}...")
    
    url_api = f"https://api.performfeeds.com/soccerdata/matchlivewinprobability/{id_competicao}/{id_jogo}"
    
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
                
                # Salva o resultado no nosso dicionário central usando o ID do jogo como chave
                dados_finais[id_jogo] = jogo_json
                
        else:
            print(f"Erro {response.status_code} no jogo {id_jogo}")
            
    except Exception as e:
        print(f"Falha ao processar jogo {id_jogo}: {e}")
    
    # Boas práticas: dê um descanso de 1 segundo entre as requisições para não ser bloqueado por IP
    time.sleep(1)

# 4. SALVANDO TODOS OS JOGOS JUNTOS
with open('todos_os_jogos.json', 'w', encoding='utf-8') as file:
    json.dump(dados_finais, file, indent=4, ensure_ascii=False)

print("Processo concluído! Todos os dados salvos em 'todos_os_jogos.json'")