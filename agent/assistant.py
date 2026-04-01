import json
import time
from typing import Dict, Optional, List
from agent.config import BedrockConfig
from dataBase.database_manager import DatabaseManager
import os

from dotenv import load_dotenv
load_dotenv()

class Assistant:
    """
    Agente de IA especializado em responder perguntas sobre o Caderno de Serviços.
    Segue a estrutura padrão do Bedrock com gerenciamento automático de sessão.
    """
    
    def __init__(self, db_path: str = "dataBase/agent_metrics.db"):
        """
        Inicializa o assistente.
        
        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        self.client = BedrockConfig.get_client()
        self.db = DatabaseManager(db_path)
        self.config = BedrockConfig()
    
    def _extract_token_usage(self, response: Dict) -> Dict[str, int]:
        """
        Extrai informações de uso de tokens da resposta do Bedrock.
        
        Args:
            response: Resposta do Bedrock
            
        Returns:
            Dicionário com input_tokens e output_tokens
        """
        try:
            usage = response.get("usage", {})
            
            input_tokens = usage.get("inputTokens", '@')
            output_tokens = usage.get("outputTokens", '@')
            
            if input_tokens == 0 and output_tokens == 0:
                citations = response.get("citations", [])
                if citations:
                    output_text = response.get("output", {}).get("text", "")
                    output_tokens = len(output_text) // 4
                    input_tokens = output_tokens // 2
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        except Exception as e:
            print(f"Erro ao extrair tokens: {str(e)}")
            output_text = response.get("output", {}).get("text", "")
            return {
                "input_tokens": len(output_text) // 8,
                "output_tokens": len(output_text) // 4
            }
    
    def _build_prompt_with_history(
        self, 
        conversation_history: List[Dict] = None,
        max_history: int = int(os.getenv("MAX_CONVERSATION_CONTEXT_HISTORY", "3"))
    ) -> str:
        """
        Constrói o prompt template incluindo o histórico de conversa.
        
        Args:
            conversation_history: Histórico de mensagens
            max_history: Número máximo de pares de perguntas/respostas a incluir
            
        Returns:
            Prompt template com histórico embutido
        """
        # Determina se é a primeira mensagem
        is_first_message = not conversation_history or len(conversation_history) <= 1
        
        # Prompt base
        base_prompt = (
            "Você é o **SERPRO Assistant**, um assistente virtual institucional que atua como um funcionário experiente do SERPRO. "
            "Sua função é esclarecer dúvidas sobre o **Caderno de Serviços do SERPRO**, utilizando exclusivamente as informações nele contidas. "
            "Adote o tom e o estilo de um colaborador cordial e técnico da empresa, falando em nome do SERPRO (ex: 'nós oferecemos', 'no SERPRO...').\n\n"
        )
        
        # Se não é a primeira mensagem, adiciona contexto conversacional
        if not is_first_message:
            context_parts = []
            recent_messages = conversation_history[-(max_history * 2):]
            
            # Agrupa em pares (usuário, assistente)
            i = 0
            while i < len(recent_messages) - 1:
                if recent_messages[i]["role"] == "user" and recent_messages[i + 1]["role"] == "assistant":
                    user_msg = recent_messages[i]["content"]
                    assistant_msg = recent_messages[i + 1]["content"]
                    
                    # Remove saudações repetitivas
                    assistant_clean = assistant_msg
                    if assistant_msg.startswith("Olá, sou o SERPRO Assistant"):
                        parts = assistant_msg.split(".", 1)
                        if len(parts) > 1:
                            assistant_clean = parts[1].strip()
                    
                    # Resumo para economizar tokens (400 caracteres)
                    assistant_summary = assistant_clean[:400] + "..." if len(assistant_clean) > 400 else assistant_clean
                    
                    context_parts.append(f"Usuário: {user_msg}")
                    context_parts.append(f"Assistente: {assistant_summary}")
                    i += 2
                else:
                    i += 1
            
            if context_parts:
                history_text = "\n".join(context_parts)
                base_prompt += (
                    f"➡️ **Histórico da conversa (apenas para contexto):**\n"
                    f"{history_text}\n\n"
                    f"**IMPORTANTE:** O histórico acima serve APENAS para entender referências implícitas. "
                    f"NÃO se apresente novamente. Continue a conversa de forma natural. "
                    f"Baseie sua resposta APENAS nas informações dos resultados da pesquisa abaixo.\n\n"
                )
        
        # Adiciona as regras de conduta com instruções detalhadas de formatação
        base_prompt += (
            "➡️ **Regras de conduta:**\n"
            "- Responda apenas perguntas relacionadas aos serviços descritos no Caderno.\n"
            "- Se a pergunta for sobre valores, contratos, clientes, vagas de emprego, infraestrutura interna, segurança, política, opinião ou qualquer assunto fora do escopo do Caderno, responda educadamente:\n"
            "  'Esta informação não faz parte do Caderno de Serviços do SERPRO.'\n"
            "- Baseie todas as respostas apenas nas informações retornadas pelos resultados da pesquisa.\n"
            "- Nunca invente ou assuma informações externas.\n\n"
            
            "➡️ **Formato de resposta obrigatório:**\n"
            "- Para perguntas COMPARATIVAS (ex: 'compare X e Y', 'qual a diferença entre', 'o que distingue'):\n"
            "  • Use estrutura clara com tópicos numerados ou com marcadores\n"
            "  • Dedique um parágrafo completo para cada aspecto comparado\n"
            "  • Inclua exemplos específicos quando disponíveis nos resultados\n"
            "  • Total esperado: 800-1500 caracteres (respostas muito curtas são inadequadas)\n\n"
            "- Para perguntas EXPLICATIVAS (ex: 'o que é', 'como funciona', 'explique'):\n"
            "  • Comece com uma definição clara\n"
            "  • Desenvolva com detalhes técnicos relevantes\n"
            "  • Inclua requisitos, etapas ou características quando aplicável\n"
            "  • Total esperado: 600-1200 caracteres\n\n"
            "- Para perguntas OBJETIVAS (ex: 'qual o prazo', 'quem pode usar'):\n"
            "  • Responda diretamente com a informação solicitada\n"
            "  • Adicione contexto relevante quando disponível\n"
            "  • Total esperado: 300-600 caracteres\n\n"
            
            "➡️ **Tarefa:**\n"
            "Analise cuidadosamente os resultados da pesquisa abaixo e elabore uma resposta COMPLETA e BEM ESTRUTURADA. "
            "Não seja telegráfico. Desenvolva cada ponto adequadamente.\n\n"
            "$search_results$\n\n"
            "$output_format_instructions$"
        )
        
        return base_prompt

    def ask(
        self,
        question: str,
        conversation_history: List[Dict] = None,
        session_id: Optional[str] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        Faz uma pergunta ao agente seguindo a estrutura padrão do Bedrock.
        O sessionId é gerenciado automaticamente pelo Bedrock.
        
        Args:
            question: Pergunta a ser feita
            conversation_history: Histórico de mensagens da conversa
            session_id: ID da sessão (gerenciado automaticamente pelo Bedrock)
            save_to_db: Se True, salva a interação no banco de dados
            
        Returns:
            Dicionário com answer, input_tokens, output_tokens, response_time_ms, session_id
        """
        start_time = time.time()
        
        try:
            # Constrói o prompt template com histórico
            prompt_template = self._build_prompt_with_history(conversation_history)
            
            print(f"[DEBUG] Pergunta: {question}")
            print(f"[DEBUG] Session ID recebido: {session_id}")
            
            # Payload seguindo a estrutura padrão
            payload = {
                "input": {"text": question},
                "retrieveAndGenerateConfiguration": {
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.config.KNOWLEDGE_BASE_ID,
                        "modelArn": self.config.MODEL_ARN,
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": self.config.NUMBER_OF_RESULTS
                            }
                        },
                        "generationConfiguration": {
                            "promptTemplate": {
                                "textPromptTemplate": prompt_template
                            },
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                    "temperature": self.config.TEMPERATURE,
                                    "topP": self.config.TOP_P,
                                    "maxTokens": self.config.MAX_TOKENS,
                                    "stopSequences": ["\nObservation"]
                                }
                            }
                        },
                        "orchestrationConfiguration": {
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                    "temperature": self.config.TEMPERATURE,
                                    "topP": self.config.TOP_P,
                                    "maxTokens": self.config.MAX_TOKENS,
                                    "stopSequences": ["\nObservation"]
                                }
                            }
                        }
                    }
                }
            }

            # Adiciona sessionId SOMENTE se já existir (continuação de conversa)
            if session_id:
                payload["sessionId"] = session_id

            print("\n@@ PAYLOAD ENVIADO AO BEDROCK @@")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print("@@-----------------------------@@\n")

            # Chamada à API do Bedrock
            response = self.client.retrieve_and_generate(**payload)

            print("\n@@ RESPOSTA DO BEDROCK @@")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            print("@@-----------------------@@\n")
            
            response_time_ms = int((time.time() - start_time) * 1000)
            answer = response.get("output", {}).get("text", "Não foi possível gerar uma resposta.")
            token_usage = self._extract_token_usage(response)
            
            # Obtém o sessionId retornado pelo Bedrock
            returned_session_id = response.get("sessionId")
            
            # Extrair citações para debug
            citations = response.get("citations", [])
            retrieved_references = []
            
            for citation in citations:
                for ref in citation.get("retrievedReferences", []):
                    ref_text = ref.get("content", {}).get("text", "")
                    if ref_text:
                        retrieved_references.append(ref_text[:200] + "..." if len(ref_text) > 200 else ref_text)
            
            print(f"[DEBUG] Session ID retornado: {returned_session_id}")
            print(f"[DEBUG] Citações encontradas: {len(citations)}")
            print(f"[DEBUG] Referências recuperadas: {len(retrieved_references)}")
            
            # Salva no banco
            if save_to_db:
                self.db.save_interaction(
                    question=question,
                    answer=answer,
                    input_tokens=token_usage["input_tokens"],
                    output_tokens=token_usage["output_tokens"],
                    model_id=self.config.MODEL_ARN.split("/")[-1],
                    session_id=returned_session_id,
                    response_time_ms=response_time_ms
                )
            
            return {
                "answer": answer,
                "input_tokens": token_usage["input_tokens"],
                "output_tokens": token_usage["output_tokens"],
                "total_tokens": token_usage["input_tokens"] + token_usage["output_tokens"],
                "response_time_ms": response_time_ms,
                "citations_count": len(citations),
                "references_count": len(retrieved_references),
                "session_id": returned_session_id,  # Retorna o sessionId para uso futuro
                "success": True
            }
            
        except Exception as e:
            error_message = f"Erro ao processar pergunta: {str(e)}"
            print(error_message)
            
            return {
                "answer": "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.",
                "error": str(e),
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "citations_count": 0,
                "references_count": 0,
                "session_id": session_id,
                "success": False
            }
    
    def get_metrics(self) -> Dict:
        """
        Retorna métricas de uso do agente.
        """
        return {
            "total_tokens": self.db.get_total_tokens(),
            "average_tokens": self.db.get_average_tokens(),
            "interaction_count": self.db.get_interaction_count()
        }

    def get_session_metrics(self, session_id: str) -> Dict:
        """
        Retorna métricas específicas de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dicionário com métricas da sessão
        """
        return self.db.get_session_metrics(session_id)