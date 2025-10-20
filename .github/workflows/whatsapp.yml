import json, os, requests
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Lê o arquivo de entrada
with open("entrada.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

numero = dados["numero"]
mensagem = dados["mensagem"].strip()

# 🔒 1️⃣ Ignora mensagens vindas de grupos
if "-" in numero:
    print(f"🚫 Mensagem ignorada (vinda de grupo): {numero}")
    exit(0)

# 🔒 2️⃣ Ignora mensagens sem o comando "Zumo"
if not mensagem.lower().startswith("zumo"):
    print(f"⏸️ Mensagem ignorada (sem comando 'Zumo'): {mensagem}")
    exit(0)

print(f"📩 Mensagem válida recebida de {numero}: {mensagem}")

# Remove o comando "Zumo" antes de enviar pro GPT
mensagem_limpa = mensagem[len("zumo"):].strip()

# 🤖 Chama o GPT
resposta = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Você é um atendente virtual simpático, profissional e direto."},
        {"role": "user", "content": mensagem_limpa}
    ]
).choices[0].message.content

print(f"🤖 Resposta gerada: {resposta}")

# 💾 Salva a resposta
with open("saida.json", "w", encoding="utf-8") as f:
    json.dump({"numero": numero, "resposta": resposta}, f, indent=2, ensure_ascii=False)

# 📤 Envia pro WhatsApp via Z-API
instance = os.getenv("ZAPI_INSTANCE")
token = os.getenv("ZAPI_TOKEN")

url = f"https://api.z-api.io/instances/{instance}/token/{token}/send-messages"

payload = [{"phone": numero, "message": resposta}]
headers = {"Content-Type": "application/json"}

r = requests.post(url, json=payload, headers=headers)

if r.status_code == 200:
    print("✅ Mensagem enviada com sucesso!")
else:
    print(f"❌ Erro ao enviar mensagem: {r.text}")



# =========================================================
# 🔁 BLOCO ADICIONADO — operação contínua 24/7
# =========================================================

import time, threading

# Mantém logs ativos a cada 5 minutos
def manter_logs():
    while True:
        print("🟢 Agente ativo —", time.strftime("%H:%M:%S"))
        time.sleep(300)

threading.Thread(target=manter_logs, daemon=True).start()

# Reinicia o workflow automaticamente antes de encerrar
def manter_ativo():
    repo = os.getenv("GITHUB_REPOSITORY", "NatureIA/AIAGENT")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️ Sem token do GitHub, não é possível reiniciar.")
        return
    url = f"https://api.github.com/repos/{repo}/actions/workflows/whatsapp.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"ref": "main"}
    try:
        print("⏳ Preparando novo ciclo de execução...")
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 204:
            print("✅ Novo ciclo iniciado com sucesso (agente contínuo).")
        else:
            print(f"⚠️ Falha ao reiniciar: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Erro ao reiniciar ciclo: {e}")

# Chama reinício automático
manter_ativo()

print("🏁 Execução finalizada — ciclo contínuo garantido.")

