import os
import time
import requests
from openai import OpenAI

# ============================================================
# REGRAS (aplicadas no código):
# 1) Só responde se a mensagem contiver "zumo"
# 2) Não responde em grupos (exceto se a mensagem no grupo for do MASTER_PHONE)
# 3) Responde qualquer solicitação do MASTER_PHONE (privado ou grupo) se tiver "zumo"
# 4) Executa 24/7 em loop contínuo (GitHub Actions + cron religam)
# 5) Nunca para (mesmo sem mensagens)
# ============================================================

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN    = os.getenv("ZAPI_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MASTER_PHONE   = (os.getenv("MASTER_PHONE") or "").replace("+", "").strip()

if not ZAPI_INSTANCE or not ZAPI_TOKEN:
    print("❌ ERRO: ZAPI_INSTANCE/ZAPI_TOKEN ausentes.")
    raise SystemExit(1)
if not OPENAI_API_KEY:
    print("❌ ERRO: OPENAI_API_KEY ausente.")
    raise SystemExit(1)

ZAPI_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
client = OpenAI(api_key=OPENAI_API_KEY)

print("✅ CADIIA conectado à Z-API.")
print(f"📡 Instância: {ZAPI_INSTANCE}")
print(f"📱 Mestre: {MASTER_PHONE or 'NÃO DEFINIDO'}")
print("♾️ Loop 24/7 ativo.\n")


def _normalize_phone(chat_id: str) -> str:
    """Converte chatId em número para envio. Não força DDI se já existir."""
    phone = (chat_id or "").replace("@c.us", "").replace("@g.us", "")
    phone = phone.replace("+", "").strip()
    return phone

def _is_group(chat_id: str) -> bool:
    return (chat_id or "").endswith("@g.us")

def _author_number(author: str) -> str:
    return (author or "").replace("@c.us", "").replace("@g.us", "").replace("+", "").strip()

def _is_from_master(author: str) -> bool:
    if not MASTER_PHONE:
        return False
    return _author_number(author).startswith(MASTER_PHONE)

def obter_mensagens():
    """
    Retorna lista de mensagens (ordem natural do endpoint).
    Cada item: {id, chatId, body, author, fromMe}
    """
    try:
        r = requests.get(f"{ZAPI_URL}/last-received-messages", timeout=15)
        if r.status_code != 200:
            print(f"⚠️ Z-API status {r.status_code} em last-received-messages")
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        msgs = []
        for m in data:
            msgs.append({
                "id": m.get("id") or m.get("messageId") or "",
                "chatId": m.get("chatId", ""),
                "body": (m.get("body") or "").strip(),
                "author": m.get("author", ""),
                "fromMe": bool(m.get("fromMe", False)),
            })
        return msgs
    except Exception as e:
        print(f"⚠️ Erro ao buscar mensagens: {e}")
        return []

def enviar_texto(chat_id: str, texto: str):
    """Envia texto via /send-text com normalização do número."""
    try:
        phone = _normalize_phone(chat_id)
        payload = {"phone": phone, "message": texto}
        resp = requests.post(f"{ZAPI_URL}/send-text", json=payload, timeout=15)
        print(f"📤 Envio [{resp.status_code}] -> {phone}: {texto[:120]}")
    except Exception as e:
        print(f"❌ Falha ao enviar: {e}")

def responder_com_ia(prompt: str) -> str:
    """Resposta IA objetiva em PT-BR."""
    try:
        out = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content":
                 "Você é o CADIIA, assistente direto, objetivo e obediente. "
                 "Responda sempre em português. Não enrole."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        return out.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Erro na IA: {e}")
        return "⚠️ Erro ao processar sua solicitação."

# --------- LOOP INFINITO ---------
# Dedup por ID de mensagem dentro da execução
vistos = set()
print("🤖 Escutando por mensagens com 'zumo'...\n")

while True:
    msgs = obter_mensagens()

    # Processa na ordem recebida; se quiser garantir crescente, remova comentário:
    # msgs.sort(key=lambda x: x.get("id",""))

    for m in msgs:
        mid   = m["id"]
        chat  = m["chatId"]
        body  = m["body"]
        author= m["author"]
        from_me = m["fromMe"]

        # Dedup local
        if not mid or mid in vistos:
            continue
        vistos.add(mid)

        # Regra 5: nunca para (mesmo sem mensagens) — só continua o loop

        # ignora nosso próprio envio (evita eco)
        if from_me:
            continue

        # Regra 1: só reage se contiver "zumo"
        if "zumo" not in body.lower():
            continue

        # Regra 2/3:
        # - Em grupo: responde apenas se a mensagem foi enviada pelo MASTER_PHONE
        # - Em privado: responde para qualquer pessoa (desde que tenha "zumo")
        if _is_group(chat) and not _is_from_master(author):
            print("⏸ Grupo ignorado (mensagem não é do mestre).")
            continue

        print(f"📩 {chat} :: {body}")
        resposta = responder_com_ia(body)
        enviar_texto(chat, resposta)

    time.sleep(4)  # mantém o ciclo vivo, 24/7
