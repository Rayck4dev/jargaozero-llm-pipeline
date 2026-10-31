# JargãoZero

<p align="center">
  <img src="./app/public/favicon.svg" width="72" alt="JargãoZero logo" />
</p>

<p align="center">
  English | <a href="./README.pt-BR.md">Português (Brasil)</a>
</p>

<p align="center">
  Turn complex technical language into clear, accessible Portuguese with a responsive React interface, local LLM inference, and automated dataset tools.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <a href="https://lmstudio.ai/"><img src="https://img.shields.io/badge/LM%20Studio-8A2BE2?style=for-the-badge&logo=lmstudio&logoColor=white" alt="LM Studio" /></a>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <a href="https://colab.research.google.com/github/Rayck4dev/jargaozero-llm-pipeline/blob/main/notebook/Jarg%C3%A3oZero_LLM.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Google Colab" /></a>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License MIT" />
</p>

---

## About

**JargãoZero** makes software architecture, database, and systems terminology easier to understand in Portuguese. It combines a browser-based translator, locally hosted language models, few-shot prompting, and dataset utilities for model evaluation and fine-tuning workflows.

## Features

- **Responsive translator:** Paste technical text or choose a built-in example, select an explanation level, and view or copy the simplified result.
- **Local model inference:** Sends requests to an OpenAI-compatible API, such as LM Studio, keeping inference on your machine.
- **Automatic model selection:** Reads the available model ID from the local `/v1/models` endpoint. You can optionally configure a specific model.
- **Dataset tools:** Includes scripts for processing, generating, splitting, deduplicating, and validating JSONL datasets.
- **Fine-tuning and evaluation data:** Includes training, validation, and test datasets for experimentation.

## Repository structure

```text
.
├── app/                       # React, Vite, and Tailwind CSS frontend
│   ├── public/                 # Static assets
│   └── src/                    # Translator interface
├── data/
│   ├── train.jsonl             # Training data
│   ├── validation.jsonl        # Validation data
│   └── test.jsonl              # Evaluation data
├── docs/                       # Evaluation and project documentation
├── models/                     # Model configuration files
├── notebook/                   # Jupyter notebooks
├── scripts/                    # Dataset and local API utilities
├── requirements.txt            # Python dependencies
├── results_jargaozero.jsonl    # Processed translation results
└── training_dataset.jsonl      # Curated training dataset
```

## Web application

### Prerequisites

- Node.js and npm
- [LM Studio](https://lmstudio.ai/) or another server implementing the OpenAI-compatible chat completions API
- A model loaded in the local inference server

### Configure the local model server

1. In LM Studio, download and **load** a model. Setting a default or root model alone does not load it.
2. Start the local server with the OpenAI-compatible API enabled on port `1235`.
3. Enable CORS in the server settings so the browser-based frontend can make requests.

The default API base URL is `http://localhost:1235/v1`. The frontend checks `/models` and uses the first available model. If no model is loaded, it displays a message explaining what to do.

### Install and run the frontend

```bash
cd app
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

### Optional frontend environment variables

Create `app/.env.local` to use a different API URL or pin a model ID:

```dotenv
VITE_API_BASE_URL=http://localhost:1235/v1
VITE_LLM_MODEL=your-loaded-model-id
```

`VITE_API_BASE_URL` must be the API base URL ending in `/v1`, not the full `/chat/completions` path. When `VITE_LLM_MODEL` is set, the frontend sends that model ID instead of discovering one through `/models`. Restart the Vite server after changing environment variables.

### Frontend checks

Run these commands from the `app/` directory:

```bash
npm run lint
npm run build
```

## Python utilities

Python 3.10 or later is recommended. To install the dependencies used by the project:

```bash
python -m pip install -r requirements.txt
```

To check the local chat completions API:

```bash
python scripts/test_api.py
```

The batch processor reads `train.jsonl` from its current working directory and writes `results_jargaozero.jsonl` there. Run it from `data/` so it uses the included training split:

```bash
cd data
python ../scripts/batch_process.py
```

The Python batch processor currently uses the model ID configured in `scripts/batch_process.py`; update it there if your local server expects a different ID.

## Technical report

The technical report is currently available in Portuguese: [`docs/Relatorio_Tecnico_JargaoZero_Llama3.pdf`](./docs/Technical_Report_JargaoZero_Llama3_en.pdf).

## Dataset quality goals

- **Valid format:** Keep `.jsonl` records structurally consistent and parseable.
- **No duplicates:** Avoid repeated entries for the same technical term.
- **Concept diversity:** Include topics such as network latency, database architecture, multi-tier caching, microservices, and security.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
