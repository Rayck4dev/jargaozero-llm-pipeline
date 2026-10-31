import json
import time
import requests

LOCAL_API_URL = "http://localhost:1235/v1/chat/completions"
MODELO_NOME = "dolphin-2.9-llama3-8b" 

PROMPT_SISTEMA = (
    "Atue exclusivamente como o tradutor do projeto JargãoZero. Siga"
    " exatamente o formato de resposta solicitado, sem incluir tags,"
    " metadados ou explicações adicionais."
)

EXEMPLO_FEW_SHOT = {
    "role": "user",
    "content": (
        "Entrada: Nível: Leigo. Texto: A latência de rede refere-se ao atraso"
        " temporal na propagação de pacotes de dados através de um meio de"
        " comunicação.\nSaída: É o tempo de espera ou o atraso que acontece"
        " desde o momento em que clica em algo na internet até a página"
        " realmente carregar no ecrã."
    ),
}

def traduzir_amostra(texto_tecnico, nivel="Leigo"):
    payload = {
        "model": MODELO_NOME,
        "messages": [
            {"role": "system", "content": PROMPT_SISTEMA},
            EXEMPLO_FEW_SHOT,
            {
                "role": "user",
                "content": (
                    f"Entrada: Nível: {nivel}. Texto: {texto_tecnico}\nSaída:"
                ),
            },
        ],
        "temperature": 0.3,
        "max_tokens": 250,
    }

    try:
        response = requests.post(LOCAL_API_URL, json=payload)
        response.raise_for_status()
        resultado = response.json()
        return resultado["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERRO: {e}"

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
                    try:
                        partes = user_msg.split("Texto:")
                        nivel_parte = partes[0].replace("Nível:", "").strip().replace(".", "")
                        nivel = nivel_parte if nivel_parte else "Leigo"
                        texto_tecnico = partes[1].strip()
                    except Exception:
                        pass
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