import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from statistics import mean


def cosine_tfidf_scores(documents, pairs):
    """Calcula similaridade cosseno lexical com vetores TF-IDF."""
    tokenized = [re.findall(r"(?u)\b\w\w+\b", doc.casefold()) for doc in documents]
    document_frequency = Counter(
        token for tokens in tokenized for token in set(tokens)
    )
    idf = {
        token: math.log((1 + len(tokenized)) / (1 + frequency)) + 1
        for token, frequency in document_frequency.items()
    }

    vectors = []
    for tokens in tokenized:
        counts = Counter(tokens)
        vector = {token: count * idf[token] for token, count in counts.items()}
        norm = math.sqrt(sum(weight * weight for weight in vector.values()))
        vectors.append(
            {token: weight / norm for token, weight in vector.items()} if norm else {}
        )

    return [
        sum(
            vectors[left].get(token, 0.0) * weight
            for token, weight in vectors[right].items()
        )
        for left, right in pairs
    ]


def count_syllables_pt(word):
    """Conta sílabas de forma aproximada para a variante portuguesa do Flesch."""
    word = re.sub(r"[^a-záéíóúâêôãõç]", "", word.casefold())
    if not word:
        return 1

    vowels = "aeiouáéíóúâêôãõ"
    count = 0
    previous_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            count += 1
        previous_was_vowel = is_vowel
    return max(1, count)


def flesch_reading_ease_pt(text):
    """Calcula uma estimativa do índice Flesch adaptado para português."""
    sentences = [sentence for sentence in re.split(r"[.!?]+", text) if sentence.strip()]
    words = re.findall(r"\b\w+\b", text.casefold())

    sentence_count = max(1, len(sentences))
    word_count = max(1, len(words))
    syllable_count = sum(count_syllables_pt(word) for word in words)
    score = (
        248.835
        - 1.015 * (word_count / sentence_count)
        - 84.6 * (syllable_count / word_count)
    )
    return round(score, 2)


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.findall(r"(?u)\b\w+\b", text))


def _first_text(item, keys):
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _items_from_file(path):
    with Path(path).open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    raise ValueError(f"{path}: esperado um array JSON ou um objeto com a chave 'results'.")


def load_evaluation_pairs(path, output_keys=None):
    output_keys = output_keys or (
        "model_output",
        "generated",
        "modelo_gerado",
        "output",
    )
    pairs = []
    skipped = []

    for index, item in enumerate(_items_from_file(path), start=1):
        if not isinstance(item, dict):
            skipped.append(index)
            continue

        reference = _first_text(
            item, ("reference", "esperado", "ground_truth", "target")
        )
        generated = _first_text(item, output_keys)
        prompt = _first_text(item, ("prompt", "input", "original", "texto"))

        if not reference or not generated:
            skipped.append(index)
            continue

        pairs.append(
            {
                "id": str(item.get("id", index)),
                "prompt": prompt,
                "reference": reference,
                "generated": generated,
            }
        )

    if not pairs:
        raise ValueError(
            f"{path}: nenhum par de referência/saída válido foi encontrado. "
            f"Campos de saída aceitos: {', '.join(output_keys)}."
        )
    return pairs, skipped


def _token_overlap_scores(reference, generated):
    reference_tokens = Counter(re.findall(r"(?u)\b\w+\b", reference.casefold()))
    generated_tokens = Counter(re.findall(r"(?u)\b\w+\b", generated.casefold()))
    overlap = sum((reference_tokens & generated_tokens).values())
    precision = overlap / sum(generated_tokens.values()) if generated_tokens else 0.0
    recall = overlap / sum(reference_tokens.values()) if reference_tokens else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return precision, recall, f1


def evaluate_pairs(pairs):
    references = [pair["reference"] for pair in pairs]
    generated = [pair["generated"] for pair in pairs]
    count = len(pairs)

    cosine_scores = cosine_tfidf_scores(
        references + generated,
        [(index, count + index) for index in range(count)],
    )
    overlap_scores = [
        _token_overlap_scores(reference, output)
        for reference, output in zip(references, generated)
    ]
    exact_matches = [
        normalize_text(reference) == normalize_text(output)
        for reference, output in zip(references, generated)
    ]
    reference_readability = [flesch_reading_ease_pt(text) for text in references]
    output_readability = [flesch_reading_ease_pt(text) for text in generated]

    total_reference_tokens = sum(
        len(re.findall(r"(?u)\b\w+\b", text.casefold())) for text in references
    )
    total_generated_tokens = sum(
        len(re.findall(r"(?u)\b\w+\b", text.casefold())) for text in generated
    )
    total_overlap = sum(
        sum(
            (
                Counter(re.findall(r"(?u)\b\w+\b", reference.casefold()))
                & Counter(re.findall(r"(?u)\b\w+\b", output.casefold()))
            ).values()
        )
        for reference, output in zip(references, generated)
    )
    micro_precision = (
        total_overlap / total_generated_tokens if total_generated_tokens else 0.0
    )
    micro_recall = total_overlap / total_reference_tokens if total_reference_tokens else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if micro_precision + micro_recall
        else 0.0
    )

    return {
        "samples": count,
        "exact_match_accuracy_percent": round(mean(exact_matches) * 100, 2),
        "tfidf_cosine_lexical_similarity_percent": round(mean(cosine_scores) * 100, 2),
        "token_overlap": {
            "macro_precision_percent": round(
                mean(score[0] for score in overlap_scores) * 100, 2
            ),
            "macro_recall_percent": round(
                mean(score[1] for score in overlap_scores) * 100, 2
            ),
            "macro_f1_percent": round(
                mean(score[2] for score in overlap_scores) * 100, 2
            ),
            "micro_f1_percent": round(micro_f1 * 100, 2),
        },
        "flesch_pt_estimated": {
            "reference_mean": round(mean(reference_readability), 2),
            "generated_mean": round(mean(output_readability), 2),
            "mean_delta": round(
                mean(output_readability) - mean(reference_readability), 2
            ),
            "method": "Estimated Portuguese Flesch formula; syllables are heuristic.",
        },
        "metric_notes": [
            "TF-IDF cosine measures lexical overlap, not semantic equivalence.",
            "Token-overlap F1 is a lexical metric, not a semantic metric.",
            "Exact match is normalized for case, punctuation, and whitespace.",
            "Flesch is an estimated readability indicator; higher scores are not automatically better for every audience.",
        ],
    }


def _evaluation_key(pair):
    return pair["prompt"] or pair["id"]


def compare_baseline(fine_tuned_pairs, baseline_pairs):
    baseline_by_key = {}
    for pair in baseline_pairs:
        key = _evaluation_key(pair)
        if key in baseline_by_key:
            raise ValueError(
                "A avaliação base contém chaves duplicadas; use prompts ou IDs únicos."
            )
        baseline_by_key[key] = pair

    fine_tuned_by_key = {}
    for pair in fine_tuned_pairs:
        key = _evaluation_key(pair)
        if key in fine_tuned_by_key:
            raise ValueError(
                "A avaliação fine-tuned contém chaves duplicadas; use prompts ou IDs únicos."
            )
        fine_tuned_by_key[key] = pair
    if fine_tuned_by_key.keys() != baseline_by_key.keys():
        missing_baseline = sorted(fine_tuned_by_key.keys() - baseline_by_key.keys())
        missing_fine_tuned = sorted(baseline_by_key.keys() - fine_tuned_by_key.keys())
        raise ValueError(
            "Modelo base e fine-tuned precisam usar exatamente as mesmas amostras. "
            f"Ausentes na base: {missing_baseline[:5]}; "
            f"ausentes no fine-tuned: {missing_fine_tuned[:5]}."
        )

    aligned_baseline = []
    for key, fine_tuned_pair in fine_tuned_by_key.items():
        baseline_pair = baseline_by_key[key]
        if normalize_text(fine_tuned_pair["reference"]) != normalize_text(
            baseline_pair["reference"]
        ):
            raise ValueError(
                f"Referências diferentes entre os modelos para a amostra {key!r}."
            )
        aligned_baseline.append(
            {
                **fine_tuned_pair,
                "generated": baseline_pair["generated"],
            }
        )

    return evaluate_pairs(aligned_baseline)


def print_metrics(title, metrics):
    print(f"\n{title}")
    print("=" * len(title))
    print(f"Amostras avaliadas                 : {metrics['samples']}")
    print(
        "Exact Match (acurácia exata)       : "
        f"{metrics['exact_match_accuracy_percent']:.2f}%"
    )
    print(
        "Cosine TF-IDF (similaridade lexical): "
        f"{metrics['tfidf_cosine_lexical_similarity_percent']:.2f}%"
    )
    overlap = metrics["token_overlap"]
    print(f"Token F1 macro                     : {overlap['macro_f1_percent']:.2f}%")
    print(f"Token F1 micro                     : {overlap['micro_f1_percent']:.2f}%")
    flesch = metrics["flesch_pt_estimated"]
    print(f"Flesch PT estimado (referência)     : {flesch['reference_mean']:.2f}")
    print(f"Flesch PT estimado (gerado)         : {flesch['generated_mean']:.2f}")
    print(f"Variação média de Flesch            : {flesch['mean_delta']:+.2f}")
    for note in metrics["metric_notes"]:
        print(f"Nota: {note}")


def evaluate_jargaozero(
    results_path="data/evaluation_results.json", baseline_path=None, output_path=None
):
    fine_tuned_pairs, skipped = load_evaluation_pairs(results_path)
    fine_tuned_metrics = evaluate_pairs(fine_tuned_pairs)
    report = {
        "fine_tuned": {
            "source": str(results_path),
            "metrics": fine_tuned_metrics,
        }
    }

    print_metrics("AVALIAÇÃO DO MODELO FINE-TUNED", fine_tuned_metrics)
    if skipped:
        print(f"Aviso: {len(skipped)} registros foram ignorados por estarem incompletos.")

    if baseline_path:
        baseline_pairs, baseline_skipped = load_evaluation_pairs(baseline_path)
        baseline_metrics = compare_baseline(fine_tuned_pairs, baseline_pairs)
        report["base_model"] = {
            "source": str(baseline_path),
            "metrics": baseline_metrics,
        }
        report["comparison"] = {
            key: round(
                fine_tuned_metrics[key] - baseline_metrics[key],
                2,
            )
            for key in (
                "exact_match_accuracy_percent",
                "tfidf_cosine_lexical_similarity_percent",
            )
        }
        print_metrics("AVALIAÇÃO DO MODELO BASE", baseline_metrics)
        print("\nDiferença fine-tuned menos base (pontos percentuais)")
        print(json.dumps(report["comparison"], ensure_ascii=False, indent=2))
        if baseline_skipped:
            print(
                f"Aviso: {len(baseline_skipped)} registros do baseline foram ignorados."
            )

    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write("\n")
        print(f"\nRelatório salvo em: {destination}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Calcula métricas lexicais e legibilidade para respostas do JargãoZero."
    )
    parser.add_argument(
        "--results",
        default="data/evaluation_results.json",
        help="JSON com as referências e as saídas do modelo fine-tuned.",
    )
    parser.add_argument(
        "--baseline",
        help="JSON opcional do modelo base com os mesmos IDs/prompts de teste.",
    )
    parser.add_argument(
        "--output",
        help="Caminho opcional para salvar os resultados das métricas em JSON.",
    )
    args = parser.parse_args()
    evaluate_jargaozero(args.results, args.baseline, args.output)


if __name__ == "__main__":
    main()
