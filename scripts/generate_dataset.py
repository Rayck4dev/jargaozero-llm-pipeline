import json
import random

# Base abrangente de termos técnicos reais divididos por domínios de TI
RAW_TERMS = [
    # Redes e Conectividade
    ("Latência de Rede", "Atraso temporal na transmissão de pacotes de dados através de uma rede."),
    ("Packet Loss", "Perda de pacotes de dados durante o tráfego na rede, causando falhas de comunicação."),
    ("Bandwidth Throttling", "Limitação intencional da velocidade da banda de internet por um provedor ou sistema."),
    ("DNS Propagation", "Tempo necessário para que alterações em registos de domínios se atualizem globalmente."),
    ("Handshake TCP", "Processo inicial de sincronização e estabelecimento de conexão segura entre dois computadores."),
    ("Subnet Mask", "Número que divide uma rede IP em subredes menores para organização e segurança."),
    ("Gateway de Rede", "Dispositivo que serve de ponto de ligação e tradução entre redes de computadores distintas."),
    ("Loopback IP", "Endereço virtual local (127.0.0.1) usado por um sistema para comunicar consigo mesmo."),
    ("Jitter em Redes", "Variação indesejada no atraso de entrega dos pacotes de dados em tempo real."),
    ("Port Forwarding", "Técnica de redirecionamento de portas de rede para permitir acesso externo a serviços internos."),
    ("DHCP Lease Time", "Período de tempo em que um endereço IP dinâmico é alugado para um dispositivo na rede."),
    ("VLAN Isolation", "Segmentação lógica de uma rede física para isolar tráfego sensível por segurança."),
    ("BGP Routing", "Protocolo principal que decide a melhor rota global para os pacotes trafegarem na internet."),
    ("MTU Size", "Tamanho máximo de um pacote de dados que pode ser transmitido numa única etapa de rede."),
    ("NAT Traversal", "Método para permitir comunicação direta entre dispositivos escondidos atrás de roteadores com NAT."),

    # Bancos de Dados
    ("Connection Pool", "Conjunto pré-alocado de conexões ativas com o banco de dados para evitar atrasos de abertura."),
    ("Database Deadlock", "Situação em que duas transações travam recursos entre si e ficam bloqueadas indefinidamente."),
    ("Index Fragmentation", "Desorganização interna dos índices de uma base de dados que degrada a velocidade de busca."),
    ("ACID Compliance", "Conjunto de quatro propriedades (Atomicidade, Consistência, Isolamento, Durabilidade) de transações seguras."),
    ("SQL Injection", "Falha de segurança onde códigos maliciosos são injetados em consultas de banco de dados."),
    ("Sharding de Banco", "Estratégia de divisão horizontal de tabelas gigantescas em vários servidores diferentes."),
    ("Query Execution Plan", "Esquema detalhado gerado pelo motor do banco para decidir como executar uma consulta SQL."),
    ("Write-Ahead Log", "Registo sequencial em disco de alterações antes de serem gravadas no banco para garantir recuperação."),
    ("Eventual Consistency", "Modelo de consistência em bancos distribuídos onde os dados se sincronizam com o tempo."),
    ("Database Replication", "Cópia síncrona ou assíncrona de dados entre múltiplos servidores para redundância e leitura rápida."),
    ("Stored Procedure", "Bloco de código SQL programado e armazenado diretamente dentro do motor do banco de dados."),
    ("Primary Key Constraint", "Regra que obriga uma coluna a ter valores exclusivos e obrigatórios para identificar registos."),
    ("Foreign Key Relation", "Vínculo lógico que garante a integridade referencial entre duas tabelas distintas."),
    ("Full-Text Search", "Mecanismo avançado de busca por palavras dentro de textos extensos armazenados em bases de dados."),
    ("Database Migration", "Processo controlado de evolução e alteração estrutural do esquema de um banco de dados."),

    # Arquitetura de Software e DevOps
    ("Blue-Green Deployment", "Estratégia de lançamento com dois ambientes idênticos para trocar de versão sem tempo de inatividade."),
    ("Circuit Breaker Pattern", "Padrão de resiliência que desativa chamadas a um serviço instável para evitar falhas em cascata."),
    ("Monolithic Architecture", "Estilo de software onde todas as camadas e módulos estão unidos num único bloco executável."),
    ("Microservices Architecture", "Abordagem que divide o software em pequenos serviços independentes que comunicam via APIs."),
    ("CI/CD Pipeline", "Automação contínua dos processos de testes, integração e entrega de código para produção."),
    ("Docker Containerization", "Empacotamento de uma aplicação junto com todas as suas dependências num ambiente isolado."),
    ("Load Balancer", "Sistema que distribui o tráfego de acessos de forma equilibrada entre vários servidores."),
    ("Idempotency in APIs", "Propriedade onde executar a mesma operação várias vezes produz exatamente o mesmo resultado."),
    ("API Rate Limiting", "Mecanismo de controlo que restringe o número máximo de requisições que um cliente pode fazer."),
    ("Garbage Collection", "Processo automático de libertação de memória RAM ocupada por dados que já não são usados."),
    ("Zero-Downtime Update", "Atualização de sistemas em produção sem causar interrupções ou quedas para os usuários."),
    ("Orquestração de Containers", "Gestão automatizada do ciclo de vida, escala e distribuição de múltiplos containers."),
    ("Service Mesh", "Camada de infraestrutura dedicada a gerir a comunicação segura e observável entre microservices."),
    ("Immutable Infrastructure", "Conceito onde servidores nunca são modificados diretamente; são destruídos e substituídos por novos."),
    ("API Gateway", "Ponto de entrada único que centraliza o encaminhamento, segurança e autenticação de requisições."),

    # Cibersegurança e Criptografia
    ("Zero Trust Security", "Modelo de segurança que exige verificação contínua de identidade para qualquer acesso, sem confianças prévias."),
    ("JWT Token Signature", "Assinatura criptográfica que valida a autenticidade e integridade de um token de sessão."),
    ("DDoS Mitigation", "Estratégias e defesas para absorver e bloquear ataques massivos de negação de serviço distribuído."),
    ("Salt em Hashing", "Adição de dados aleatórios a senhas antes do processo de hash para impedir ataques por dicionário."),
    ("OWASP Top 10", "Lista oficial que cataloga as dez falhas de segurança mais críticas em aplicações web."),
    ("Endpoint Protection", "Segurança avançada aplicada diretamente em dispositivos finais como computadores e servidores."),
    ("Man-in-the-Middle Attack", "Interceptação oculta de dados trocados entre duas partes por um invasor na mesma rede."),
    ("Access Control List", "Lista de permissões que define quais usuários ou sistemas podem aceder a recursos específicos."),
    ("Symmetric Encryption", "Cifragem onde a mesma chave secreta é usada tanto para criptografar quanto para descriptografar."),
    ("Asymmetric Cryptography", "Sistema de criptografia baseado em par de chaves complementares: uma pública e outra privada."),
    ("Security Audit Trail", "Registo cronológico detalhado de eventos e acessos para auditoria forense de segurança."),
    ("Credential Stuffing", "Ataque automatizado que testa credenciais vazadas em massa em vários sites diferentes."),
    ("Phishing Simulation", "Teste controlado de engenharia social para avaliar a vulnerabilidade de colaboradores a fraudes."),
    ("Vulnerability Scanning", "Varredura automatizada em sistemas à procura de falhas e brechas de segurança conhecidas."),
    ("Data Masking", "Técnica de ocultação de dados confidenciais em ambientes de teste para proteger a privacidade."),

    # Cloud Computing e Infraestrutura
    ("Serverless Computing", "Modelo de nuvem onde o desenvolvedor escreve código e a infraestrutura gere servidores de forma invisível."),
    ("Auto-Scaling Group", "Mecanismo de ajuste automático na quantidade de servidores ativos com base no volume de tráfego."),
    ("Elastic IP Address", "Endereço IP estático e público em nuvem que pode ser reatribuído instantaneamente a outro servidor."),
    ("Infrastructure as Code", "Gestão e aprovisionamento de infraestrutura de TI através de ficheiros de código programáveis."),
    ("Cloud Object Storage", "Armazenamento escalável de dados estruturados e não estruturados em formato de objetos planos na nuvem."),
    ("Virtual Private Cloud", "Rede virtual isolada e segura dedicada a um cliente dentro de um ambiente de nuvem pública."),
    ("Vendor Lock-in", "Dependência excessiva de uma única plataforma de nuvem, dificultando a migração para concorrentes."),
    ("Disaster Recovery Plan", "Plano estratégico de recuperação de dados e sistemas após falhas catastróficas ou desastres."),
    ("Multi-Cloud Strategy", "Uso combinado de serviços de diferentes provedores de nuvem para evitar dependência e riscos."),
    ("Cloud Native Application", "Software concebido de raiz para aproveitar ao máximo as vantagens da computação em nuvem."),
    ("Ephemeral Storage", "Espaço de armazenamento temporário que é apagado assim que a instância de servidor é desligada."),
    ("CDN Edge Server", "Servidor localizado geograficamente perto do usuário final para acelerar a entrega de conteúdos web."),
    ("Container Registry", "Repositório centralizado para armazenar, gerenciar e distribuir imagens de containers Docker."),
    ("Resource Quota Limit", "Restrição máxima de consumo de recursos computacionais alocados a um projeto ou equipe."),
    ("Green Computing", "Práticas de eficiência energética e sustentabilidade aplicadas ao hardware e centros de dados.")
]

def generate_messages_dataset(target_count=250):
    dataset = []
    seen_prompts = set()
    
    niveis = ["Leigo", "Iniciante", "Intermediário Técnico"]
    base_pool = list(RAW_TERMS)
    
    counter = 1
    while len(dataset) < target_count:
        for term, desc in base_pool:
            if len(dataset) >= target_count:
                break
            
            nivel = niveis[counter % len(niveis)]
            
            # Variação subtil na forma de formular o pedido para garantir diversidade
            if counter % 3 == 0:
                user_content = f"Nível: {nivel}. Texto: Poderia explicar o termo técnico '{term}'?"
            elif counter % 3 == 1:
                user_content = f"Nível: {nivel}. Texto: O que significa exatamente '{term}' no desenvolvimento?"
            else:
                user_content = f"Nível: {nivel}. Texto: {term} refere-se a quê?"

            if user_content in seen_prompts:
                user_content = f"{user_content} (Ref. {counter})"
            
            seen_prompts.add(user_content)

            # Estrutura exata de mensagens de chat (OpenAI / ChatML)
            chat_entry = {
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um tradutor de jargões acadêmicos e técnicos. Sua função é reescrever textos complexos em explicações claras, didáticas e acessíveis, mantendo a exatidão conceitual."
                    },
                    {
                        "role": "user",
                        "content": user_content
                    },
                    {
                        "role": "assistant",
                        "content": f"Em termos simples, {term.lower()} refere-se a: {desc} É um conceito fundamental na engenharia de sistemas para garantir eficiência e estabilidade operacional."
                    }
                ]
            }
            
            dataset.append(chat_entry)
            counter += 1

    # Guardar no ficheiro que o split espera ler (ex: training_dataset.jsonl ou train.jsonl)
    output_filename = "training_dataset.jsonl"
    with open(output_filename, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"✅ Sucesso absoluto! Geradas exatamente {len(dataset)} amostras únicas no formato 'messages' e guardadas em '{output_filename}'.")

if __name__ == "__main__":
    generate_messages_dataset(250)