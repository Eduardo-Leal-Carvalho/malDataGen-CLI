import http.client
import json
import sys
from configparser import ConfigParser
import urllib.request
import os
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
    
    if "idToken" not in data:
        print("Erro ao obter token de autenticação.")
        print("Resposta do servidor:", json_str)
        return

    idToken = data["idToken"]
    userinfo["idtoken"] = idToken
    with open('config.ini', 'w') as conf:
        configObject.write(conf)
    print("Login realizado com sucesso! Token atualizado.")

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
    
    if "edges" not in jsonData:
        print("Erro: A resposta da API não contém a chave 'edges'.")
        print("Resposta recebida:", jsonData)
        return

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
    
    dataset = []

    # Criar dicionário limpo
    dataset.append({
        "seq": jsonData["seq"],
        "id": jsonData["id"],
        "description": jsonData["description"],
    })
    print(tabulate(dataset, headers="keys", tablefmt="grid"))

def findDataset(userinfo, hostinfo, identifier):
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", "/dataset", "", headers, hostinfo["baseurl"]))
    
    if "edges" not in jsonData:
        return None
    
    for edge in jsonData["edges"]:
        node = edge["node"]
        
        if (str(node["id"]) == identifier or 
            str(node["seq"]) == identifier or 
            node["description"].lower() == identifier.lower()):
            dataset = []
            # Criar dicionário limpo
            dataset.append({
                "seq": node["seq"],
                "id": node["id"],
                "description": node["description"],
            })
            print(tabulate(dataset, headers="keys", tablefmt="grid"))

            return node
        
    return None

# ===== PROCESSORS =====
def getProcessors(userinfo,hostinfo):
    payload = ""    
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", f"/processor?skip=0&take=20&sort=%5B%7B%22field%22:%22id%22,%20%22order%22:%22ASC%22%7D%5D", payload, headers, hostinfo["baseurl"]))    
    
    if "edges" not in jsonData:
        print("Erro: A resposta da API não contém a chave 'edges'.")
        print("Resposta recebida:", jsonData)
        return

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

def findProcessor(userinfo, hostinfo, identifier):
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    # Using a larger take value to ensure we find the processor
    jsonData = json.loads(send_request("GET", f"/processor?skip=0&take=100&sort=%5B%7B%22field%22:%22id%22,%20%22order%22:%22ASC%22%7D%5D", "", headers, hostinfo["baseurl"]))
    
    if "edges" not in jsonData:
        return None

    for edge in jsonData["edges"]:
        node = edge["node"]
        if (str(node["id"]) == identifier or 
            str(node["seq"]) == identifier or 
            node["name"].lower() == identifier.lower()):
            return node
    return None

def percorreListaProcesses(data):
    processes_list = []

    for edge in data.get("edges", []):
        node = edge.get("node", {})
        
        process_data = {
            "id": node.get("id"),
            "metrics": None,
            "results": None,
            "processor": node.get("processor") or {},
            "dataset": node.get("dataset") or {}
        }

        if "metrics_file" in node and node["metrics_file"]:
            process_data["metrics"] = {
                "id": node["metrics_file"].get("id"),
                "public_url": node["metrics_file"].get("public_url")
            }
            
        if "result_file" in node and node["result_file"]:
            process_data["results"] = {
                "id": node["result_file"].get("id"),
                "public_url": node["result_file"].get("public_url")
            }

        processes_list.append(process_data)

    return processes_list


def getProcesses(userinfo,hostinfo):
    payload = ""
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    json_str = send_request("GET", f"/processing", payload, headers, hostinfo["baseurl"])
    data = json.loads(json_str)

    if "edges" not in data:
        print("Erro: A resposta da API não contém a chave 'edges'.")
        print("Resposta recebida:", data)
        return

    processes = percorreListaProcesses(data)

    print(len(processes),"processes encontrados")
    for p in processes:
        proc_name = p['processor'].get('name', 'N/A')
        ds_desc = p['dataset'].get('description', 'N/A')
        print(f"id [{p['id']}] | {proc_name} | {ds_desc}")
    
    resp = input("Deseja baixar as metrics e results de todos os processos que possuem arquivos? (s/n): ")

    if resp.lower() == 's':
        if not os.path.exists("zips"):
            os.makedirs("zips")
            print("Criada pasta zips")
            
        for p in processes:
            if p["metrics"] and p["metrics"].get("public_url"):
                print(f"Baixando Metrics do processo {p['id']}...")
                download_file(p["metrics"]["public_url"], f"zips/metrics_{p['id']}.zip")
            else:
                print(f"Processo {p['id']} não possui link público de métricas.")
                
            if p["results"] and p["results"].get("public_url"):
                print(f"Baixando Results do processo {p['id']}...")
                download_file(p["results"]["public_url"], f"zips/results_{p['id']}.zip")
            else:
                print(f"Processo {p['id']} não possui link público de resultados.")

def getProcesse(userinfo,hostinfo,id):
    payload = ""
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    json_str = send_request("GET", f"/processing/{id}", payload, headers, hostinfo["baseurl"])
    data = json.loads(json_str)
    
    if "code" in data and data["code"] == "@user_auth_middleware/NOT_AUTHENTICATED":
        print("Erro: Não autenticado. Por favor, execute 'python app.py signin' novamente.")
        return

    if data:
        print(f"processo {data.get('id')} encontrado")
        print(f"ID [{data.get('id')}] | {data.get('processor', {}).get('name', 'N/A')} | {data.get('dataset', {}).get('description', 'N/A')}")
        resp = input("Deseja baixar os arquivos disponíveis? (s/n): ")

        if resp.lower() == 's':
            if not os.path.exists("zips"):
                os.makedirs("zips")
                print("Criada pasta zips")
            
            # Check for metrics file
            metrics = data.get("metrics_file")
            if metrics and metrics.get("public_url"):
                print(f"Baixando Metrics...")
                download_file(metrics["public_url"], f"zips/metrics_{data['id']}.zip")
            else:
                print("Este processo ainda não possui arquivo de métricas disponível.")
            
            # Check for results file
            results = data.get("result_file")
            if results and results.get("public_url"):
                print(f"Baixando Results...")
                download_file(results["public_url"], f"zips/results_{data['id']}.zip")
            else:
                print("Este processo ainda não possui arquivo de resultados disponível.")
    else:
        print(f"Processo {id} não encontrado.")
        

def requestDatasetProcessing(userinfo,hostinfo, processorID,datasetID):

    payload = ""    
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", f"/processor/{processorID}", payload, headers, hostinfo["baseurl"]))

    sendingParameters = []

    if "configuration" not in jsonData or "parameters" not in jsonData["configuration"]:
        print("Erro: Este processador não possui parâmetros configuráveis.")
        return

    for parameter in jsonData["configuration"]["parameters"]:
        print(f"{parameter['name']}: {parameter['default_value']} [{parameter['type']}]")
        parameterInput = input("Pressione Enter para pular alteração ou digite novo valor: ")
        print("-"*25)
        if parameterInput != "":
            sendingParameters. append({
                "name": parameter["name"],
                "value": parameterInput
            })
        else:
            sendingParameters. append({
                "name": parameter["name"],
                "value": parameter["default_value"]
            })

    payload = json.dumps({
        "processor_id": processorID,
        "dataset_id": datasetID,
        "parameters": sendingParameters
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {userinfo['idtoken']}"
    }
    print(send_request("POST", "/processing", payload, headers, hostinfo["baseurl"]))


def exportProcessorConfig(userinfo, hostinfo, processorIdentifier):
    proc = findProcessor(userinfo, hostinfo, processorIdentifier)
    if not proc:
        print(f"Processador '{processorIdentifier}' não encontrado.")
        return

    # Get full details to get parameters
    headers = {'Authorization': f"Bearer {userinfo['idtoken']}"}
    jsonData = json.loads(send_request("GET", f"/processor/{proc['id']}", "", headers, hostinfo["baseurl"]))
    
    parameters = []
    if "configuration" in jsonData and "parameters" in jsonData["configuration"]:
        for p in jsonData["configuration"]["parameters"]:
            parameters.append({
                "name": p["name"],
                "value": p["default_value"]
            })
    
    config = {
        "processor_id": proc["id"],
        "processor_name": proc["name"],
        "parameters": parameters
    }
    
    # Generate filename with collision handling
    base_filename = proc["name"].replace(" ", "_")
    filename = f"{base_filename}.json"
    counter = 1
    while os.path.exists(filename):
        filename = f"{base_filename}_{counter}.json"
        counter += 1
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=4)
        
    print(f"Configuração exportada para: {filename}")


def runProcessingFromConfig(userinfo, hostinfo, configFilename, datasetIdentifier):
    if not os.path.exists(configFilename):
        print(f"Arquivo de configuração '{configFilename}' não encontrado.")
        return
        
    with open(configFilename, 'r') as f:
        config = json.load(f)
    
    ds = findDataset(userinfo, hostinfo, datasetIdentifier)
    if not ds:
        print(f"Dataset '{datasetIdentifier}' não encontrado.")
        return
        
    payload = json.dumps({
        "processor_id": config["processor_id"],
        "dataset_id": ds["id"],
        "parameters": config["parameters"]
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {userinfo['idtoken']}"
    }
    
    print(f"Iniciando processamento com {config['processor_name']} e dataset {ds['description']}...")
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

      getFindDataset <datasetID> or <seq> or <description>
          Procura por informações de um dataset específico.

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

      exportconfig <processorID/seq/name>
          Exporta a configuração padrão de um processador para um arquivo JSON.

      runconfig <file.json> <datasetID/seq/name>
          Inicia um processamento usando uma configuração salva e um dataset.

      help
          Exibe esta mensagem de ajuda.

    Exemplo de uso:
      python app.py signin
      python app.py getdataset 12345
      python app.py getprocesse 102510
      python app.py requestprocessing 12345 102510 
      python app.py exportconfig MyProcessor
      python app.py runconfig MyProcessor.json 102510
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
    elif cmd == "finddataset" and len(sys.argv) > 2:
        findDataset(userinfo,hostinfo,sys.argv[2])
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
    elif cmd == "exportconfig" and len(sys.argv) > 2:
        exportProcessorConfig(userinfo, hostinfo, sys.argv[2])
    elif cmd == "runconfig" and len(sys.argv) > 3:
        runProcessingFromConfig(userinfo, hostinfo, sys.argv[2], sys.argv[3])
    elif cmd == "help":
        help()
    else:
        print("Comando inválido ou parâmetros insuficientes.")
        print("Utilize o comando help para informações dos comandos ")


if __name__ == "__main__":
    main()
