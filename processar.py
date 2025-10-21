import os
import time
import requests
from openai import OpenAI

# ============================================================
# ⚙️ CONFIGURAÇÃO DE AMBIENTE
# ============================================================
# Regras fixas do CADIIA:
# 1️⃣ Nunca responder se a mensagem não contiver "zumo"
# 2️⃣ Nunca responder em grupos comuns
# 3️⃣ Atender qualquer solicitação do mestre (MASTER_PHONE)
#     mesmo dentro de grupos, desde que contenha "zumo"
# 4️⃣ Rodar 24/7 sem interrupções
# 5️⃣ Nunca parar — com ou sem mensagens
# ============================================================

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MASTER_PHONE = os.getenv("MASTER_PHONE", "00000000000")

if not ZAPI_INSTANCE or not ZAPI_TOKEN:
    print("❌ ERRO: Variáveis ZAPI_INSTANCE e ZAPI_TOKEN ausentes!")
    exit(1)

if not OPENAI_API_KEY:
    print("❌ ERRO: OPENAI_API_KEY ausente!")
    exit(1)

ZAPI_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
client = OpenAI(api_key=OPENAI_API_KEY)

print("✅ CADIIA inicializado e conectado à Z-API.")
print(f"📡 Instância: {ZAPI_INSTANCE}")
print(f"📱 Mestre autorizado: {MASTER_PHONE}")
print("♾️ Modo contínuo 24/7 ativo.\n")


# ============================================================
# 🧩 FUNÇÕES AUXILIARES
# ============================================================

def enviar_resposta(numero, texto):
    """Envia mensagem de resposta via Z-API"""
    try:
        payload = {
            "phone": numero.replace("@c.us", "").replace("@g.us", ""),
            "message": texto
        }
        r = requests.post(f"{ZAPI_URL}/send-text", json=payload, timeout=15)
        print(f"📤 [{r.status_code}] Enviado para {numero}: {texto[:80]}...")
    except Exception as e:
        print(f"❌ Erro ao enviar resposta: {e}")


def obter_mensagens():
    """Obtém a última mensagem recebida via Z-API"""
    try:
        r = requests.get(f"{ZAPI_URL}/last-received-messages", timeout=15)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                ultima = data[-1]
                numero = ultima.get("chatId", "")
                msg = ultima.get("body", "").strip()
                return numero, msg
    except Exception as e:
        print(f"⚠️ Erro ao buscar mensagens: {e}")
    return None, None


def gerar_resposta_ia(pergunta):
    """Gera resposta com GPT (assistente CADIIA)"""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "Você é o CADIIA — um assistente inteligente, "
                    "obediente, objetivo e direto. Responda sempre em português, "
                    "sem enrolação, e atenda a qualquer solicitação do mestre "
                    "que contenha a palavra 'zumo'."
                )},
                {"role": "user", "content": pergunta}
            ]
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Erro na IA: {e}")
        return "⚠️ Ocorreu um erro ao processar sua solicitação."


# ============================================================
# 🔁 LOOP PRINCIPAL — NUNCA PARA
# ============================================================
ultima_mensagem = ""
print("🤖 CADIIA está online e monitorando mensagens com 'zumo'...\n")

while True:
    numero, msg = obter_mensagens()

    # Mantém o loop vivo, mesmo sem mensagens
    if not msg or msg == ultima_mensagem:
        time.sleep(4)
        continue

    ultima_mensagem = msg
    print(f"📩 Nova mensagem de {numero}: {msg}")

    # Regra 1️⃣ — Ignora mensagens sem "zumo"
    if "zumo" not in msg.lower():
        print("⏸ Ignorado — mensagem sem 'zumo'.\n")
        time.sleep(3)
        continue

    # Regra 2️⃣ — Ignora grupos comuns (sem mestre)
    if "@g.us" in numero and MASTER_PHONE not in numero:
        print("⏸ Ignorado — mensagem de grupo comum.\n")
        time.sleep(3)
        continue

    # Regra 3️⃣ — Sempre atender o mestre
    print(f"✅ Comando 'zumo' detectado de {numero}. Processando...")
    resposta = gerar_resposta_ia(msg)
    enviar_resposta(numero, resposta)
    print("🟢 Ação concluída. Voltando à escuta...\n")

    # Regra 4️⃣ e 5️⃣ — mantém o ciclo ativo
    time.sleep(5)
