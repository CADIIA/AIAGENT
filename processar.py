# processar.py — núcleo CADIIA (responde mensagens via Z-API)
import os
import time
import json
import requests

INSTANCE = os.getenv("ZAPI_INSTANCE")
TOKEN = os.getenv("ZAPI_TOKEN")

print("🟢 CADIIA ativo — modo 24/7")

def enviar_resposta(numero, texto):
    url = f"https://api.z-api.io/instances/{INSTANCE}/token/{TOKEN}/send-text"
    payload = {"phone": numero, "message": texto}
    try:
        requests.post(url, json=payload)
        print(f"📤 Resposta enviada para {numero}: {texto}")
    except Exception as e:
        print(f"⚠️ Erro ao enviar: {e}")

def ler_mensagem():
    try:
        if not os.path.exists("entrada.json"):
            with open("entrada.json", "w") as f:
                json.dump({}, f)
            return None

        with open("entrada.json", "r") as f:
            data = json.load(f)
            if not data or "mensagem" not in data:
                return None
            return data
    except Exception as e:
        print(f"⚠️ Erro ao ler entrada.json: {e}")
        return None

def limpar():
    with open("entrada.json", "w") as f:
        json.dump({}, f)

while True:
    entrada = ler_mensagem()
    if entrada:
        numero = entrada["numero"]
        msg = entrada["mensagem"].lower()

        print(f"📨 Mensagem recebida de {numero}: {msg}")

        # Regras fixas
        if "zumo" not in msg:
            print("⏸ Ignorado — sem palavra-chave 'zumo'")
            limpar()
            time.sleep(5)
            continue

        if "@g.us" in numero:
            print("⏸ Ignorado — mensagem de grupo")
            limpar()
            time.sleep(5)
            continue

        # Responde qualquer comando do usuário principal
        resposta = f"🤖 CADIIA em operação — comando '{msg}' reconhecido."
        enviar_resposta(numero, resposta)
        limpar()

    time.sleep(10)
