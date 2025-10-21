import os
import time
import requests
from openai import OpenAI

# ==============================
# CONFIGURAÇÕES INICIAIS
# ==============================
print("🔍 DEBUG — Variáveis de ambiente recebidas:")
for k in ["ZAPI_INSTANCE", "ZAPI_TOKEN", "MASTER_PHONE", "OPENAI_API_KEY", "GH_TOKEN"]:
    print(f"   {k}: {os.getenv(k)}")

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
MASTER_PHONE = os.getenv("MASTER_PHONE", "00000000000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

if not ZAPI_INSTANCE or not ZAPI_TOKEN:
    print("❌ ERRO: Variáveis da Z-API ausentes.")
    exit(1)

URL_BASE = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
print("✅ Ambiente pronto, iniciando CADIIA IA...")

# ==============================
# FUNÇÕES
# ==============================
def verificar_mensagens():
    """Busca novas mensagens (usando endpoint atualizado da Z-API)."""
    try:
        r = requests.get(f"{URL_BASE}/chats/messages", timeout=15)
        print("📡 Resposta da ZAPI:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                ultima = data[-1]
                numero = ultima.get("chatId", "")
                msg = ultima.get("body", "").strip()
                return {"numero": numero, "mensagem": msg}
    except Exception as e:
        print(f"⚠️ Erro ao verificar mensagens: {e}")
    return None


def enviar_resposta(numero, texto):
    """Envia resposta de texto via Z-API."""
    try:
        payload = {
            "phone": numero.replace("@c.us", "").replace("@g.us", ""),
            "message": texto
        }
        r = requests.post(f"{URL_BASE}/send-text", json=payload, timeout=10)
        print(f"📤 [{r.status_code}] Resposta enviada: {texto}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")


def gerar_resposta_ia(mensagem):
    """Usa GPT (OpenAI) para interpretar e responder à mensagem."""
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é o agente CADIIA, um assistente inteligente conectado ao WhatsApp. Responda de forma útil, natural e precisa."},
                {"role": "user", "content": mensagem}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Erro ao gerar resposta IA: {e}")
        return "⚠️ Falha ao gerar resposta inteligente."


# ==============================
# LOOP PRINCIPAL
# ==============================
print("🟢 CADIIA ativo — ciclo contínuo iniciado...")

while True:
    entrada = verificar_mensagens()

    if not entrada:
        time.sleep(5)
        continue

    numero = entrada["numero"]
    msg = entrada["mensagem"].strip()

    # Ignora mensagens sem "zumo"
    if "zumo" not in msg.lower():
        time.sleep(2)
        continue

    # Bloqueia grupos que não sejam do mestre (se configurado)
    if "@g.us" in numero and (MASTER_PHONE not in numero):
        print("⏸ Ignorado — grupo não autorizado.")
        time.sleep(3)
        continue

    print(f"📩 Mensagem detectada: {msg}")
    resposta = gerar_resposta_ia(msg)
    enviar_resposta(numero, resposta)
    time.sleep(3)
