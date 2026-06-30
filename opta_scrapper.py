import json
import re
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
    'Accept': '*/*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Sec-Fetch-Storage-Access': 'none',
    'Alt-Used': 'api.performfeeds.com',
    'Connection': 'keep-alive',
    # Ajuste aqui caso continue dando 403:
    'Referer': 'https://theanalyst.com/competition/fifa-world-cup/fixtures',
    'Sec-Fetch-Dest': 'script',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
}

params = {
    '_rt': 'c',
    '_fmt': 'jsonp',
    '_clbk': '_33a835a45b8f4360977d3aa6bc55a6d6',
}

response = requests.get(
    'https://api.performfeeds.com/soccerdata/matchlivewinprobability/1mjq6w6ezkxe611ykkj8rgz7f1/3hsg9oklerq6uua8pos3dmdck',
    params=params,
    headers=headers,
)

if response.status_code == 200:
    print("Requisição bem-sucedida! Tratando os dados...")
    
    # Expressão regular para pegar tudo o que está dentro dos parênteses do JSONP
    match = re.search(r'\((.*)\)', response.text)
    
    if match:
        json_string_limpa = match.group(1)
        
        # Converte a string limpa em um dicionário Python para garantir a validade
        dados_json = json.loads(json_string_limpa)
        
        # Salva o JSON formatado e identado (bonito para ler)
        with open('tests.json', 'w', encoding='utf-8') as file:
            json.dump(dados_json, file, indent=4, ensure_ascii=False)
            
        print("Arquivo 'tests.json' salvo com sucesso e pronto para análise!")
    else:
        print("Não foi possível extrair o JSON de dentro do formato JSONP.")
else:
    print(f"Erro {response.status_code}. O servidor bloqueou a requisição.")
    print("Dica: Verifique os cookies ou tente atualizar o 'Referer'.")