// ===============================
// 🔁 relay.js — Z-API + GitHub Dispatch automático
// ===============================

import fetch from "node-fetch";

const INSTANCE = process.env.ZAPI_INSTANCE;
const TOKEN = process.env.ZAPI_TOKEN;
const GH_TOKEN = process.env.GH_TOKEN;
const REPO = process.env.GITHUB_REPOSITORY;

if (!INSTANCE || !TOKEN || !GH_TOKEN || !REPO) {
  console.error("❌ Variáveis de ambiente ausentes.");
  process.exit(1);
}

console.log("🟢 Relay iniciado — verificando mensagens a cada 10s...");

async function verificarMensagens() {
  try {
    const url = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/messages`;
    const r = await fetch(url);
    const mensagens = await r.json();

    if (!Array.isArray(mensagens)) return;

    for (const msg of mensagens) {
      if (!msg || !msg.phone || !msg.message) continue;
      if (msg.fromMe) continue; // Ignora mensagens enviadas pelo bot

      const numero = msg.phone;
      const mensagem = msg.message.trim();

      console.log(`📩 Nova mensagem: ${numero} => ${mensagem}`);

      // Dispara evento repository_dispatch no GitHub
      const dispatchUrl = `https://api.github.com/repos/${REPO}/dispatches`;
      const payload = {
        event_type: "mensagem_recebida",
        client_payload: { numero, mensagem },
      };

      const response = await fetch(dispatchUrl, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${GH_TOKEN}`,
          Accept: "application/vnd.github+json",
        },
        body: JSON.stringify(payload),
      });

      if (response.status === 204) {
        console.log("🚀 Workflow disparado com sucesso!");
      } else {
        const txt = await response.text();
        console.error(`⚠️ Erro ao disparar workflow: ${response.status} - ${txt}`);
      }
    }
  } catch (e) {
    console.error("⚠️ Erro ao verificar mensagens:", e.message);
  }
}

setInterval(verificarMensagens, 10000);
verificarMensagens();
