# CLI – Ferramenta de Interação com API de Processamento de Datasets

Esta aplicação CLI em Python permite autenticar, consultar datasets, processadores, processos e solicitar novos processamentos em um servidor remoto. Também oferece a opção de baixar automaticamente arquivos de *metrics* e *results* associados a cada processamento.

---

## 📦 Funcionalidades

- 🔐 Autenticação (signin) via Firebase Authentication  
- 📚 Listagem de datasets  
- 🗂️ Consulta de dataset específico  
- ⚙️ Listagem de processadores  
- 🔎 Consulta de processador específico  
- 🧠 Solicitar processamento entre dataset e processador  
- 📊 Listagem de processos realizados com opção de download  
- 🔍 Consulta de processo específico  
- ❓ Ajuda integrada via comando `help`  

---

## 🚀 Instalação

### Clone o repositório:

```bash
git clone https://github.com/Eduardo-Leal-Carvalho/malDataGen-CLI.git
cd malDataGen-CLI
```

## ⚙️ Configuração

Antes de usar a CLI, você precisa criar um arquivo config.ini na raiz do projeto:

```bash
[USERINFO]
email = seuemail@example.com
password = suasenha
idtoken = 

[HOSTINFO]
firebaseapikey = SUA_FIREBASE_API_KEY
googleapiurl = identitytoolkit.googleapis.com
baseurl = api.seuservidor.com
```
O campo idtoken será automaticamente preenchido após o comando signin.

## 🧩 Uso da CLI
A forma geral do comando é:

```bash
python app.py <comando> [parâmetros]
```

## 📝 Comandos Disponíveis
### 🔐 signin
Faz login no servidor utilizando o e-mail e senha do arquivo config.ini.
Após login bem-sucedido, o idtoken é atualizado no próprio arquivo.

```bash
python app.py signin
```

### 📚 getdatasets
Lista todos os datasets disponíveis no servidor.

```bash
python app.py getdatasets
```

### 🗂️ getdataset <datasetID>
Retorna informações detalhadas sobre um dataset específico.

```bash
python app.py getdataset 12345
```

### ⚙️ getprocessors
Lista todos os processadores registrados.

```bash
python app.py getprocessors
```

### 🔎 getprocessor <processorID>
Mostra detalhes de um processador específico.

```bash
python app.py getprocessor 10
```

### 🧠 requestprocessing <processorID> <datasetID>
Solicita um novo processamento de dataset utilizando um processador específico.

```bash
python app.py requestprocessing 5 102510
```

### 📊 getprocesses

Lista todos os processos realizados.

Também oferece a opção:

* Baixar metrics
* Baixar results

Automática ou individualmente.

```bash
python app.py getprocesses
```

### 🔍 getprocesse <processID>
Consulta um processo específico e permite baixar seus arquivos.

```bash
python app.py getprocesse 9001
```

### ❓ help
Exibe todas as instruções sobre os comandos.

```bash
python app.py help
```
