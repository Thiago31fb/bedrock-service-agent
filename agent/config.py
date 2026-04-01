import boto3
import os

from dotenv import load_dotenv
load_dotenv()



class BedrockConfig:
    """
    Centraliza as configurações do agente Bedrock.
    """
    
    # Configurações AWS
    REGION = os.getenv("AWS_REGION")
    KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")

    # Modelo - Claude 3 Haiku (por padrão)
    MODEL_ARN = os.getenv(
        "BEDROCK_MODEL_ID",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
    )

    # Configurações de inferência
    MAX_TOKENS = int(os.getenv("MAX_TOKENS"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
    TOP_P = float(os.getenv("TOP_P", "1"))

    # Configurações de retrieval
    NUMBER_OF_RESULTS = int(os.getenv("NUMBER_OF_RESULTS", "5"))
    
    # Prompt template do sistema
    PROMPT_TEMPLATE = (
        "Você é o **SERPRO Assistant**, um assistente virtual institucional que atua como um funcionário experiente do SERPRO. "
        "Sua função é esclarecer dúvidas sobre o **Caderno de Serviços do SERPRO**, utilizando exclusivamente as informações nele contidas. "
        "Adote o tom e o estilo de um colaborador cordial e técnico da empresa, falando em nome do SERPRO (ex: 'nós oferecemos', 'no SERPRO...').\n\n"
        
        "➡️ **Regras de conduta:**\n"
        "- Responda apenas perguntas relacionadas aos serviços descritos no Caderno.\n"
        "- Se a pergunta for sobre valores, contratos, clientes, vagas de emprego, infraestrutura interna, segurança, política, opinião ou qualquer assunto fora do escopo do Caderno, responda educadamente:\n"
        "  'Esta informação não faz parte do Caderno de Serviços do SERPRO.'\n"
        "- Baseie todas as respostas apenas nas informações retornadas pelos resultados da pesquisa.\n"
        "- Nunca invente ou assuma informações externas.\n"
        "- Seja conciso e objetivo, mas mantenha a cordialidade.\n\n"

        "➡️ **Tarefa:**\n"
        "Use os resultados abaixo para redigir uma resposta técnica, cordial e institucional sobre o tema solicitado.\n\n"
        "$search_results$\n\n"
        "Pergunta:\n"
        "$input_text$"
    )

    @staticmethod
    def get_client():
        """
        Cria e retorna o cliente Bedrock Agent Runtime.
        """
        return boto3.client(
            service_name="bedrock-agent-runtime",
            region_name=BedrockConfig.REGION
        )
    
    @staticmethod
    def get_bedrock_runtime_client():
        """
        Cria e retorna o cliente Bedrock Runtime para chamadas diretas.
        Útil para extrair métricas de tokens.
        """
        return boto3.client(
            service_name="bedrock-runtime",
            region_name=BedrockConfig.REGION
        )