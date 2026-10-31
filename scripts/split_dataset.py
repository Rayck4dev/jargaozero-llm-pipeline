import argparse
import json
import random
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"(?u)\b\w+\b", text))


def infer_concept(record, line_number):
    concept = record.get("concept")
    if isinstance(concept, str) and concept.strip():
        return concept.strip()

    messages = record.get("messages")
    if not isinstance(messages, list):
        raise ValueError(f"Linha {line_number}: campo 'messages' ausente.")
    user_messages = [
        message.get("content", "")
        for message in messages
        if isinstance(message, dict) and message.get("role") == "user"
    ]
    if len(user_messages) != 1 or not isinstance(user_messages[0], str):
        raise ValueError(
            f"Linha {line_number}: não foi possível identificar uma mensagem do usuário."
        )

    user_content = user_messages[0]
    quoted = re.search(r"""['‘“"]([^'’”"]+)['’”"]""", user_content)
    if quoted:
        return quoted.group(1).strip()

    text = re.sub(r"^\s*Nível:\s*[^.]+\.\s*Texto:\s*", "", user_content, flags=re.I)
    text = re.sub(r"\s*\(Ref\.\s*\d+\)\s*$", "", text, flags=re.I).strip()
    text = re.sub(
        r"\s+(?:refere-se a quê|refere-se a que|significa exatamente|no desenvolvimento)\s*\??$",
        "",
        text,
        flags=re.I,
    )
    if not text or len(text) > 160:
        raise ValueError(
            f"Linha {line_number}: conceito não identificável; inclua campo 'concept' "
            "ou coloque o termo entre aspas no prompt."
        )
    return text.strip(" ?.!:")


def load_grouped_records(input_path):
    groups = defaultdict(list)
    with Path(input_path).open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Linha {line_number}: JSON inválido: {error}"
                ) from error
            if not isinstance(record, dict):
                raise ValueError(f"Linha {line_number}: esperado objeto JSON.")

            messages = record.get("messages")
            if (
                not isinstance(messages, list)
                or [message.get("role") for message in messages if isinstance(message, dict)]
                != ["system", "user", "assistant"]
                or len(messages) != 3
                or not all(
                    isinstance(message.get("content"), str)
                    and message["content"].strip()
                    for message in messages
                    if isinstance(message, dict)
                )
            ):
                raise ValueError(
                    f"Linha {line_number}: esperado trio válido system/user/assistant."
                )

            concept = infer_concept(record, line_number)
            groups[normalize(concept)].append(record)

    if len(groups) < 3:
        raise ValueError(
            f"São necessários pelo menos 3 conceitos para dividir; encontrados {len(groups)}."
        )
    return groups


def split_groups(groups, train_ratio=0.8, val_ratio=0.1, seed=3407):
    if train_ratio <= 0 or val_ratio <= 0 or train_ratio + val_ratio >= 1:
        raise ValueError(
            "As proporções precisam ser positivas e a soma de treino/validação menor que 1."
        )

    concepts = list(groups)
    random.Random(seed).shuffle(concepts)
    train_end = max(1, int(len(concepts) * train_ratio))
    validation_count = max(1, int(len(concepts) * val_ratio))
    if train_end + validation_count >= len(concepts):
        train_end = len(concepts) - validation_count - 1
    assignments = {
        "train": concepts[:train_end],
        "validation": concepts[train_end : train_end + validation_count],
        "test": concepts[train_end + validation_count :],
    }

    if not all(assignments.values()):
        raise ValueError("A divisão resultou em uma partição vazia.")
    return {
        name: [record for concept in assigned for record in groups[concept]]
        for name, assigned in assignments.items()
    }, assignments


def save_splits(splits, output_dir, overwrite=False):
    output_dir = Path(output_dir)
    destinations = {
        name: output_dir / f"{name}.jsonl" for name in splits
    }
    existing = [path for path in destinations.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Os arquivos não serão sobrescritos sem --overwrite: "
            + ", ".join(str(path) for path in existing)
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, records in splits.items():
        temporary = destinations[name].with_suffix(".jsonl.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
        temporary.replace(destinations[name])
    return destinations


def validar_e_dividir_dataset(
    input_file,
    train_ratio=0.8,
    val_ratio=0.1,
    seed=3407,
    output_dir="data/split",
    overwrite=False,
):
    groups = load_grouped_records(input_file)
    splits, assignments = split_groups(groups, train_ratio, val_ratio, seed)
    destinations = save_splits(splits, output_dir, overwrite)

    concept_sets = {name: set(values) for name, values in assignments.items()}
    if (
        concept_sets["train"] & concept_sets["validation"]
        or concept_sets["train"] & concept_sets["test"]
        or concept_sets["validation"] & concept_sets["test"]
    ):
        raise AssertionError("Vazamento de conceito entre as partições.")

    print(f"Conceitos: {len(groups)} | Registros: {sum(map(len, splits.values()))}")
    for name, records in splits.items():
        print(
            f"{name}: {len(records)} registros, "
            f"{len(assignments[name])} conceitos -> {destinations[name]}"
        )
    print("Divisão agrupada por conceito; nenhum conceito aparece em mais de uma parte.")


def main():
    parser = argparse.ArgumentParser(
        description="Divide um JSONL por conceito para evitar vazamento entre partições."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="training_dataset.jsonl",
        help="Dataset de entrada em JSONL (padrão: training_dataset.jsonl).",
    )
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--output-dir", default="data/split")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Permite substituir arquivos existentes no diretório de saída.",
    )
    args = parser.parse_args()
    validar_e_dividir_dataset(
        args.input,
        args.train_ratio,
        args.validation_ratio,
        args.seed,
        args.output_dir,
        args.overwrite,
    )


if __name__ == "__main__":
    main()
