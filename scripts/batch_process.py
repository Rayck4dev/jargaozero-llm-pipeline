import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lm_studio_client import LMStudioClient

CLIENT = LMStudioClient()

PROMPT_SISTEMA = (
    "Atue exclusivamente como o tradutor do projeto JargãoZero. Siga"
    " exatamente o formato de resposta solicitado, sem incluir tags,"
    " metadados ou explicações adicionais. Preserve os fatos e adapte"
    " a linguagem ao nível solicitado."
)

EXEMPLO_USER = (
    "Nível: Leigo. Texto: A latência de rede é o atraso na transmissão "
    "de dados entre dispositivos."
)
EXEMPLO_ASSISTANT = (
    "É o tempo que os dados levam para chegar de um dispositivo a outro."
)

def traduzir_amostra(texto_tecnico, nivel="Leigo"):
    return CLIENT.chat_completion(
        [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": EXEMPLO_USER},
            {"role": "assistant", "content": EXEMPLO_ASSISTANT},
            {
                "role": "user",
                "content": (
                    f"Nível: {nivel}. Texto: {texto_tecnico}\nSaída:"
                ),
            },
        ],
        temperature=0.3,
        max_tokens=250,
    )

def processar_dataset(
    ficheiro_entrada="train.jsonl", ficheiro_saida="results_jargaozero.jsonl"
):
    print(f"A iniciar o processamento do ficheiro: {ficheiro_entrada}")

    total_processados = 0

    with open(ficheiro_entrada, "r", encoding="utf-8") as f_in, open(
        ficheiro_saida, "w", encoding="utf-8"
    ) as f_out:

        for linha in f_in:
            linha = linha.strip()
            if not linha:
                continue

            dados = json.loads(linha)
            
            if "messages" in dados:
                user_msg = next((m["content"] for m in dados["messages"] if m["role"] == "user"), "")
                
                nivel = "Leigo"
                texto_tecnico = user_msg
                
                if "Nível:" in user_msg and "Texto:" in user_msg:
                    nivel_parte, texto_parte = user_msg.split("Texto:", 1)
                    nivel = nivel_parte.split("Nível:", 1)[1].strip().rstrip(".")
                    texto_tecnico = texto_parte.strip()
            else:
                texto_tecnico = dados.get("texto", dados.get("input", dados.get("original", "")))
                nivel = dados.get("nivel", "Leigo")

            print(f"[{total_processados + 1}] A traduzir ({nivel}): {texto_tecnico[:40]}...")

            traducao = traduzir_amostra(texto_tecnico, nivel)

            resultado_obj = {
                "original": texto_tecnico,
                "nivel": nivel,
                "traducao": traducao,
            }

            f_out.write(json.dumps(resultado_obj, ensure_ascii=False) + "\n")
            total_processados += 1

            time.sleep(0.3)

    print(
        f"\nProcessamento concluído! {total_processados} amostras traduzidas e"
        f" guardadas em '{ficheiro_saida}'."
    )

if __name__ == "__main__":
    processar_dataset("train.jsonl", "results_jargaozero.jsonl")