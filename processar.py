import json, os, requests, time, threading
from openai import OpenAI

# ✅ Configura o cliente OpenRouter
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ✅ Variáveis de ambiente da Z-API e GitHub
instance = os.getenv("ZAPI_INSTANCE")
token = os.getenv("ZAPI_TOKEN")

# =========================================================
# 🔁 FUNÇÃO PRINCIPAL — Monitora e responde automaticamente
# =========================================================
def processar_mensagens():
    ultimo_id = None
    while True:
        try:
            url = f"https://api.z-api.io/instances/{instance}/token/{token}/chats/messages"
            r = requests.get(url)
            if r.status_code != 200:
                print(f"⚠️ Erro ao buscar mensagens: {r.text}")
                time.sleep(10)
                continue

            mensagens = r.json()

            if not isinstance(mensagens, list):
                print("⚠️ Nenhuma mensagem válida recebida.")
                time.sleep(10)
                continue

            for msg in mensagens:
                if not msg.get("message"):
                    continue

                msg_id = msg.get("id")
                numero = msg.get("phone")
                texto = msg.get("message", "").strip()

                # Ignora mensagens repetidas
                if msg_id == ultimo_id:
                    continue

                ultimo_id = msg_id

                # 🔒 Ignora grupos
                if "-" in numero:
                    print(f"🚫 Ignorada (grupo): {numero}")
                    continue

                # 🔒 Só responde se começar com "zumo"
                if not texto.lower().startswith("zumo"):
                    print(f"⏸️ Ignorada (sem comando): {texto}")
                    continue

                print(f"📩 Nova mensagem válida de {numero}: {texto}")

                # Remove o comando "zumo"
                mensagem_limpa = texto[len("zumo"):].strip()

                # 🤖 Gera resposta
                try:
                    resposta = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Você é um atendente virtual simpático, profissional e direto."},
                            {"role": "user", "content": mensagem_limpa}
                        ]
                    ).choices[0].message.content
                except Exception as e:
                    print(f"❌ Erro na API OpenRouter: {e}")
                    continue

                print(f"🤖 Resposta gerada: {resposta}")

                # 📤 Envia a resposta no WhatsApp
                payload = [{"phone": numero, "message": resposta}]
                headers = {"Content-Type": "application/json"}
                enviar = requests.post(
                    f"https://api.z-api.io/instances/{instance}/token/{token}/send-messages",
                    json=payload,
                    headers=headers
                )

                if enviar.status_code == 200:
                    print(f"✅ Mensagem enviada para {numero}")
                else:
                    print(f"❌ Falha ao enviar mensagem: {enviar.text}")

        except Exception as e:
            print(f"⚠️ Erro geral no loop: {e}")

        time.sleep(10)  # 🔁 Executa novamente a cada 10 segundos


# =========================================================
# 🔁 BLOCO ADICIONADO — operação contínua 24/7
# =========================================================

def manter_logs():
    while True:
        print("🟢 Agente ativo —", time.strftime("%H:%M:%S"))
        time.sleep(300)

threading.Thread(target=manter_logs, daemon=True).start()

def manter_ativo():
    repo = os.getenv("GITHUB_REPOSITORY", "NatureIA/AIAGENT")
    token_gh = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token_gh:
        print("⚠️ Sem token do GitHub, não é possível reiniciar.")
        return
    url = f"https://api.github.com/repos/{repo}/actions/workflows/whatsapp.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {token_gh}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"ref": "main"}
    try:
        print("⏳ Preparando novo ciclo de execução...")
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 204:
            print("✅ Novo ciclo iniciado com sucesso (agente contínuo).")
        else:
            print(f"⚠️ Falha ao reiniciar: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Erro ao reiniciar ciclo: {e}")

# =========================================================
# 🚀 EXECUÇÃO
# =========================================================
print("🚀 Iniciando agente autônomo WhatsApp GPT (GitHub + Z-API)")
processar_mensagens()

# Chama reinício automático ao encerrar
manter_ativo()
print("🏁 Execução finalizada — ciclo contínuo garantido.")
