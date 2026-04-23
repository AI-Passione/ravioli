# ravioli 🍝

![ravioli](docs/ravioli.png)

> AI-native, Notebook-style personal Data Warehouse for business-friendly vibe-analytics.

**ravioli** is a modern, open-source personal Data Warehouse (DWH) designed for the AI era. It combines the power of a professional data stack with the casual, interactive feel of a notebook. Part of the **AI Passione** ecosystem.

## 🚀 Vision: Vibe-Analytics for Everyone
Traditional DWHs are stiff and complex. **ravioli** is different. It's built to be:
- **AI-Native**: Built-in integration with LLMs (via Ollama) for natural language querying and automated insights.
- **Notebook-Style**: Interactive, iterative, and visual.
- **Business-Friendly**: Designed for people who want results, not just queries.
- **100% Local**: Your data stays on your machine. Privacy by design.
- **Tool-Agnostic**: Abstractions that let you swap tools while keeping your data architecture intact.

---

## 🛠 Features
- **Seamless Ingestion**: Python-based ingestors for Apple Health, Spotify, LinkedIn, Substack, and more.
- **AI-Driven Insights**: Integrated AI agents that understand your data and help you explore it.
- **Professional Transformation**: Powered by `dbt` for reliable, version-controlled data modeling.
- **Vibrant Visualization**: Built on Streamlit for a premium, interactive analytics experience.

---

## 🚦 Getting Started

### Launch Everything
Spin up the database, AI models, and the interface with a single command:

```bash
make up
```

This will:
1.  Start **Postgres** (Docker).
2.  Start the **Ollama** server and pull the `qwen2.5:3b` model.
3.  Launch the **Ravioli** Streamlit interface at `http://localhost:8501`.

### Python Setup
We use [uv](https://github.com/astral-sh/uv) for lightning-fast dependency management.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync environment
uv sync
```

---

## 🏗 Architecture & Tooling

| Category | Tools |
| :--- | :--- |
| **DWH** | Postgres |
| **Transformation** | [dbt Core](https://github.com/dbt-labs/dbt-core) |
| **AI Engine** | [Ollama](https://github.com/ollama/ollama) |
| **Interface** | [Streamlit](https://github.com/streamlit/streamlit) |
| **Orchestration** | Python / Makefile |
| **Package Manager** | [uv](https://github.com/astral-sh/uv) |

---

## 🏗 Folder Structure
Ravioli follows a strict modular structure where tooling is materialized through the filesystem:

```text
.
├── src/ravioli/             # Core logic & applications
│   ├── apps/                # Interactive analytics & AI agents
│   ├── ingestion/           # Data connectors (Apple Health, Spotify, etc.)
│   ├── db/                  # Database session & initialization
│   └── core/                # Shared configurations & dbt wrappers
├── docker/                  # Infrastructure (Docker Compose, .env)
├── docs/                    # Architecture RFCs & diagrams
├── prompts/                 # AI system prompts & LLM context
└── pyproject.toml           # Project metadata
```

---

## 🇮🇹 AI Passione Theme
Ravioli is part of the **AI Passione** suite—rebranded from the ground up to bring "passione" back into data engineering. It's about craft, quality, and the joy of discovery.

*Formerly known as Jimwurst.*
