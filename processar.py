import os
import time
import requests
from openai import OpenAI

# ======================================
# CONFIGURAÇÃO DE AMBIENTE
# ======================================
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

print("✅ CADIIA inicializado com sucesso!")
print(f"📡 Instância Z-API: {ZAPI_INSTANCE}")
print(f"📱 Mestre autorizado: {MASTER_PHONE}")

# ======================================
# FUNÇÕES AUXILIARES
# ======================================

def enviar_resposta(numero, texto):
    try:
        payload = {
            "phone": numero.replace("@c.us", "").replace("@g.us", ""),
            "message": texto
        }
        r = requests.post(f"{ZAPI_URL}/send-text", json=payload, timeout=15)
        print(f"📤 Enviado para {numero}: {texto[:60]}...")
    except Exception as e:
        print(f"❌ Erro ao enviar resposta: {e}")

def obter_mensagens():
    try:
        r = requests.get(f"{ZAPI_URL}/last-received-messages", timeout=15)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                ultima = data[-1]
                numero = ultima.get("chatId", "")
                msg = ultima.get("body", "").strip()
                return numero, msg
    except Exception as e:
        print(f"⚠️ Erro ao buscar mensagens: {e}")
    return None, None

def gerar_resposta_ia(pergunta):
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é o assistente CADIIA, direto e útil. Responda em português de forma objetiva."},
                {"role": "user", "content": pergunta}
            ]
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Erro na IA: {e}")
        return "Ocorreu um erro ao processar sua solicitação."

# ======================================
# REGRAS CADIIA
# ======================================
# 1. Nunca responder se não houver 'zumo' na mensagem.
# 2. Nunca responder mensagens de grupos.
# 3. Atender qualquer solicitação do mestre se tiver 'zumo' em qualquer conversa.
# 4. Rodar 24/7 continuamente.
# 5. Nunca parar — mesmo sem mensagens.

print("🤖 CADIIA ativo — aguardando mensagens...")

ultima_mensagem = ""

# ======================================
# LOOP PRINCIPAL 24/7
# ======================================
while True:
    numero, msg = obter_mensagens()

    if not msg or msg == ultima_mensagem:
        time.sleep(4)
        continue

    ultima_mensagem = msg
    print(f"📩 Nova mensagem de {numero}: {msg}")

    # Regras
    if "zumo" not in msg.lower():
        time.sleep(2)
        continue

    # Ignora grupos (só responde em privado)
    if "@g.us" in numero:
        print("⏸ Mensagem em grupo ignorada.")
        time.sleep(2)
        continue

    # Somente responde comandos do mestre
    if MASTER_PHONE not in numero:
        print("⏸ Mensagem ignorada (não é do mestre).")
        time.sleep(2)
        continue

    resposta = gerar_resposta_ia(msg)
    enviar_resposta(numero, resposta)
    time.sleep(5)
