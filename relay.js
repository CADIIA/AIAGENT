// relay.js — coleta mensagens da Z-API e aciona processar.py via GitHub Actions
import fetch from "node-fetch";
import fs from "fs";

const INSTANCE = process.env.ZAPI_INSTANCE;
const TOKEN = process.env.ZAPI_TOKEN;
const GH_TOKEN = process.env.GH_TOKEN;
const REPO = process.env.GITHUB_REPOSITORY;

if (!INSTANCE || !TOKEN) {
  console.error("❌ Falta INSTANCE ou TOKEN da Z-API.");
  process.exit(1);
}

console.log("🟢 Relay ativo — monitorando mensagens Z-API a cada 10s...");

async function verificarMensagens() {
  try {
    // ✅ endpoint garantido para mensagens não lidas
    const url = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/chats-messages/unread`;

    const res = await fetch(url);
    const msgs = await res.json();

    if (!Array.isArray(msgs)) return;

    for (const msg of msgs) {
      if (!msg || !msg.phone || !msg.message) continue;
      if (msg.fromMe || msg.isGroupMsg) continue; // ignora mensagens enviadas ou de grupos

      const numero = msg.phone;
      const mensagem = msg.message.trim();

      console.log(`📩 ${numero}: ${mensagem}`);

      // apenas reage se contiver a palavra "zumo"
      if (!mensagem.toLowerCase().includes("zumo")) continue;

      fs.writeFileSync("entrada.json", JSON.stringify({ numero, mensagem }));

      // dispara workflow do GitHub
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
        const txt = await gh.text();
        console.error(`⚠️ Erro ao disparar workflow: ${gh.status} - ${txt}`);
      }
    }
  } catch (err) {
    console.error("⚠️ Erro ao consultar Z-API:", err.message);
  }
}

setInterval(verificarMensagens, 10000);
verificarMensagens();



