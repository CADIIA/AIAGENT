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
    // ✅ endpoint atualizado (era /messages → agora é /receive-messages)
    const url = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/receive-messages`;
    const res = await fetch(url);
    const msgs = await res.json();

    if (!Array.isArray(msgs)) return;

    for (const msg of msgs) {
      if (!msg || !msg.phone || !msg.message) continue;
      if (msg.fromMe) continue;

      const numero = msg.phone;
      const mensagem = msg.message.trim();

      console.log(`📩 ${numero}: ${mensagem}`);

      // Salva mensagem localmente
      fs.writeFileSync("entrada.json", JSON.stringify({ numero, mensagem }));

      // Envia resposta automática
      await fetch(`https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/send-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: numero,
          message: "✅ Mensagem recebida. Processando..."
        })
      });
    }
  } catch (err) {
    console.error("⚠️ Erro ao consultar Z-API:", err.message);
  }
}

setInterval(verificarMensagens, 10000);
verificarMensagens();
