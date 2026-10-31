import json

def remover_duplicados(filepath="results_jargaozero.jsonl"):
    seen_outputs = set()
    linhas_unicas = []
    duplicados_removidos = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for linha in f:
            linha_strip = linha.strip()
            if not linha_strip:
                continue
            
            try:
                dados = json.loads(linha_strip)
                traducao = dados.get("traducao", "").strip()
                
                if traducao in seen_outputs:
                    duplicados_removidos += 1
                    print(f"🔄 A remover duplicado: {traducao[:60]}...")
                else:
                    seen_outputs.add(traducao)
                    linhas_unicas.append(linha_strip)
            except json.JSONDecodeError:
                linhas_unicas.append(linha_strip)

    with open(filepath, "w", encoding="utf-8") as f:
        for linha in linhas_unicas:
            f.write(linha + "\n")

    print(f"\n✅ Limpeza concluída! Foram removidos {duplicados_removidos} duplicados.")
    print(f"📂 Total final de amostras únicas no ficheiro: {len(linhas_unicas)}")

if __name__ == "__main__":
    remover_duplicados()