import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_metrics
import lm_studio_client
import rebuild_dataset
import split_dataset
import validate_dataset


def candidate_rows(concept_count=50):
    rows = []
    levels = rebuild_dataset.LEVELS
    for index in range(concept_count):
        concept = f"Conceito {index}"
        technical_text = f"O conceito {index} organiza os dados em componentes relacionados."
        for level_index, level in enumerate(levels):
            answer = (
                f"Explicação {level_index} do conceito {index}, "
                "com informações adaptadas ao nível escolhido."
            )
            rows.append(
                {
                    "concept": concept,
                    "source_definition": f"Definição {index}.",
                    "technical_text": technical_text,
                    "level": level,
                    "messages": [
                        {"role": "system", "content": f"Explique como {level}."},
                        {
                            "role": "user",
                            "content": f"Nível: {level}. Texto: {technical_text}",
                        },
                        {"role": "assistant", "content": answer},
                    ],
                }
            )
    return rows


class EvaluateMetricsTests(unittest.TestCase):
    def test_exact_match_normalizes_case_and_punctuation(self):
        metrics = evaluate_metrics.evaluate_pairs(
            [
                {
                    "reference": "Banco de dados!",
                    "generated": "banco de dados",
                    "prompt": "Exemplo",
                    "id": "1",
                }
            ]
        )
        self.assertEqual(metrics["exact_match_accuracy_percent"], 100)

    def test_lexical_similarity_distinguishes_unrelated_text(self):
        scores = evaluate_metrics.cosine_tfidf_scores(
            ["latência de rede", "banco de dados"],
            [(0, 0), (0, 1)],
        )
        self.assertAlmostEqual(scores[0], 1)
        self.assertLess(scores[1], scores[0])

    def test_loads_existing_model_output_field(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "prompt": "Explique latência",
                            "reference": "Atraso na rede.",
                            "model_output": "Atraso na rede!",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            pairs, skipped = evaluate_metrics.load_evaluation_pairs(path)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(skipped, [])


class RebuildDatasetTests(unittest.TestCase):
    def test_generation_builds_one_record_per_level(self):
        explanations = {
            "Leigo": "Resposta simples e clara para qualquer pessoa.",
            "Estudante": "Resposta educativa que explica o conceito com contexto.",
            "Técnico": "Resposta técnica que mantém a terminologia precisa.",
        }
        client = Mock()
        client.chat_completion.return_value = json.dumps(
            {
                "technical_text": "Um conceito técnico descrito sem fatos adicionais.",
                "explanations": explanations,
            },
            ensure_ascii=False,
        )

        rows = rebuild_dataset.generate_concept(
            client, "Termo", "Definição de referência.", request_timeout=45
        )

        self.assertEqual([row["level"] for row in rows], list(rebuild_dataset.LEVELS))
        self.assertEqual(
            [row["messages"][1]["content"] for row in rows],
            [
                "Nível: Leigo. Texto: Um conceito técnico descrito sem fatos adicionais.",
                "Nível: Estudante. Texto: Um conceito técnico descrito sem fatos adicionais.",
                "Nível: Técnico. Texto: Um conceito técnico descrito sem fatos adicionais.",
            ],
        )
        client.chat_completion.assert_called_once()

    def test_candidate_rows_have_distinct_levels_and_no_concept_leakage(self):
        groups = rebuild_dataset.validate_candidate_rows(candidate_rows())
        splits = rebuild_dataset.split_by_concept(groups, seed=7)
        concepts = {
            name: {row["concept"] for row in rows}
            for name, rows in splits.items()
        }
        self.assertEqual(sum(len(rows) for rows in splits.values()), 150)
        self.assertFalse(concepts["train"] & concepts["validation"])
        self.assertFalse(concepts["train"] & concepts["test"])
        self.assertFalse(concepts["validation"] & concepts["test"])

    def test_candidate_validation_rejects_missing_level(self):
        rows = candidate_rows(51)
        with self.assertRaisesRegex(ValueError, "exatamente uma amostra"):
            rebuild_dataset.validate_candidate_rows(rows[:-1])

    def test_split_requires_explicit_review_confirmation(self):
        with self.assertRaisesRegex(ValueError, "--confirm-reviewed"):
            rebuild_dataset.require_review_confirmation(False)
        rebuild_dataset.require_review_confirmation(True)


class ExistingSplitTests(unittest.TestCase):
    def test_legacy_examples_are_grouped_by_quoted_concept(self):
        rows = []
        for index in range(12):
            for variation in range(2):
                rows.append(
                    {
                        "messages": [
                            {"role": "system", "content": "System"},
                            {
                                "role": "user",
                                "content": (
                                    f"Nível: Leigo. Texto: Explique o termo técnico "
                                    f"'{index}'? (Ref. {variation})"
                                ),
                            },
                            {"role": "assistant", "content": f"Resposta {index}."},
                        ]
                    }
                )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            groups = split_dataset.load_grouped_records(path)
            splits, assigned = split_dataset.split_groups(groups, seed=3)
        self.assertEqual(len(groups), 12)
        self.assertEqual(sum(len(part) for part in splits.values()), len(rows))
        self.assertFalse(set(assigned["train"]) & set(assigned["validation"]))
        self.assertFalse(set(assigned["train"]) & set(assigned["test"]))
        self.assertFalse(set(assigned["validation"]) & set(assigned["test"]))


class ValidateDatasetTests(unittest.TestCase):
    def test_candidate_format_passes_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "split.jsonl"
            path.write_text(
                "\n".join(json.dumps(row) for row in candidate_rows()) + "\n",
                encoding="utf-8",
            )
            report = validate_dataset.validate_dataset(path)
        self.assertTrue(report["valid"])
        self.assertEqual(report["records"], 150)

    def test_incomplete_annotated_concepts_fail_validation(self):
        rows = candidate_rows()
        rows.pop()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "split.jsonl"
            path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            report = validate_dataset.validate_dataset(path)
        self.assertFalse(report["valid"])
        self.assertTrue(report["incomplete_concepts"])


class LMStudioClientTests(unittest.TestCase):
    def test_discovers_loaded_model_and_parses_completion(self):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": " Explicação local. "}}]
        }
        session = Mock()
        session.get.return_value.json.return_value = {
            "data": [{"id": "local-model"}]
        }
        session.post.return_value = response
        with patch.dict("os.environ", {"JARGAOZERO_LLM_MODEL": ""}):
            client = lm_studio_client.LMStudioClient(
                base_url="http://localhost:1235/v1"
            )
        client._session = session

        answer = client.chat_completion(
            [{"role": "user", "content": "Explique"}], max_tokens=50
        )

        self.assertEqual(client.model_id, "local-model")
        self.assertEqual(answer, "Explicação local.")
        session.post.assert_called_once()

    def test_empty_model_list_fails_explicitly(self):
        session = Mock()
        session.get.return_value.json.return_value = {"data": []}
        with patch.dict("os.environ", {"JARGAOZERO_LLM_MODEL": ""}):
            client = lm_studio_client.LMStudioClient()
        client._session = session
        with self.assertRaisesRegex(RuntimeError, "Nenhum modelo"):
            _ = client.model_id


if __name__ == "__main__":
    unittest.main()
