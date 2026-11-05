# JargãoZero

<p align="center">
  <img src="./app/public/favicon.svg" width="72" alt="Logo do JargãoZero" />
</p>

<p align="center">
  Transforme termos técnicos complexos em explicações claras e acessíveis em português com uma interface React responsiva, inferência local por LLM e ferramentas para conjuntos de dados.
</p>

<p align="center">
  <a href="./README.md">English</a> | Português (Brasil)
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <a href="https://lmstudio.ai/"><img src="https://img.shields.io/badge/LM%20Studio-8A2BE2?style=for-the-badge&logo=lmstudio&logoColor=white" alt="LM Studio" /></a>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <a href="https://colab.research.google.com/github/Rayck4dev/jargaozero-llm-pipeline/blob/main/notebook/Jarg%C3%A3oZero_LLM.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Abrir no Google Colab" /></a>
  <img src="https://img.shields.io/badge/Licença-MIT-yellow.svg?style=for-the-badge" alt="Licença MIT" />
  <a href="https://hub.xerj.org/contributors/Rayck4dev"><img src="https://hub.xerj.org/contributors/Rayck4dev/badge.svg" alt="XERJ Corpus Hub contributor" /></a>
</p>

---

## Sobre

O **JargãoZero** facilita o entendimento de termos de arquitetura de software, bancos de dados e sistemas em português. O projeto combina um tradutor acessado pelo navegador, modelos de linguagem executados localmente, prompts few-shot e ferramentas para preparar conjuntos de dados para avaliação e ajuste fino.

## Funcionalidades

- **Tradutor responsivo:** Cole um texto técnico ou escolha um exemplo, selecione o nível de explicação e consulte ou copie o resultado simplificado.
- **Inferência local:** Envia solicitações para uma API compatível com OpenAI, como a do LM Studio, mantendo a inferência na sua máquina.
- **Seleção automática do modelo:** Consulta o endpoint local `/v1/models` e usa o identificador do primeiro modelo disponível. Também é possível configurar um modelo específico.
- **Ferramentas para datasets:** Inclui scripts para processar, gerar, dividir, remover duplicatas e validar conjuntos de dados JSONL.
- **Dados para ajuste fino e avaliação:** Inclui divisões de treino, validação e teste para experimentação.

## Estrutura do repositório

```text
.
├── app/                       # Frontend em React, Vite e Tailwind CSS
│   ├── public/                 # Arquivos estáticos
│   └── src/                    # Interface do tradutor
├── data/
│   ├── train.jsonl             # Dados de treino
│   ├── validation.jsonl        # Dados de validação
│   ├── test.jsonl              # Dados de avaliação
│   ├── candidates/             # Dados locais gerados, aguardando revisão
│   └── rebuilt/                # Divisões revisadas e separadas por conceito
├── docs/                       # Relatórios e documentação do projeto
├── models/                     # Arquivos de configuração de modelos
├── notebook/                   # Notebooks Jupyter
├── scripts/                    # Ferramentas para datasets e API local
├── requirements.txt            # Dependências Python
├── results_jargaozero.jsonl    # Resultados de traduções processadas
└── training_dataset.jsonl      # Dataset de treino curado
```

## Aplicação web

### Pré-requisitos

- Node.js e npm
- [LM Studio](https://lmstudio.ai/) ou outro servidor com suporte à API de chat completions compatível com OpenAI
- Um modelo carregado no servidor de inferência local

### Configure o servidor de modelos local

1. No LM Studio, baixe e **carregue** um modelo. Definir um modelo padrão ou raiz, por si só, não o carrega.
2. Inicie o servidor local com a API compatível com OpenAI ativada na porta `1235`.
3. Habilite CORS nas configurações do servidor para permitir solicitações do frontend no navegador.

A URL base padrão da API é `http://localhost:1235/v1`. O frontend consulta `/models` e usa o primeiro modelo disponível. Se nenhum modelo estiver carregado, a interface exibe instruções para carregá-lo.

### Instale e execute o frontend

```bash
cd app
npm install
npm run dev
```

Abra o endereço local exibido pelo Vite, normalmente `http://localhost:5173`.

### Variáveis de ambiente opcionais do frontend

Crie `app/.env.local` para usar outra URL da API ou definir um identificador de modelo:

```dotenv
VITE_API_BASE_URL=http://localhost:1235/v1
VITE_LLM_MODEL=identificador-do-modelo-carregado
```

`VITE_API_BASE_URL` deve ser a URL base da API, terminando em `/v1`, e não o caminho completo `/chat/completions`. Se `VITE_LLM_MODEL` estiver definido, o frontend enviará esse identificador em vez de consultar `/models`. Reinicie o servidor Vite após alterar as variáveis de ambiente.

### Verificações do frontend

Execute os comandos abaixo dentro da pasta `app/`:

```bash
npm run lint
npm run build
```

## Ferramentas Python

Recomenda-se Python 3.10 ou superior. Para instalar as dependências do projeto:

```bash
python -m pip install requests
```

As ferramentas locais de API e datasets precisam apenas de `requests`. O arquivo `requirements.txt` inclui dependências de ajuste fino por GPU e pode não ser instalável no Windows; use um ambiente GPU compatível para as dependências do notebook/treinamento.

Execute os testes do fluxo de datasets na raiz do repositório:

```bash
python -m unittest discover -s tests -v
```

Para verificar a conexão com a API local de chat completions:

```bash
python scripts/test_api.py
```

O processador em lote procura `train.jsonl` no diretório de trabalho atual e grava `results_jargaozero.jsonl` nesse mesmo diretório. Execute-o a partir de `data/` para usar a divisão de treino incluída:

```bash
cd data
python ../scripts/batch_process.py
```

O processador em lote e o teste da API descobrem o primeiro modelo retornado por `/v1/models`. Para fixar um modelo, defina `JARGAOZERO_LLM_MODEL`; para alterar a URL do servidor, defina `JARGAOZERO_API_BASE_URL` (o valor deve terminar em `/v1`).

### Reconstruir e avaliar um dataset localmente

Os datasets e as divisões existentes são preservados. O fluxo de reconstrução grava novos arquivos em `data/candidates/` e `data/rebuilt/`.

1. Instale `requests` como descrito acima e inicie o servidor do LM Studio na porta `1235`, com um modelo carregado.
2. Gere candidatos retomáveis a partir das definições de termos já existentes no projeto:

   ```bash
   python scripts/rebuild_dataset.py --generate
   ```

   São criadas três explicações por conceito (`Leigo`, `Estudante` e `Técnico`). A execução padrão usa 66 conceitos (198 pares de entrada/saída). Para alterar a URL da API, defina `JARGAOZERO_API_BASE_URL`; também é possível fixar o ID do modelo com `--model`. Modelos locais lentos podem usar um tempo limite maior por conceito com `--request-timeout 1800`.
3. Revise e edite manualmente `data/candidates/rebuilt_dataset.jsonl`, verificando precisão factual, clareza e diferenças reais entre os níveis. As verificações automáticas do gerador não substituem a revisão humana.
4. Após a revisão, crie divisões determinísticas de treino/validação/teste, mantendo cada conceito em uma única divisão:

   ```bash
   python scripts/rebuild_dataset.py --split-reviewed --confirm-reviewed
   ```

   O comando não substitui arquivos existentes, a menos que `--overwrite` seja informado.
5. Valide cada arquivo JSONL gerado:

   ```bash
   python scripts/validate_dataset.py data/rebuilt/train.jsonl
   python scripts/validate_dataset.py data/rebuilt/validation.jsonl
   python scripts/validate_dataset.py data/rebuilt/test.jsonl
   ```

Os arquivos existentes `data/train.jsonl`, `data/validation.jsonl`, `data/test.jsonl` e `training_dataset.jsonl` são dados legados; a divisão aleatória anterior por registro não evita vazamento de conceitos. Não apresente resultados desses arquivos como uma avaliação limpa em dados reservados.

Para avaliar os resultados já existentes com as métricas corrigidas:

```bash
python scripts/evaluate_metrics.py --results data/evaluation_results.json --output data/rebuilt/metrics.json
```

O avaliador calcula correspondência exata normalizada, F1 de sobreposição de tokens, similaridade cosseno TF-IDF **lexical** e uma estimativa heurística de Flesch para português. Essas métricas automáticas lexicais/de legibilidade não comprovam correção semântica; use revisão humana para conclusões de qualidade. O argumento opcional `--baseline caminho/para/baseline.json` compara um modelo base somente se ambos os arquivos tiverem os mesmos prompts (ou IDs) e referências.

As métricas corrigidas das 25 saídas existentes estão em [`docs/metrics_summary.json`](./docs/metrics_summary.json). Elas não formam um benchmark limpo de generalização, pois a divisão legada por registro contém conceitos sobrepostos.

A geração do dataset e a inferência podem ser feitas localmente pelo LM Studio. O ajuste fino QLoRA ainda requer um ambiente com GPU compatível. O ambiente Python deste workspace não possui PyTorch instalado nem o comando `nvidia-smi` detectado; portanto, o ajuste fino não pode ser executado aqui no momento.

## Relatório técnico

O relatório técnico em português está disponível em [`docs/Relatorio_Tecnico_JargaoZero_Llama3.pdf`](./docs/Relatorio_Tecnico_JargaoZero_Llama3.pdf).

## Objetivos de qualidade dos datasets

- **Formato válido:** Mantenha os registros `.jsonl` consistentes e válidos.
- **Sem duplicatas:** Evite entradas repetidas para o mesmo termo técnico.
- **Diversidade de conceitos:** Inclua tópicos como latência de rede, arquitetura de bancos de dados, cache multinível, microsserviços e segurança.

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo [LICENSE](./LICENSE).
