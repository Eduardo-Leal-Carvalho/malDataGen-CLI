import http.client
import json
import sys
from configparser import ConfigParser
import urllib.request
from tabulate import tabulate



def download_file(url, filename):
    # Abre a URL
    with urllib.request.urlopen(url) as response:
        # Obtém o tamanho total do arquivo (em bytes)
        total_size = int(response.getheader('Content-Length').strip())
        total_mb = total_size / (1024 * 1024)

        print(f"Tamanho total do arquivo: {total_mb:.2f} MB")

        downloaded_size = 0
        block_size = 1024 * 64  # 64 KB por leitura

        with open(filename, 'wb') as out_file:
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)

                # Atualiza progresso
                downloaded_size += len(buffer)
                downloaded_mb = downloaded_size / (1024 * 1024)
                remaining_mb = total_mb - downloaded_mb

                print(f"\rBaixado: {downloaded_mb:.2f} MB | Restante: {remaining_mb:.2f} MB", end='')

        print("\nDownload concluído!")

def send_request(operation,endpoint, payload, headers, base_url):
    conn = http.client.HTTPSConnection(base_url)
    conn.request(operation, endpoint, payload, headers)
    res = conn.getresponse()
    return res.read().decode("utf-8")

# ===== SIGN IN  =====
def signIn(configObject, userinfo,hostinfo):
    payload = json.dumps({
        "email": userinfo["email"],
        "password": userinfo["password"],
        "returnSecureToken": True
    })
    headers = {'Content-Type': 'application/json'}
    json_str = send_request("POST", f"/v1/accounts:signInWithPassword?key={hostinfo['firebaseapikey']}", payload, headers, hostinfo["googleapiurl"])
    data = json.loads(json_str)
    idToken = data["idToken"]
    print(json_str)
    userinfo["idtoken"] = idToken
    with open('config.ini', 'w') as conf:
        configObject.write(conf)

# ===== PRINT PARAMETERS  =====
def printParameters(paramsList):

    # Prepara itens para o tabulate
    tableRows = []
    for p in paramsList:
        tableRows.append({
            "Name": p.get("name", ""),
            "Type": p.get("type", ""),
            "Default": p.get("default_value", ""),
        })

    # Exibe tabela
    print(tabulate(tableRows, headers="keys", tablefmt="grid"))


# ===== DATASETS =====
def getDatasets(userinfo,hostinfo):
    payload = ""    
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", "/dataset", payload, headers, hostinfo["baseurl"]))
    
    datasets = []

    for edge in jsonData["edges"]:
        node = edge["node"]

        # Criar dicionário limpo
        datasets.append({
            "seq": node["seq"],
            "id": node["id"],
            "description": node["description"],
        })
    print(tabulate(datasets, headers="keys", tablefmt="grid"))


def getDataset(userinfo,hostinfo,datasetID):
    payload = ""    
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", f"/dataset/{datasetID}", payload, headers, hostinfo["baseurl"]))
    print(jsonData)
    
    dataset = []

    # Criar dicionário limpo
    dataset.append({
        "seq": jsonData["seq"],
        "id": jsonData["id"],
        "description": jsonData["description"],
    })
    print(tabulate(dataset, headers="keys", tablefmt="grid"))
    
    
# ===== PROCESSORS =====
def getProcessors(userinfo,hostinfo):
    payload = ""    
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", f"/processor?skip=0&take=20&sort=%5B%7B%22field%22:%22id%22,%20%22order%22:%22ASC%22%7D%5D", payload, headers, hostinfo["baseurl"]))    
    
    processors = []

    for edge in jsonData["edges"]:
        node = edge["node"]

        # Criar dicionário limpo
        processors.append({
            "seq": node["seq"],
            "id": node["id"],
            "name": node["name"],
            "version": node["version"]
        })
    
    print(tabulate(processors, headers="keys", tablefmt="grid"))
    if("y" == input("Deseja visualizar parametros de algum processador? (y/n): ")):
        procID = int(input("Digite a seq do processador: "))
        printParameters(jsonData['edges'][procID-1]['node']['configuration']['parameters'])



def getProcessor(userinfo,hostinfo, processorID):
    payload = ""    
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", f"/processor/{processorID}", payload, headers, hostinfo["baseurl"]))

    processor = []

    # Criar dicionário limpo
    processor.append({
        "seq": jsonData["seq"],
        "id": jsonData["id"],
        "name": jsonData["name"],
        "version": jsonData["version"]
    })
    print(tabulate(processor, headers="keys", tablefmt="grid"))

def percorreListaProcesses(data):
    listMetrics = []
    listResults = []
    listProcessor = []
    listDataset = []

    for edge in data.get("edges", []):
        node = edge.get("node", {})
        
        for key, value in node.items():
            if key == "metrics_file" and "public_url" in value:
                listMetrics.append({"id":value["id"],"public_url":value["public_url"]})
            if key == "result_file" and "public_url" in value:
                listResults.append({"id":value["id"],"public_url":value["public_url"]})
            if key == "processor" and "name" in value:
                listProcessor.append({"id":value["id"],"name":value["name"]})
            if key == "dataset" and "description" in value:
                listDataset.append({"id":value["id"],"description":value["description"]})

    return listMetrics, listResults, listProcessor, listDataset

def getProcesses(userinfo,hostinfo):
    payload = ""
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    json_str = send_request("GET", f"/processing", payload, headers, hostinfo["baseurl"])
    data = json.loads(json_str)
    metrics, results, processors, datasets = percorreListaProcesses(data)

    print(len(metrics),"processes encontrados")
    for i in range(len(metrics)):
        print(f"id [{metrics[i]['id']}] | {processors[i]['name']} | {datasets[i]['description']}")
    
    resp = input("Deseja baixar as metrics e results de todos os arquivos? (s/n): ")

    if resp.lower() == 's':
        print("Criando pasta zips")
        for i in range(len(metrics)):
            print(f"Baixando Metrics [{metrics[i]['id']}]...")
            download_file(metrics[i]["public_url"], f"zips/dataset{metrics[i]['id']}.zip")
            print(f"Baixando Results [{metrics[i]['id']}]...")
            download_file(results[i]["public_url"], f"zips/results{results[i]['id']}.zip")

def getProcesse(userinfo,hostinfo,id):
    payload = ""
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    json_str = send_request("GET", f"/processing/{id}", payload, headers, hostinfo["baseurl"])
    data = json.loads(json_str)
    if len(data) != 0:
        print(f"processe {data['id']} encontrado")
        print(f"ID [{data['id']}] | {data['processor']['name']} | {data['dataset']['description']}")
        resp = input("Deseja baixar as metrics e results de todos os arquivos? (s/n): ")

        if resp.lower() == 's':
            print("Criando pasta")
            print(f"Baixando Metrics...")
            download_file(data["metrics_file"]["public_url"], f"zips/metrics_{data['id']}.zip")
            print(f"Baixando Results...")
            download_file(data["result_file"]["public_url"], f"zips/results{data['id']}.zip")
        
    
def requestDatasetProcessing(userinfo,hostinfo, processorID,datasetID):
    payload = json.dumps({
        "processor_id": processorID,
        "dataset_id": datasetID,
        "parameters": [{
                "name": "num_samples_class_malware",
                "value": "20"
            },
            {
                "name": "num_samples_class_benign",
                "value": "20"
        }]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {userinfo['idtoken']}"
    }
    print(send_request("POST", "/processing", payload, headers, hostinfo["baseurl"]))

def help():
    help_text = """
    Uso: python3 app.py <comando> [parâmetros]

    Comandos disponíveis:

      signin
          Faz login com o usuário definido no config.ini e obtém o token de autenticação.

      getdatasets
          Lista todos os datasets disponíveis no servidor.

      getdataset <datasetID>
          Mostra informações de um dataset específico.

      getprocessors
          Lista todos os processadores disponíveis.

      getprocessor <processorID>
          Mostra informações de um processador específico.

      requestprocessing <processorID> <datasetID>
          Solicita o processamento de um dataset por um processador.

      getprocesses
          Lista processos já realizados e oferece opção para baixar métricas e resultados.

      getprocesse <processID>
          Mostra informações de um processo específico e oferece opção para baixar seus arquivos.

      help
          Exibe esta mensagem de ajuda.

    Exemplo de uso:
      python app.py signin
      python app.py getdataset 12345
      python app.py getprocesse 102510
      python app.py requestprocessing 12345 102510 
    """
    print(help_text)

    

# ===== CLI HANDLER =====
def main():
    config_object = ConfigParser()
    config_object.read("config.ini")
    userinfo = config_object["USERINFO"]
    hostinfo = config_object["HOSTINFO"]

    cmd = sys.argv[1].lower()

    if cmd == "signin":
        signIn(config_object,userinfo,hostinfo)
    elif cmd == "getdatasets":
        getDatasets(userinfo,hostinfo)
    elif cmd == "getdataset" and len(sys.argv) > 2:
        getDataset(userinfo,hostinfo,sys.argv[2])
    elif cmd == "getprocessors":
        getProcessors(userinfo,hostinfo)
    elif cmd == "getprocessor" and len(sys.argv) > 2:
        getProcessor(userinfo,hostinfo,sys.argv[2])
    elif cmd == "requestprocessing" and len(sys.argv) > 2:
        requestDatasetProcessing(userinfo,hostinfo,sys.argv[2],sys.argv[3])
    elif cmd == "getprocesses":
        getProcesses(userinfo,hostinfo)
    elif cmd == "getprocesse" and len(sys.argv) > 2:
        getProcesse(userinfo,hostinfo, sys.argv[2])
    elif cmd == "help":
        help()
    else:
        print("Comando inválido ou parâmetros insuficientes.")
        print("Utilize o comando help para informações dos coomandos ")


if __name__ == "__main__":
    main()
