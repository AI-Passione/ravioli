# ravioli 🍝

![ravioli](src/ravioli/frontend/public/ravioli-logo.png)

> AI-native, Notebook-style personal Data Warehouse for business-friendly vibe-analytics.

**ravioli** is a modern, open-source personal Data Warehouse (DWH) designed for the AI era. It combines the power of a professional data stack with the casual, interactive feel of a notebook. Part of the **AI Passione** ecosystem.

## 🚀 Vision: Vibe-Analytics for Everyone
Traditional DWHs are stiff and complex. **ravioli** is different. It's built to be:
- **AI-Native**: Ready for integration with LLMs for natural language querying and automated insights.
- **Notebook-Style**: Interactive, iterative, and visual.
- **Business-Friendly**: Designed for people who want results, not just queries.
- **100% Local**: Your data stays on your machine. Privacy by design.
- **Tool-Agnostic**: Abstractions that let you swap tools while keeping your data architecture intact.

---

## 🛠 Features
- **Seamless Ingestion**: Python-based ingestors for Apple Health, Spotify, LinkedIn, Substack, and more.
- **AI-Driven Insights**: Integrated AI agents that understand your data and help you explore it.
- **Professional Transformation**: Powered by `dbt` for reliable, version-controlled data modeling.
- **Vibrant Visualization**: Built on Vanilla TypeScript for a premium, interactive analytics experience.

---

## 🚦 Getting Started

### Launch Everything
Spin up the database, AI models, and the interface with a single command:

```bash
make up
```

This will:
1.  Start **Postgres** (Docker).
2.  Launch the **Ravioli** interface at `http://localhost:5173`.

### Python Setup
We use [uv](https://github.com/astral-sh/uv) for lightning-fast dependency management.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync environment
uv sync
```

---

## 🇮🇹 AI Passione Theme
Ravioli is part of the **AI Passione** suite—rebranded from the ground up to bring "passione" back into data engineering. It's about craft, quality, and the joy of discovery.

*Formerly known as Jimwurst.*
