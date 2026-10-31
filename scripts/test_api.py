import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lm_studio_client import LMStudioClient


client = LMStudioClient()


def traduzir_jargao_local(texto_tecnico, nivel="Leigo"):
    return client.chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "Explique o texto técnico em português brasileiro no nível "
                    "solicitado, preservando o significado e sem inventar fatos."
                ),
            },
            {
                "role": "user",
                "content": f"Nível: {nivel}. Texto: {texto_tecnico}",
            },
        ],
        max_tokens=200,
    )


if __name__ == "__main__":
    termo_teste = (
        "O padrão Cache-Aside verifica primeiro o cache e consulta o banco "
        "de dados quando o valor solicitado não está armazenado."
    )
    print(f"Modelo local: {client.model_id}")
    print("A enviar requisição para o LM Studio...")
    traducao = traduzir_jargao_local(termo_teste)
    print("\nResultado da tradução:\n", traducao)
