import json
import requests

LOCAL_API_URL = "http://localhost:1235/v1/chat/completions"


def traduzir_jargao_local(texto_tecnico, nivel="Leigo"):
  prompt_sistema = (
      "Atue exclusivamente como o tradutor do projeto JargãoZero. Siga"
      " exatamente o formato de resposta solicitado, sem incluir tags,"
      " metadados ou explicações adicionais."
  )

  payload = {
      "model": "dolphin-2.9-llama3-8b",
      "messages": [
          {"role": "system", "content": prompt_sistema},
          {
              "role": "user",
              "content": (
                  f"Entrada: Nível: Leigo. Texto: A latência de rede refere-se"
                  " ao atraso temporal na propagação de pacotes de dados através"
                  " de um meio de comunicação.\nSaída: É o tempo de espera ou o"
                  " atraso que acontece desde o momento em que clica em algo na"
                  " internet até a página realmente carregar no ecrã."
              ),
          },
          {
              "role": "user",
              "content": (
                  f"Entrada: Nível: {nivel}. Texto: {texto_tecnico}\nSaída:"
              ),
          },
      ],
      "temperature": 0.3,
      "max_tokens": 200,
  }

  try:
    response = requests.post(LOCAL_API_URL, json=payload)
    response.raise_for_status()
    resultado = response.json()
    return resultado["choices"][0]["message"]["content"].strip()
  except Exception as e:
    return f"Erro na conexão com a API local: {e}"


if __name__ == "__main__":
  termo_teste = "O padrão de arquitetura Cache-Aside armazena dados em cache de forma manual, onde a aplicação verifica o cache primeiro antes de consultar o banco de dados relacional."
  print("A enviar requisição para o LM Studio local (porta 1235)...")
  traducao = traduzir_jargao_local(termo_teste)
  print("\nResultado da Tradução:\n", traducao)