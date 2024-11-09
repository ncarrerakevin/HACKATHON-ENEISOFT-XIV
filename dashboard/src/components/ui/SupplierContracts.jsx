const OpenAI = require("openai");
require("dotenv").config();

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

async function testGPTAnalysis(req, res) {
    try {
        const message = `
      Analiza esta información de un proveedor del Estado:
      - Nombre: CORPORACION BRAVO-SANCHEZ S.R.L
      - Total de adjudicaciones: 1
      - Valor promedio de contratos: S/. 320,112.00
      - % de adjudicaciones rápidas: 0%
      - Número de compradores únicos: 0

      Proporciona:
      1. Análisis de patrones de contratación
      2. Posibles banderas rojas o puntos de atención
      3. Recomendaciones para supervisión
      4. Comparación con patrones típicos del mercado
    `;

        const response = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [{ role: "user", content: message }],
            temperature: 0,
            max_tokens: 1000,
        });
        res.status(200).json(response);
    } catch (err) {
        res.status(500).json(err.message);
    }
}

module.exports = { testGPTAnalysis };
