import json
import os

def validate_dataset(filepath):
    print(f"🔍 A auditar o ficheiro: {filepath}\n")
    
    if not os.path.exists(filepath):
        print(f"❌ Erro: O ficheiro {filepath} não foi encontrado!")
        return

    total_simples = 0
    empty_outputs = 0
    unique_entries = set()
    duplicates = 0
    malformed_lines = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        if first_line:
            sample_json = json.loads(first_line)
            print(f"📌 Chaves detetadas no teu JSONL: {list(sample_json.keys())}\n")
        f.seek(0)

        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            total_simples += 1
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                malformed_lines += 1
                continue
            
            output_text = (
                data.get('traducao') or 
                data.get('response') or 
                data.get('output') or 
                data.get('text') or 
                data.get('instruction') or 
                str(data)
            )
            
            output_str = str(output_text).strip()
            
            if not output_str:
                empty_outputs += 1
            
            if output_str in unique_entries:
                duplicates += 1
            else:
                unique_entries.add(output_str)

    print("\n" + "="*40)
    print("📊 RELATÓRIO DE QUALIDADE DO DATASET (QA)")
    print("="*40)
    print(f"Total de Amostras Analisadas : {total_simples}")
    print(f"Linhas Malformadas (JSON)   : {malformed_lines}")
    print(f"Saídas Vazias               : {empty_outputs}")
    print(f"Entradas Duplicadas         : {duplicates}")
    print(f"Amostras Únicas Válidas     : {len(unique_entries)}")
    print("="*40)

if __name__ == "__main__":
    validate_dataset("results_jargaozero.jsonl")