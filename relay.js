// relay.js — CADIIA WhatsApp Agent (versão contínua e autônoma)
import fetch from "node-fetch";
import fs from "fs";

const INSTANCE = process.env.ZAPI_INSTANCE;
const TOKEN = process.env.ZAPI_TOKEN;
const GH_TOKEN = process.env.GH_TOKEN;
const REPO = process.env.GITHUB_REPOSITORY;

if (!INSTANCE || !TOKEN || !GH_TOKEN || !REPO) {
  console.error("❌ Variáveis de ambiente ausentes.");
  process.exit(1);
}

console.log("🟢 Relay CADIIA ativo — ciclo contínuo iniciado...");

// cria o arquivo de entrada inicial, para evitar erro “no such file”
try {
  if (!fs.existsSync("entrada.json")) {
    fs.writeFileSync("entrada.json", JSON.stringify({ numero: "debug", mensagem: "inicial" }));
  }
} catch (e) {
  console.error("⚠️ Falha ao criar entrada.json inicial:", e.message);
}

// Função principal
async function verificarMensagens() {
  try {
    const url = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/chats`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.error) {
      console.error("⚠️ Erro da Z-API:", data.error);
      return;
    }

    if (!data || !Array.isArray(data.chats)) {
      console.log("ℹ️ Nenhuma conversa encontrada.");
      return;
    }

    for (const chat of data.chats) {
      if (!chat || !chat.phone || !chat.lastMessage) continue;
      const numero = chat.phone;
      const mensagem = chat.lastMessage.text?.trim() || "";

      if (!mensagem || chat.lastMessage.fromMe) continue;

      console.log(`📩 ${numero}: ${mensagem}`);

      // reage apenas se contiver “zumo”
      if (!mensagem.toLowerCase().includes("zumo")) continue;

      fs.writeFileSync("entrada.json", JSON.stringify({ numero, mensagem }));

      // dispara workflow GitHub
      const dispatchUrl = `https://api.github.com/repos/${REPO}/dispatches`;
      const payload = {
        event_type: "mensagem_recebida",
        client_payload: { numero, mensagem },
      };

      const gh = await fetch(dispatchUrl, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${GH_TOKEN}`,
          Accept: "application/vnd.github+json",
        },
        body: JSON.stringify(payload),
      });

      if (gh.status === 204) {
        console.log("🚀 Workflow disparado com sucesso!");
      } else {
        const erro = await gh.text();
        console.error(`⚠️ Erro ao disparar workflow: ${gh.status} - ${erro}`);
      }
    }
  } catch (err) {
    console.error("⚠️ Erro geral ao consultar Z-API:", err.message);
  }
}

// loop infinito com atraso controlado
async function iniciarCiclo() {
  while (true) {
    await verificarMensagens();
    await new Promise((r) => setTimeout(r, 10000)); // espera 10s antes de verificar de novo
  }
}

iniciarCiclo();
