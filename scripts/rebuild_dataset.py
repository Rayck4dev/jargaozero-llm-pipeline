import argparse
import json
import random
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_dataset import RAW_TERMS
from lm_studio_client import LMStudioClient


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE_PATH = ROOT / "data" / "candidates" / "rebuilt_dataset.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "rebuilt"
TARGET_CONCEPTS = 66
MIN_CONCEPTS = 50
MAX_RECORDS = 200
LEVELS = ("Leigo", "Estudante", "Técnico")

SYSTEM_PROMPT = (
    "Você é um editor didático de tecnologia em português brasileiro. "
    "Use somente os fatos da definição fornecida, não invente detalhes, "
    "benefícios, riscos ou exemplos. Escreva respostas claras, naturais e "
    "conceitualmente corretas. Retorne somente um objeto JSON válido, sem "
    "Markdown, com as chaves technical_text e explanations. "
    "technical_text deve ser um parágrafo técnico original de 2 a 4 frases "
    "baseado estritamente na definição. explanations deve conter exatamente "
    "as chaves Leigo, Estudante e Técnico. Leigo usa palavras cotidianas e "
    "frases curtas; Estudante explica o conceito e seu funcionamento com "
    "contexto pedagógico; Técnico preserva terminologia precisa e relações "
    "entre componentes. As três respostas devem ser materialmente distintas, "
    "explicar o mesmo conteúdo e não acrescentar fatos ausentes da definição."
)


def normalize(text):
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"(?u)\b\w+\b", normalized))


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path}:{line_number}: JSON inválido: {error}"
                ) from error
    return rows


def write_jsonl_atomic(path, rows):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(destination)


def parse_generation(content, concept):
    content = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    if fenced:
        content = fenced.group(1)

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"O modelo não retornou JSON válido para {concept!r}: {error}"
        ) from error

    if not isinstance(payload, dict):
        raise ValueError(f"A resposta para {concept!r} precisa ser um objeto JSON.")
    technical_text = payload.get("technical_text")
    explanations = payload.get("explanations")
    if not isinstance(technical_text, str) or not technical_text.strip():
        raise ValueError(f"Texto técnico vazio ou inválido para {concept!r}.")
    if not isinstance(explanations, dict) or set(explanations) != set(LEVELS):
        raise ValueError(
            f"Esperadas exatamente as explicações {LEVELS} para {concept!r}."
        )

    normalized_outputs = []
    for level in LEVELS:
        answer = explanations[level]
        if not isinstance(answer, str) or len(answer.strip()) < 20:
            raise ValueError(f"Resposta {level!r} curta ou inválida para {concept!r}.")
        normalized_outputs.append(normalize(answer))

    if len(set(normalized_outputs)) != len(LEVELS):
        raise ValueError(
            f"As explicações de {concept!r} não são distintas entre os níveis."
        )
    return technical_text.strip(), {
        level: explanations[level].strip() for level in LEVELS
    }


def generate_concept(client, concept, definition, request_timeout):
    request_text = (
        f"Termo: {concept}\n"
        f"Definição de referência: {definition}\n\n"
        "Crie um texto técnico denso de 2 a 4 frases que preserve a definição "
        "sem acrescentar fatos. Depois, reescreva esse mesmo conteúdo para os "
        "três níveis solicitados. Não use o nome do nível dentro da resposta. "
        "Responda no formato JSON definido pelo sistema."
    )
    content = client.chat_completion(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request_text},
        ],
        temperature=0.3,
        max_tokens=650,
        timeout=request_timeout,
    )
    technical_text, explanations = parse_generation(content, concept)
    rows = []
    for level in LEVELS:
        rows.append(
            {
                "concept": concept,
                "source_definition": definition,
                "technical_text": technical_text,
                "level": level,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Explique o texto técnico em português brasileiro no "
                            f"nível {level}, preservando os fatos e o significado."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Nível: {level}. Texto: {technical_text}",
                    },
                    {"role": "assistant", "content": explanations[level]},
                ],
            }
        )
    return rows


def validate_candidate_rows(rows, min_concepts=MIN_CONCEPTS):
    if not rows:
        raise ValueError("O arquivo de candidatos está vazio.")

    groups = defaultdict(list)
    seen_prompts = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Registro {index} não é um objeto JSON.")
        concept = row.get("concept")
        level = row.get("level")
        technical_text = row.get("technical_text")
        messages = row.get("messages")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (concept, level, technical_text)
        ):
            raise ValueError(f"Registro {index} possui conceito ou texto vazio.")
        if level not in LEVELS:
            raise ValueError(f"Registro {index} usa nível desconhecido: {level!r}.")
        if (
            not isinstance(messages, list)
            or not all(isinstance(message, dict) for message in messages)
            or [message.get("role") for message in messages] != [
                "system",
                "user",
                "assistant",
            ]
        ):
            raise ValueError(f"Registro {index} não tem mensagens system/user/assistant.")
        if not all(
            isinstance(message.get("content"), str)
            and message["content"].strip()
            for message in messages
        ):
            raise ValueError(f"Registro {index} possui mensagem vazia.")
        if normalize(technical_text) != normalize(
            messages[1]["content"].split("Texto:", 1)[-1]
        ):
            raise ValueError(
                f"Registro {index} tem texto técnico diferente do conteúdo do prompt."
            )

        prompt_key = normalize(messages[1]["content"])
        if prompt_key in seen_prompts:
            raise ValueError(f"Prompt duplicado no registro {index}.")
        seen_prompts.add(prompt_key)
        groups[normalize(concept)].append(row)

    if len(groups) < min_concepts:
        raise ValueError(
            f"São necessários pelo menos {min_concepts} conceitos; encontrados {len(groups)}."
        )
    if len(rows) < 150 or len(rows) > MAX_RECORDS:
        raise ValueError(
            f"O dataset deve ter entre 150 e {MAX_RECORDS} pares; encontrados {len(rows)}."
        )

    for concept, concept_rows in groups.items():
        levels = [row["level"] for row in concept_rows]
        if len(levels) != len(LEVELS) or set(levels) != set(LEVELS):
            raise ValueError(
                f"O conceito {concept!r} precisa ter exatamente uma amostra por nível."
            )
        technical_texts = {normalize(row["technical_text"]) for row in concept_rows}
        if len(technical_texts) != 1:
            raise ValueError(
                f"O conceito {concept!r} deve usar o mesmo texto-fonte nos três níveis."
            )
        answers = {
            row["level"]: normalize(row["messages"][2]["content"])
            for row in concept_rows
        }
        if len(set(answers.values())) != len(LEVELS):
            raise ValueError(
                f"As respostas do conceito {concept!r} não variam entre os níveis."
            )
    return groups


def split_by_concept(groups, seed=3407):
    concepts = list(groups)
    random.Random(seed).shuffle(concepts)
    test_count = max(1, round(len(concepts) * 0.12))
    validation_count = max(1, round(len(concepts) * 0.12))
    test_concepts = set(concepts[:test_count])
    validation_concepts = set(
        concepts[test_count : test_count + validation_count]
    )
    train_concepts = set(concepts[test_count + validation_count :])

    if train_concepts & validation_concepts or train_concepts & test_concepts:
        raise AssertionError("Um conceito foi atribuído a mais de uma divisão.")
    if validation_concepts & test_concepts:
        raise AssertionError("Um conceito foi atribuído a mais de uma divisão.")

    return {
        "train": [
            row for concept in concepts if concept in train_concepts
            for row in groups[concept]
        ],
        "validation": [
            row for concept in concepts if concept in validation_concepts
            for row in groups[concept]
        ],
        "test": [
            row for concept in concepts if concept in test_concepts
            for row in groups[concept]
        ],
    }


def generate_candidates(candidate_path, model=None, seed=3407, request_timeout=900):
    client = LMStudioClient(model_id=model)
    model_id = client.model_id
    candidate_path = Path(candidate_path)
    existing_rows = read_jsonl(candidate_path) if candidate_path.exists() else []

    completed_groups = {}
    if existing_rows:
        grouped = defaultdict(list)
        for row in existing_rows:
            grouped[normalize(row.get("concept", ""))].append(row)
        for concept, rows in grouped.items():
            if len(rows) == len(LEVELS) and {
                row.get("level") for row in rows
            } == set(LEVELS):
                completed_groups[concept] = rows

    if len(RAW_TERMS) < TARGET_CONCEPTS:
        raise ValueError(
            f"A base possui {len(RAW_TERMS)} termos, mas {TARGET_CONCEPTS} "
            "conceitos são necessários."
        )
    selected_terms = random.Random(seed).sample(RAW_TERMS, TARGET_CONCEPTS)
    selected_concepts = {normalize(concept) for concept, _ in selected_terms}
    output_rows = [
        row
        for concept, rows in completed_groups.items()
        if concept in selected_concepts
        for row in rows
    ]

    for index, (concept, definition) in enumerate(selected_terms, start=1):
        normalized_concept = normalize(concept)
        if normalized_concept in completed_groups:
            print(f"[{index}/{TARGET_CONCEPTS}] Mantido do checkpoint: {concept}")
            continue

        print(f"[{index}/{TARGET_CONCEPTS}] Gerando: {concept}")
        generated_rows = generate_concept(
            client, concept, definition, request_timeout
        )
        output_rows.extend(generated_rows)
        write_jsonl_atomic(candidate_path, output_rows)

    validate_candidate_rows(output_rows)
    print(
        f"\nCandidatos gerados: {len(output_rows)} pares, "
        f"{len(output_rows) // len(LEVELS)} conceitos, modelo {model_id!r}."
    )
    print(f"Revise manualmente as respostas antes de separá-las: {candidate_path}")


def split_reviewed_candidates(candidate_path, output_dir, seed, overwrite):
    rows = read_jsonl(candidate_path)
    groups = validate_candidate_rows(rows)
    splits = split_by_concept(groups, seed)

    output_dir = Path(output_dir)
    destinations = {
        name: output_dir / f"{name}.jsonl" for name in splits
    }
    existing = [path for path in destinations.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "As divisões já existem e não serão sobrescritas: "
            + ", ".join(str(path) for path in existing)
            + ". Use --overwrite se quiser substituí-las."
        )

    split_concepts = {}
    for name, split_rows in splits.items():
        split_concepts[name] = {normalize(row["concept"]) for row in split_rows}
        write_jsonl_atomic(destinations[name], split_rows)

    if (
        split_concepts["train"] & split_concepts["validation"]
        or split_concepts["train"] & split_concepts["test"]
        or split_concepts["validation"] & split_concepts["test"]
    ):
        raise AssertionError("Foi detectado vazamento de conceito entre divisões.")

    print("\nDivisões concluídas por conceito:")
    for name, split_rows in splits.items():
        print(
            f"  {name}: {len(split_rows)} pares, "
            f"{len(split_concepts[name])} conceitos -> {destinations[name]}"
        )
    print("Nenhum conceito aparece em mais de uma divisão.")


def require_review_confirmation(confirmed):
    if not confirmed:
        raise ValueError(
            "Revise manualmente o JSONL e informe --confirm-reviewed "
            "para criar as divisões."
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Gera candidatos multinível pelo LM Studio e cria divisões "
            "sem vazamento após revisão humana."
        )
    )
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--generate",
        action="store_true",
        help="Gera candidatos com um modelo carregado no LM Studio.",
    )
    actions.add_argument(
        "--split-reviewed",
        action="store_true",
        help="Divide os candidatos revisados por conceito.",
    )
    parser.add_argument(
        "--candidate-path",
        type=Path,
        default=DEFAULT_CANDIDATE_PATH,
        help=f"Arquivo de candidatos (padrão: {DEFAULT_CANDIDATE_PATH}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Diretório das divisões (padrão: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument("--model", help="ID de modelo opcional da API local.")
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=900,
        help="Tempo limite em segundos por conceito durante a geração (padrão: 900).",
    )
    parser.add_argument(
        "--confirm-reviewed",
        action="store_true",
        help="Confirma que os candidatos foram revisados por uma pessoa.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Permite substituir divisões em data/rebuilt.",
    )
    args = parser.parse_args()

    if args.generate:
        if args.request_timeout <= 0:
            parser.error("--request-timeout precisa ser maior que zero.")
        generate_candidates(
            args.candidate_path,
            args.model,
            args.seed,
            args.request_timeout,
        )
    else:
        try:
            require_review_confirmation(args.confirm_reviewed)
        except ValueError as error:
            parser.error(str(error))
        split_reviewed_candidates(
            args.candidate_path,
            args.output_dir,
            args.seed,
            args.overwrite,
        )


if __name__ == "__main__":
    main()
