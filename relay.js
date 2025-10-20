// relay.js — ponte entre Z-API e GitHub Actions
import express from "express";
import fetch from "node-fetch";

const app = express();
app.use(express.json());

// 🔥 Endpoint que a Z-API vai chamar
app.post("/webhook", async (req, res) => {
  try {
    const { phone, message } = req.body;

    if (!phone || !message) {
      return res.status(400).send("❌ Dados ausentes.");
    }

    console.log(`📩 Mensagem recebida: ${phone} -> ${message}`);

    // 🔁 Envia evento pro GitHub Actions
    const response = await fetch("https://api.github.com/repos/NatureIA/AIAGENT/dispatches", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        event_type: "mensagem_recebida",
        client_payload: { numero: phone, mensagem: message }
      })
    });

    if (response.status === 204) {
      console.log("✅ Workflow disparado no GitHub com sucesso!");
      res.status(200).send("OK");
    } else {
      const text = await response.text();
      console.error("⚠️ Falha ao chamar GitHub:", text);
      res.status(500).send(text);
    }
  } catch (err) {
    console.error("💥 Erro no relay:", err);
    res.status(500).send(err.message);
  }
});

// Porta padrão
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Relay ativo na porta ${PORT}`));
