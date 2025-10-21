// relay.js
// 🔁 Repassa as mensagens recebidas da Z-API direto para o GitHub Actions

import express from "express";
import fetch from "node-fetch";

const app = express();
app.use(express.json());

const GH_REPO = process.env.GITHUB_REPOSITORY || "CADIIA/AIAGENT";
const GH_TOKEN = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;

// 🔔 Recebe mensagens enviadas pela Z-API
app.post("/relay", async (req, res) => {
  try {
    const dados = req.body;
    console.log("📩 Mensagem recebida via webhook:", dados);

    // Salva o conteúdo no arquivo entrada.json via workflow
    const url = `https://api.github.com/repos/${GH_REPO}/actions/workflows/whatsapp.yml/dispatches`;

    const body = {
      ref: "main",
      inputs: {
        mensagem: JSON.stringify(dados)
      }
    };

    const r = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${GH_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });

    if (r.status === 204) {
      console.log("✅ Workflow disparado com sucesso!");
      res.status(200).json({ ok: true });
    } else {
      const txt = await r.text();
      console.log("⚠️ Falha ao disparar workflow:", txt);
      res.status(500).json({ erro: txt });
    }
  } catch (e) {
    console.error("❌ Erro no relay:", e);
    res.status(500).json({ erro: e.message });
  }
});

// ✅ Mantém online
app.get("/", (_, res) => res.send("🟢 Relay ativo e aguardando eventos da Z-API."));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Relay escutando na porta ${PORT}`));
