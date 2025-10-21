// relay.js — versão estável unificada (Z-API + GitHub Dispatch + compat geral)

import fs from "fs";
import fetch from "node-fetch";

const INSTANCE = process.env.ZAPI_INSTANCE;
const TOKEN = process.env.ZAPI_TOKEN;
const GH_TOKEN = process.env.GH_TOKEN;
const REPO = process.env.GITHUB_REPOSITORY;

// endpoint universal que cobre /chats-messages/unread e /get-messages
const urlBase = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}`;

async function getMensagens() {
  try {
    let resp = await fetch(`${urlBase}/chats-messages/unread`);
    if (!resp.ok) resp = await fetch(`${urlBase}/get-messages`);
    const data = await resp.json();

    if (!Array.isArray(data) || data.length === 0) return;

    for (const msg of data) {
      const texto = (msg.message || msg.text?.body || "").toLowerCase();
      if (texto.includes("zumo") && !msg.fromMe) {
        const payload = {
          numero: msg.phone || msg.chatId || msg.remoteJid || "desconhecido",
          mensagem: texto,
        };
        fs.writeFileSync("entrada.json", JSON.stringify(payload, null, 2));
        console.log(`📩 ${payload.numero}: ${payload.mensagem}`);

        // dispara o workflow com token pessoal ou GITHUB_TOKEN (agora permitido)
        const dispatch = await fetch(
          `https://api.github.com/repos/${REPO}/dispatches`,
          {
            method: "POST",
            headers: {
              Authorization: `token ${GH_TOKEN}`,
              Accept: "application/vnd.github.v3+json",
            },
            body: JSON.stringify({
              event_type: "mensagem_recebida",
              client_payload: payload,
            }),
          }
        );

        if (!dispatch.ok) {
          const t = await dispatch.text();
          console.error("❌ Falha ao disparar workflow:", dispatch.status, t);
        } else {
          console.log("🚀 Workflow disparado com sucesso!");
        }
      }
    }
  } catch (err) {
    console.error("⚠️ Erro geral no relay:", err.message);
  }
}

// loop
console.log("🟢 Relay ativo — monitorando mensagens Z-API a cada 10s...");
setInterval(getMensagens, 10000);
