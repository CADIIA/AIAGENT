// relay.js — consulta Z-API e grava mensagens localmente (loop contínuo)
import fetch from "node-fetch";
import fs from "fs";

const INSTANCE = process.env.ZAPI_INSTANCE;
const TOKEN = process.env.ZAPI_TOKEN;

if (!INSTANCE || !TOKEN) {
  console.error("❌ Faltam variáveis ZAPI_INSTANCE ou ZAPI_TOKEN.");
  process.exit(1);
}

console.log("🟢 Relay CADIIA ativo — ciclo contínuo iniciado...");

async function verificarMensagens() {
  try {
    const url = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/chats`;
    const res = await fetch(url);
    const data = await res.json();

    if (!Array.isArray(data)) return;

    for (const chat of data) {
      if (!chat?.messages) continue;

      for (const msg of chat.messages) {
        if (!msg?.text?.body) continue;
        if (msg.fromMe || msg.isGroupMsg) continue;

        const numero = msg.chatId.replace("@c.us", "");
        const mensagem = msg.text.body.trim();

        console.log(`📩 ${numero}: ${mensagem}`);

        if (!mensagem.toLowerCase().includes("zumo")) continue;

        fs.writeFileSync("entrada.json", JSON.stringify({ numero, mensagem }));

        console.log("✅ Mensagem salva para processamento.");
      }
    }
  } catch (err) {
    console.error("⚠️ Erro da Z-API:", err.message);
  }
}

async function ciclo() {
  while (true) {
    await verificarMensagens();
    await new Promise(r => setTimeout(r, 10000)); // espera 10s
  }
}

ciclo();
