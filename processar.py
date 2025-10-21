# processar.py
# Regras implementadas:
# - responde somente se a mensagem contiver "zumo"
# - não responde em grupos (exceto se o MASTER_PHONE estiver presente no chatId)
# - atende qualquer solicitação do MASTER em qualquer chat (privado ou grupo)
# - roda em loop 24/7, autocorretivo, tolerante a falhas de rede/API

import os
import time
import json
import traceback
from typing import List, Dict, Any
import requests

# ---- Config ----
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MASTER_PHONE = os.getenv("MASTER_PHONE", "")  # ex: 5581999999999

CHECK_INTERVAL = 5  # segundos entre polls
SEEN_FILE = "cadiia_seen.json"
MAX_RETRIES = 3
BACKOFF_BASE = 1.5

# ---- Validações iniciais ----
missing = [k for k,v in (("ZAPI_INSTANCE",ZAPI_INSTANCE),("ZAPI_TOKEN",ZAPI_TOKEN),("OPENAI_API_KEY",OPENAI_API_KEY)) if not v]
if missing:
    print("❌ ENV faltando:", missing)
    raise SystemExit(1)

ZAPI_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
OPENAI_API = OPENAI_API_KEY  # apenas nome sem lib para evitar import issues

print("✅ CADIIA carregado")
print("📡 Z-API:", ZAPI_INSTANCE)
print("👑 MASTER_PHONE:", MASTER_PHONE or "(não definido)")

# ---- Persistência de vistos ----
def load_seen() -> set:
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen(s: set):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(s), f)
    except Exception as e:
        print("⚠️ Falha ao salvar vistos:", e)

seen = load_seen()

# ---- Helpers Z-API ----
def zapi_get(path: str, timeout=15) -> Any:
    url = f"{ZAPI_URL}{path}"
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = requests.get(url, timeout=timeout)
            return r
        except Exception as e:
            wait = BACKOFF_BASE ** attempt
            print(f"⚠️ GET erro (attempt {attempt}): {e} -> backoff {wait}s")
            time.sleep(wait)
    return None

def zapi_post(path: str, payload: Dict, timeout=15) -> Any:
    url = f"{ZAPI_URL}{path}"
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            return r
        except Exception as e:
            wait = BACKOFF_BASE ** attempt
            print(f"⚠️ POST erro (attempt {attempt}): {e} -> backoff {wait}s")
            time.sleep(wait)
    return None

# ---- Send / Fetch ----
def fetch_messages() -> List[Dict]:
    r = zapi_get("/last-received-messages")
    if not r:
        return []
    try:
        if r.status_code != 200:
            print("⚠️ Z-API fetch status:", r.status_code, r.text[:200])
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        return data
    except Exception as e:
        print("⚠️ parse fetch:", e)
        return []

def send_text(chat_id: str, text: str):
    phone = chat_id.replace("@c.us","").replace("@g.us","")
    payload = {"phone": phone, "message": text}
    r = zapi_post("/send-text", payload)
    if r is None:
        print("❌ send_text failed (no response)")
        return False
    if r.status_code not in (200,201):
        print("❌ send_text status:", r.status_code, r.text[:200])
        return False
    return True

# ---- OpenAI call (minimal, robust) ----
def call_openai(prompt: str) -> str:
    # Usar REST simples para evitar dependências extras; usa chave OPENAI_API
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"Você é o assistente CADIIA. Responda em português, direto e objetivo."},
            {"role":"user","content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=20)
            if r.status_code == 200:
                j = r.json()
                return j["choices"][0]["message"]["content"].strip()
            else:
                print(f"⚠️ OpenAI status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print("⚠️ OpenAI erro:", e)
        time.sleep(BACKOFF_BASE ** attempt)
    return "Desculpe, erro ao processar sua solicitação."

# ---- Regras aplicadas à mensagem ----
def should_respond(msg: Dict) -> bool:
    # identifica campos variáveis
    body = (msg.get("body") or msg.get("text") or msg.get("message") or "").strip()
    if not body:
        return False
    if "zumo" not in body.lower():
        return False
    chat_id = msg.get("chatId","")
    is_group = "@g.us" in chat_id
    from_me = bool(msg.get("fromMe") or msg.get("self") or False)
    if from_me:
        return False
    # se grupo e MASTER_PHONE não está no chatId -> ignora
    if is_group:
        if MASTER_PHONE and MASTER_PHONE in chat_id:
            return True
        return False
    # privado com 'zumo' -> responde
    return True

# ---- Main loop ----
print("🟢 Loop iniciado")
try:
    while True:
        try:
            msgs = fetch_messages()
            # ordenar para determinismo (timestamp ou fallback)
            def keyfn(m):
                return int(m.get("timestamp") or m.get("id") or 0)
            msgs.sort(key=keyfn)
            for m in msgs:
                # id único heurístico
                mid = str(m.get("id") or m.get("messageId") or m.get("timestamp") or json.dumps(m))
                if mid in seen:
                    continue
                seen.add(mid)
                # persistir periodicamente
                if len(seen) % 50 == 0:
                    save_seen(seen)

                chat_id = m.get("chatId","")
                body = (m.get("body") or m.get("text") or "").strip()
                print("📩", chat_id, "->", body[:200])

                if not should_respond(m):
                    continue

                # gerar resposta IA (resiliência ao erro)
                try:
                    resp = call_openai(body)
                except Exception as e:
                    print("⚠️ Erro IA:", e)
                    resp = "Erro interno ao gerar resposta."

                ok = send_text(chat_id, resp)
                if not ok:
                    print("⚠️ envio falhou para", chat_id)
            # salvar vistos a cada ciclo
            save_seen(seen)
        except Exception:
            print("‼️ erro ciclo:", traceback.format_exc())
        print("⏰ tick")
        time.sleep(CHECK_INTERVAL)
except KeyboardInterrupt:
    print("⛔ encerrado manualmente")
except Exception:
    print("⛔ encerrado por exceção", traceback.format_exc())
finally:
    save_seen(seen)
