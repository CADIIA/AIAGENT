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
last_id = None  # evita respostas repetidas

def zget(path, timeout=15):
    for wait in (0, 2, 5, 10):
        if wait: time.sleep(wait)
        try:
            r = requests.get(f"{ZAPI_URL}{path}", timeout=timeout)
            if r.status_code == 429:
                # rate limit – aguarda e tenta de novo
                retry = int(r.headers.get("Retry-After", "5"))
                time.sleep(retry)
                continue
            if r.ok: return r.json()
            print(f"⚠️ ZGET {path} -> {r.status_code} {r.text[:180]}")
        except Exception as e:
            print(f"⚠️ ZGET {path} erro: {e}")
    return None

def zpost(path, payload, timeout=15):
    for wait in (0, 2, 5, 10):
        if wait: time.sleep(wait)
        try:
            r = requests.post(f"{ZAPI_URL}{path}", headers=HEADERS, json=payload, timeout=timeout)
            if r.status_code == 429:
                retry = int(r.headers.get("Retry-After", "5"))
                time.sleep(retry)
                continue
            if r.ok: return True
            print(f"⚠️ ZPOST {path} -> {r.status_code} {r.text[:180]}")
        except Exception as e:
            print(f"⚠️ ZPOST {path} erro: {e}")
    return False

def enviar(numero, texto):
    phone = numero.replace("@c.us","").replace("@g.us","")
    ok = zpost("/send-text", {"phone": phone, "message": texto})
    print(f"📤 Envio para {phone}: {'OK' if ok else 'FALHOU'}")

def pedir_ia(prompt):
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
              {"role":"system","content":"Você é o CADIIA. Responda em PT-BR, objetivo e direto."},
              {"role":"user","content":prompt}
            ],
            temperature=0.4,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ IA erro: {e}")
        return "Tive um erro ao processar. Tente novamente."

def pegar_ultima():
    data = zget("/last-received-messages")
    if not isinstance(data, list) or not data:
        return None
    msg = data[-1]
    return {
        "id":   str(msg.get("id") or msg.get("messageId") or ""),
        "from": str(msg.get("chatId") or msg.get("remoteJid") or ""),
        "body": str(msg.get("body") or msg.get("text") or "").strip(),
        "fromMe": bool(msg.get("fromMe", False))
    }

print("🟢 Loop 24/7 iniciado…")
idle = 0
while True:
    try:
        m = pegar_ultima()
        if not m:
            idle += 1
            if idle % 60 == 0: print("⏳ aguardando…")
            time.sleep(3)
            continue
        idle = 0

        # dedup
        if last_id == m["id"] or not m["id"]:
            time.sleep(2); continue
        last_id = m["id"]

        numero = m["from"]
        texto  = m["body"]
        if not texto:
            continue

        # regra 1: só reage se contiver "zumo"
        if "zumo" not in texto.lower():
            continue

        # regra 2: NUNCA responder em grupos (exceto mestre)
        if "@g.us" in numero and MASTER_PHONE not in numero:
            print("🚫 Grupo ignorado (não é do mestre).")
            continue

        # regra 3: atender o mestre em qualquer contexto (já coberto acima)
        print(f"📩 {numero} :: {texto}")

        resposta = pedir_ia(texto)
        enviar(numero, resposta)

        time.sleep(2)

    except Exception as e:
        print(f"❌ Loop erro: {e}")
        time.sleep(5)
