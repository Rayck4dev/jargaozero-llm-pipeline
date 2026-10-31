import json
import random

def validar_e_dividir_dataset(input_file, train_ratio=0.8, val_ratio=0.1):
    with open(input_file, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    amostras_validas = []
    erros = 0

    for i, linha in enumerate(linhas, start=1):
        if not linha.strip():
            continue
        try:
            dado = json.loads(linha)
            if "messages" in dado and len(dado["messages"]) == 3:
                amostras_validas.append(dado)
            else:
                print(f"⚠️ Alerta na linha {i}: Estrutura de mensagens inválida.")
                erros += 1
        except json.JSONDecodeError as e:
            print(f"❌ Erro de sintaxe JSON na linha {i}: {e}")
            erros += 1

    print(f"\n✅ Total de amostras válidas: {len(amostras_validas)}")
    if erros > 0:
        print(f"⚠️ Total de erros/inconsistências encontrados: {erros}")

    random.shuffle(amostras_validas)
    n_total = len(amostras_validas)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    treino = amostras_validas[:n_train]
    validacao = amostras_validas[n_train:n_train + n_val]
    teste = amostras_validas[n_train + n_val:]

    def salvar_jsonl(dados, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for item in dados:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

    salvar_jsonl(treino, "train.jsonl")
    salvar_jsonl(validacao, "validation.jsonl")
    salvar_jsonl(teste, "test.jsonl")

    print("\n📂 Ficheiros gerados com sucesso:")
    print(f" - train.jsonl ({len(treino)} amostras)")
    print(f" - validation.jsonl ({len(validacao)} amostras)")
    print(f" - test.jsonl ({len(teste)} amostras)")

validar_e_dividir_dataset("training_dataset.jsonl")