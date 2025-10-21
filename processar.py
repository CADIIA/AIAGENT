import os, time, json, requests
from openai import OpenAI

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN    = os.getenv("ZAPI_TOKEN")
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
MASTER_PHONE  = os.getenv("MASTER_PHONE", "00000000000")

if not (ZAPI_INSTANCE and ZAPI_TOKEN and OPENAI_API_KEY):
    print("❌ Ambiente inválido. Verifique ZAPI_INSTANCE, ZAPI_TOKEN, OPENAI_API_KEY.")
    while True: time.sleep(3600)

ZAPI_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
client = OpenAI(api_key=OPENAI_API_KEY)

print("✅ CADIIA inicializado")
print(f"📡 Z-API: {ZAPI_INSTANCE} | 👑 Mestre: {MASTER_PHONE}")

HEADERS = {"Content-Type": "application/json"}
last_id = None

def zget(path, timeout=15):
    for wait in (0, 2, 5, 10):
        if wait: time.sleep(wait)
        try:
            r = requests.get(f"{ZAPI_URL}{path}", timeout=timeout)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", "5")))
                continue
            if r.ok: return r.json()
            print(f"⚠️ ZGET {path} -> {r.status_code} {r.text[:120]}")
        except Exception as e:
            print(f"⚠️ ZGET erro: {e}")
    return None

def zpost(path, payload, timeout=15):
    for wait in (0, 2, 5, 10):
        if wait: time.sleep(wait)
        try:
            r = requests.post(f"{ZAPI_URL}{path}", headers=HEADERS, json=payload, timeout=timeout)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", "5")))
                continue
            if r.ok: return True
            print(f"⚠️ ZPOST {path} -> {r.status_code} {r.text[:120]}")
        except Exception as e:
            print(f"⚠️ ZPOST erro: {e}")
    return False

def enviar(numero, texto):
    phone = numero.replace("@c.us","").replace("@g.us","")
    ok = zpost("/send-text", {"phone": phone, "message": texto})
    print(f"📤 Envio para {phone}: {'OK' if ok else 'FALHOU'}")

def executar_agente(mensagem, numero):
    """
    Função principal do CADIIA.
    Recebe a mensagem, interpreta e responde conforme regras.
    """
    texto = mensagem.strip()
    if not texto:
        return None
    if "zumo" not in texto.lower():
        return None
    if "@g.us" in numero and MASTER_PHONE not in numero:
        print("🚫 Grupo ignorado (não é do mestre).")
        return None

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content":
                    "Você é o CADIIA, o agente oficial. "
                    "Responda em português, de forma objetiva, sem emojis e sem mencionar GPT. "
                    "Interprete e aja conforme a intenção da mensagem com 'zumo'."
                },
                {"role": "user", "content": texto}
            ],
            temperature=0.4,
        )
        saida = resposta.choices[0].message.content.strip()
        print(f"🤖 CADIIA respondeu: {saida}")
        return saida
    except Exception as e:
        print(f"⚠️ Erro IA: {e}")
        return "Erro interno ao processar a solicitação."

def pegar_ultima():
    data = zget("/last-received-messages")
    if not isinstance(data, list) or not data:
        return None
    msg = data[-1]
    return {
        "id": str(msg.get("id") or msg.get("messageId") or ""),
        "from": str(msg.get("chatId") or msg.get("remoteJid") or ""),
        "body": str(msg.get("body") or msg.get("text") or "").strip(),
        "fromMe": bool(msg.get("fromMe", False))
    }

print("🟢 Loop 24/7 iniciado…")
idle = 0

while True:
    try:
        msg = pegar_ultima()
        if not msg:
            idle += 1
            if idle % 60 == 0: print("⏳ aguardando…")
            time.sleep(3)
            continue
        idle = 0

        if last_id == msg["id"] or not msg["id"]:
            time.sleep(2)
            continue
        last_id = msg["id"]

        numero = msg["from"]
        texto  = msg["body"]
        if not texto:
            continue

        resposta = executar_agente(texto, numero)
        if resposta:
            enviar(numero, resposta)

        time.sleep(2)

    except Exception as e:
        print(f"❌ Loop erro: {e}")
        time.sleep(5)

