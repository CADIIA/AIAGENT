# =========================================================
# 🤖 CADIIA — Agente Inteligente 24/7
# =========================================================
# Regras Fundamentais:
# 1️⃣ Nunca responder se a mensagem NÃO contiver a palavra “zumo”.
# 2️⃣ Nunca responder em grupos (ignora mensagens com "group" ou tipo != chat individual).
# 3️⃣ Atender qualquer solicitação do usuário se vier após “zumo”.
# 4️⃣ Operação contínua 24/7 — reinicia automaticamente via workflow GitHub.
# 5️⃣ Seguir instruções sem alterar ou questionar.
# 6️⃣ Sempre responder de forma útil, direta e profissional, sem florear.
# =========================================================

import os, json, time, threading, requests
from openai import OpenAI

# Variáveis de ambiente
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
INSTANCE = os.getenv("ZAPI_INSTANCE")
TOKEN = os.getenv("ZAPI_TOKEN")

# =========================================================
# 🔁 Bloco de monitoramento — operação contínua 24/7
# =========================================================

def manter_logs():
    """Mantém logs vivos para evitar timeout"""
    while True:
        print("🟢 CADIIA ativo —", time.strftime("%H:%M:%S"))
        time.sleep(300)  # log a cada 5 minutos

threading.Thread(target=manter_logs, daemon=True).start()

# =========================================================
# 📥 Leitura da entrada
# =========================================================
try:
    with open("entrada.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
except Exception as e:
    print("❌ Erro ao ler entrada.json:", e)
    exit()

numero = dados.get("numero", "")
mensagem = dados.get("mensagem", "").strip()
print(f"📨 Mensagem recebida de {numero}: {mensagem}")

# =========================================================
# 🚫 Regras de bloqueio
# =========================================================
if not mensagem or "zumo" not in mensagem.lower():
    print("⏸ Ignorado — sem palavra-chave 'zumo'")
    exit()

if "group" in numero.lower():
    print("🚫 Ignorado — mensagem de grupo detectada.")
    exit()

# =========================================================
# 💬 Núcleo de Resposta IA
# =========================================================
prompt = f"""
O usuário enviou a mensagem: "{mensagem}".
Você é o agente CADIIA.
Responda sempre de forma direta, precisa e útil.
Nunca questione o comando do usuário.
Nunca use linguagem floreada.
Fale de forma profissional e concisa.
"""

try:
    client = OpenAI(api_key=OPENAI_KEY)
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    ).choices[0].message.content.strip()
except Exception as e:
    resposta = f"⚠️ Erro de IA: {e}"

print(f"💬 Resposta gerada: {resposta}")

# =========================================================
# 📤 Enviar resposta via Z-API
# =========================================================
try:
    url = f"https://api.z-api.io/instances/{INSTANCE}/token/{TOKEN}/send-text"
    r = requests.post(url, json={"phone": numero, "message": resposta})
    if r.status_code == 200:
        print("✅ Resposta enviada com sucesso.")
    else:
        print(f"⚠️ Erro ao enviar resposta: {r.status_code} - {r.text}")
except Exception as e:
    print(f"❌ Falha no envio: {e}")

# =========================================================
# 🔁 Reinício automático do ciclo
# =========================================================
def reiniciar_workflow():
    repo = os.getenv("GITHUB_REPOSITORY", "CADIIA/AIAGENT")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️ Sem token do GitHub, reinício automático desativado.")
        return
    url = f"https://api.github.com/repos/{repo}/actions/workflows/whatsapp.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"ref": "main"}
    try:
        print("♻️ Iniciando novo ciclo automático...")
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 204:
            print("✅ Novo ciclo acionado com sucesso.")
        else:
            print(f"⚠️ Falha no reinício: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Erro ao reiniciar ciclo: {e}")

reiniciar_workflow()
print("🏁 Execução concluída — operação contínua garantida.")
