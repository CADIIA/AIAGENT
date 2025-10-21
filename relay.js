// ===============================
// 🔁 relay.js — Agente Z-API + GitHub 24/7
// ===============================

import fs from "fs";
import fetch from "node-fetch";

const INSTANCE = process.env.ZAPI_INSTANCE;
const TOKEN = process.env.ZAPI_TOKEN;
const GH_TOKEN = process.env.GH_TOKEN;
const REPO = process.env.GITHUB_REPOSITORY;

if (!INSTANCE || !TOKEN || !GH_TOKEN || !REPO) {
  console.error("❌ Variáveis de ambiente ausentes.");
  process.exit(1);
}

console.log("🟢 Relay iniciado — monitorando mensagens a cada 10s...");

async function verificarMensagens() {
  try {
    const url = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/messages`;
    const r = await fetch(url);
    const data = await r.json();

    if (!data || !Array.isArray(data)) return;

    for (const msg of data) {
      if (!msg || !msg.phone || !msg.message) continue;
      if (msg.fromMe) continue; // Ignora mensagens enviadas pelo próprio bot

      const numero = msg.phone;
      const mensagem = msg.message.trim();

      // Salva no entrada.json
      fs.writeFileSync(
        "entrada.json",
        JSON.stringify({ numero, mensagem }, null, 2),
        "utf8"
      );

      console.log(`📩 Nova mensagem: ${numero} => ${mensagem}`);

      // Commit no GitHub para disparar o workflow
      await fetch(
        `https://api.github.com/repos/${REPO}/contents/entrada.json`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${GH_TOKEN}`,
            Accept: "application/vnd.github+json",
          },
          body: JSON.stringify({
            message: `Atualização automática - ${new Date().toISOString()}`,
            content: Buffer.from(
              JSON.stringify({ numero, mensagem }, null, 2)
            ).toString("base64"),
          }),
        }
      );

      console.log("🚀 Workflow disparado com sucesso.");
    }
  } catch (e) {
    console.error("⚠️ Erro ao verificar mensagens:", e.message);
  }
}

// Loop a cada 10 segundos
setInterval(verificarMensagens, 10000);
verificarMensagens();
