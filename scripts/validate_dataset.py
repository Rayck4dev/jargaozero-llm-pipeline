import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"(?u)\b\w+\b", text))


def validate_dataset(filepath):
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset não encontrado: {path}")

    records = []
    malformed_lines = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                malformed_lines.append((line_number, str(error)))
                continue
            records.append((line_number, record))

    invalid_structure = []
    empty_outputs = []
    prompts = Counter()
    answers = Counter()
    concepts_by_level = {}
    for line_number, record in records:
        if not isinstance(record, dict):
            invalid_structure.append(line_number)
            continue
        messages = record.get("messages")
        if (
            not isinstance(messages, list)
            or len(messages) != 3
            or not all(isinstance(message, dict) for message in messages)
            or [message.get("role") for message in messages]
            != ["system", "user", "assistant"]
        ):
            invalid_structure.append(line_number)
            continue

        contents = [message.get("content") for message in messages]
        if not all(isinstance(content, str) for content in contents):
            invalid_structure.append(line_number)
            continue
        if not all(content.strip() for content in contents):
            empty_outputs.append(line_number)

        prompts[normalize(contents[1])] += 1
        answers[normalize(contents[2])] += 1

        concept = record.get("concept")
        level = record.get("level")
        if isinstance(concept, str) and isinstance(level, str):
            concepts_by_level.setdefault(normalize(concept), set()).add(level)

    duplicate_prompts = sum(count - 1 for count in prompts.values() if count > 1)
    duplicate_answers = sum(count - 1 for count in answers.values() if count > 1)
    incomplete_concepts = {
        concept: sorted(levels)
        for concept, levels in concepts_by_level.items()
        if levels != {"Leigo", "Estudante", "Técnico"}
    }

    print("Relatório de validação do dataset")
    print(f"Arquivo: {path}")
    print(f"Registros lidos: {len(records)}")
    print(f"Linhas JSON malformadas: {len(malformed_lines)}")
    print(f"Registros com estrutura inválida: {len(invalid_structure)}")
    print(f"Registros com conteúdo vazio: {len(empty_outputs)}")
    print(f"Prompts duplicados além da primeira ocorrência: {duplicate_prompts}")
    print(f"Respostas duplicadas além da primeira ocorrência: {duplicate_answers}")
    if concepts_by_level:
        print(f"Conceitos anotados: {len(concepts_by_level)}")
        print(f"Conceitos sem os três níveis: {len(incomplete_concepts)}")

    for line_number, error in malformed_lines[:10]:
        print(f"  JSON inválido na linha {line_number}: {error}")
    if invalid_structure:
        print(f"  Estrutura inválida nas linhas: {invalid_structure[:10]}")
    if empty_outputs:
        print(f"  Conteúdo vazio nas linhas: {empty_outputs[:10]}")
    if incomplete_concepts:
        print(f"  Níveis incompletos (primeiros 10): {dict(list(incomplete_concepts.items())[:10])}")

    return {
        "valid": not malformed_lines
        and not invalid_structure
        and not empty_outputs
        and duplicate_prompts == 0
        and not incomplete_concepts,
        "records": len(records),
        "malformed_lines": len(malformed_lines),
        "invalid_structure": len(invalid_structure),
        "empty_outputs": len(empty_outputs),
        "duplicate_prompts": duplicate_prompts,
        "duplicate_answers": duplicate_answers,
        "incomplete_concepts": incomplete_concepts,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Valida estrutura e duplicatas de um dataset JSONL."
    )
    parser.add_argument("filepath", help="Caminho do dataset JSONL.")
    args = parser.parse_args()
    report = validate_dataset(args.filepath)
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
