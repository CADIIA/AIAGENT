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
