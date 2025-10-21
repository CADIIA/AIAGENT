// relay.js — CADIIA WhatsApp Agent (versão final)
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

console.log("🟢 Relay ativo — monitorando mensagens Z-API a cada 10 s...");

// cria um arquivo de debug para evitar erro “no such file”
try {
  fs.writeFileSync("entrada.json", JSON.stringify({ numero: "debug", mensagem: "inicial" }));
} catch (e) {
  console.error("⚠️ Falha ao criar entrada.json inicial:", e.message);
}

async function verificarMensagens() {
  try {
    // endpoint correto da Z-API para listar conversas
    const url = `https://api.z-api.io/instances/${INSTANCE}/token/${TOKEN}/chats`;
    const res = await fetch(url);
    const data = await res.json();

    if (!data || !Array.isArray(data.chats)) return;

    for (const chat of data.chats) {
      if (!chat || !chat.phone || !chat.lastMessage) continue;
      const numero = chat.phone;
      const mensagem = chat.lastMessage.text?.trim() || "";

      if (!mensagem || chat.lastMessage.fromMe) continue;

      console.log(`📩 ${numero}: ${mensagem}`);

      // reage apenas quando contiver “zumo”
      if (!mensagem.toLowerCase().includes("zumo")) continue;

      fs.writeFileSync("entrada.json", JSON.stringify({ numero, mensagem }));

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
        console.error(`⚠️ Erro ao disparar workflow: ${gh.status}`);
        const erroTxt = await gh.text();
        console.error(erroTxt);
      }
    }
  } catch (err) {
    console.error("⚠️ Erro ao consultar Z-API:", err.message);
  }
}

setInterval(verificarMensagens, 10000);
verificarMensagens();
