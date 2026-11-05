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
  <a href="https://hub.xerj.org/contributors/Rayck4dev"><img src="https://hub.xerj.org/contributors/Rayck4dev/badge.svg" alt="XERJ Corpus Hub contributor" /></a>
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
│   ├── test.jsonl              # Evaluation data
│   ├── candidates/             # Locally generated data awaiting review
│   └── rebuilt/                # Reviewed, concept-separated dataset splits
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
python -m pip install requests
```

The local API and dataset utilities only need `requests`. The broader `requirements.txt` includes GPU fine-tuning packages and may not install on Windows; use a compatible GPU runtime for the notebook/training dependencies.

Run the dataset pipeline tests from the repository root with:

```bash
python -m unittest discover -s tests -v
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

The batch processor and API check discover the first model returned by `/v1/models`. To pin a model, set `JARGAOZERO_LLM_MODEL`; to change the server URL, set `JARGAOZERO_API_BASE_URL` (the value should end in `/v1`).

### Rebuild and evaluate a dataset locally

The checked-in dataset and split files are preserved. The rebuild workflow writes new files under `data/candidates/` and `data/rebuilt/` instead.

1. Install `requests` as described above and start the LM Studio server on port `1235` with a model loaded.
2. Generate resumable candidate examples from the project’s existing term definitions:

   ```bash
   python scripts/rebuild_dataset.py --generate
   ```

   This creates three explanations (`Leigo`, `Estudante`, and `Técnico`) per concept. The default run targets 66 concepts (198 prompt/answer pairs). To change the API URL, set `JARGAOZERO_API_BASE_URL`; an optional `--model` argument pins a model ID. Slow local models can use a longer per-concept timeout with `--request-timeout 1800`.
3. Review and edit `data/candidates/rebuilt_dataset.jsonl` for factual accuracy, clarity, and distinct difficulty levels. The generator’s checks do not replace human review.
4. After review, create deterministic train/validation/test splits with concepts kept in a single split:

   ```bash
   python scripts/rebuild_dataset.py --split-reviewed --confirm-reviewed
   ```

   The command refuses to overwrite existing files unless `--overwrite` is supplied.
5. Validate each resulting JSONL file:

   ```bash
   python scripts/validate_dataset.py data/rebuilt/train.jsonl
   python scripts/validate_dataset.py data/rebuilt/validation.jsonl
   python scripts/validate_dataset.py data/rebuilt/test.jsonl
   ```

The existing `data/train.jsonl`, `data/validation.jsonl`, `data/test.jsonl`, and `training_dataset.jsonl` are legacy data; their previous random record-level split is not a leakage-free evaluation set. Do not report results from them as a clean held-out benchmark.

Evaluate the existing model results with the corrected metrics:

```bash
python scripts/evaluate_metrics.py --results data/evaluation_results.json --output data/rebuilt/metrics.json
```

The evaluator reports normalized exact match, token-overlap F1, TF-IDF cosine **lexical** similarity, and a heuristic Portuguese Flesch estimate. These automatic lexical/readability measures do not establish semantic correctness; use human review for quality claims. An optional `--baseline path/to/baseline.json` compares a baseline only when both files contain the same prompts (or IDs) and references.

The corrected measurements for the existing 25 outputs are recorded in [`docs/metrics_summary.json`](./docs/metrics_summary.json). They are not a clean generalization benchmark because the legacy record-level split has concept overlap.

Dataset generation and inference can run locally through LM Studio. QLoRA fine-tuning still requires a supported GPU environment. This workspace's Python environment currently has no PyTorch installation or detected `nvidia-smi` command, so fine-tuning cannot be run here yet.

## Technical report

The technical reports are available in [Portuguese](./docs/Relatorio_Tecnico_JargaoZero_Llama3.pdf) and [English](./docs/Technical_Report_JargaoZero_Llama3_en.pdf).

## Dataset quality goals

- **Valid format:** Keep `.jsonl` records structurally consistent and parseable.
- **No duplicates:** Avoid repeated entries for the same technical term.
- **Concept diversity:** Include topics such as network latency, database architecture, multi-tier caching, microservices, and security.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
