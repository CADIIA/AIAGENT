import os
import time
import json
import requests

# ======================================
# CONFIGURAÇÕES AUTOMÁTICAS
# ======================================
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
USUARIO_MESTRE = os.getenv("MASTER_PHONE", "00000000000")  # Valor padrão se não existir

URL_BASE = None
if ZAPI_INSTANCE and ZAPI_TOKEN:
    URL_BASE = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
else:
    print("⚠️ AVISO: ZAPI_INSTANCE ou ZAPI_TOKEN ausentes.")
    print(f"ZAPI_INSTANCE={ZAPI_INSTANCE}")
    print(f"ZAPI_TOKEN={ZAPI_TOKEN}")
    time.sleep(10)
    exit(1)

if not USUARIO_MESTRE or USUARIO_MESTRE == "00000000000":
    print("⚠️ AVISO: MASTER_PHONE não definido. Operando em modo livre.")
else:
    print(f"📱 Mestre autorizado: {USUARIO_MESTRE}")

# ======================================
# FUNÇÕES
# ======================================
def verificar_mensagens():
    """Busca novas mensagens recebidas"""
    try:
        r = requests.get(f"{URL_BASE}/last-received-messages", timeout=15)
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
    """Envia resposta de texto"""
    try:
        payload = {
            "phone": numero.replace("@c.us", "").replace("@g.us", ""),
            "message": texto
        }
        r = requests.post(f"{URL_BASE}/send-text", json=payload, timeout=10)
        print(f"📤 [{r.status_code}] Resposta enviada: {texto}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")


def limpar():
    """Apenas log para manter ciclo ativo"""
    print("♻️ Nenhuma nova mensagem... aguardando...")


# ======================================
# LOOP PRINCIPAL (NUNCA PARA)
# ======================================
print("🟢 CADIIA ativo — ciclo contínuo iniciado...")

while True:
    entrada = verificar_mensagens()

    if not entrada:
        time.sleep(5)
        continue

    numero = entrada["numero"]
    msg = entrada["mensagem"].lower().strip()

    # --- 1️⃣ Só reage se contiver 'zumo'
    if "zumo" not in msg:
        limpar()
        time.sleep(3)
        continue

    # --- 2️⃣ Ignora grupos, exceto se for o dono
    if "@g.us" in numero and USUARIO_MESTRE not in numero:
        print("⏸ Ignorado — grupo comum")
        limpar()
        time.sleep(3)
        continue

    # --- 3️⃣ Atende o mestre em qualquer contexto
    print(f"📩 Mensagem reconhecida de {numero}: {msg}")
    enviar_resposta(numero, f"🤖 Zumo recebido: {msg}")
    limpar()
    time.sleep(3)
