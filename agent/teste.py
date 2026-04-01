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
    Versão adaptada com Approach 1 (sem generationConfiguration).
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
            
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            
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
    
    def _build_context_aware_prompt(
        self, 
        question: str, 
        conversation_history: List[Dict] = None,
        max_history: int = int(os.getenv("MAX_CONVERSATION_CONTEXT_HISTORY", "3"))
    ) -> str:
        """
        Constrói um prompt que inclui contexto do histórico de forma inteligente.
        
        Args:
            question: Pergunta atual do usuário
            conversation_history: Histórico de mensagens
            max_history: Número máximo de pares de perguntas/respostas a incluir
            
        Returns:
            Prompt enriquecido com contexto
        """
        if not conversation_history or len(conversation_history) < 2:
            return question
        
        # Extrai apenas os últimos pares de pergunta-resposta
        context_parts = []
        recent_messages = conversation_history[-(max_history * 2):]
        
        # Agrupa em pares (usuário, assistente)
        i = 0
        while i < len(recent_messages) - 1:
            if recent_messages[i]["role"] == "user" and recent_messages[i + 1]["role"] == "assistant":
                user_msg = recent_messages[i]["content"]
                assistant_msg = recent_messages[i + 1]["content"]
                
                # Remove a saudação repetitiva do assistente para economizar tokens
                assistant_clean = assistant_msg
                if assistant_msg.startswith("Olá, sou o SERPRO Assistant"):
                    # Remove a primeira frase de apresentação
                    parts = assistant_msg.split(".", 1)
                    if len(parts) > 1:
                        assistant_clean = parts[1].strip()
                
                # Resumo mais generoso (400 caracteres ao invés de 150)
                assistant_summary = assistant_clean[:400] + "..." if len(assistant_clean) > 400 else assistant_clean
                
                context_parts.append(f"Pergunta anterior: {user_msg}")
                context_parts.append(f"Resposta resumida: {assistant_summary}")
                i += 2
            else:
                i += 1
        
        if not context_parts:
            return question
        
        # Monta o prompt contextualized
        context_text = "\n".join(context_parts)
        
        enhanced_prompt = f"""[CONTEXTO DA CONVERSA]
{context_text}

[NOVA PERGUNTA]
{question}

INSTRUÇÕES:
1. Você já está em uma conversa ativa - NÃO se apresente novamente
2. Continue a conversa de forma natural
3. O contexto acima serve APENAS para entender referências implícitas
4. Baseie sua resposta APENAS nas informações da base de conhecimento
5. Se não encontrar informações, diga explicitamente"""
        
        return enhanced_prompt
    
    def ask_with_context(
        self, 
        question: str, 
        conversation_history: List[Dict] = None,
        max_history: int = 3,
        session_id: Optional[str] = None, 
        save_to_db: bool = True
    ) -> Dict:
        """
        Faz uma pergunta ao agente incluindo histórico de conversa de forma inteligente.
        
        Args:
            question: Pergunta atual
            conversation_history: Lista de mensagens anteriores
            max_history: Número máximo de pares de perguntas/respostas a incluir
            session_id: ID da sessão
            save_to_db: Se deve salvar no banco
            
        Returns:
            Dicionário com answer, tokens, tempo de resposta, etc.
        """
        # Determina se é a primeira mensagem da conversa
        is_first_message = not conversation_history or len(conversation_history) <= 1
        
        if is_first_message:
            # Primeira mensagem: usa a pergunta normal
            contextual_prompt = question
        else:
            # Mensagens subsequentes: usa prompt com contexto
            contextual_prompt = self._build_context_aware_prompt(
                question=question,
                conversation_history=conversation_history,
                max_history=max_history
            )
        
        # Chama o método ask com o prompt apropriado
        return self.ask(
            question=contextual_prompt,
            session_id=session_id,
            save_to_db=save_to_db,
            original_question=question,
            is_first_message=is_first_message
        )

    def ask(
        self,
        question: str,
        session_id: Optional[str] = None,
        save_to_db: bool = True,
        original_question: Optional[str] = None,
        is_first_message: bool = True
    ) -> Dict:
        """
        Faz uma pergunta ao agente e opcionalmente salva no banco de dados.
        USA APPROACH 1: Sem generationConfiguration para melhor funcionamento.
        
        Args:
            question: Pergunta a ser feita (pode incluir contexto)
            session_id: ID opcional da sessão
            save_to_db: Se True, salva a interação no banco de dados
            original_question: Pergunta original do usuário (sem contexto)
            is_first_message: Se é a primeira mensagem da conversa
            
        Returns:
            Dicionário com answer, input_tokens, output_tokens, response_time_ms
        """
        start_time = time.time()
        
        
        
        try:
            print(f"[DEBUG] Primeira mensagem: {is_first_message}")
            print(f"[DEBUG] Pergunta enviada ao Bedrock: {question[:200]}...")
            
            prompt_template = self.config.PROMPT_TEMPLATE
            
            if not is_first_message:
                # Para mensagens subsequentes, modifica o prompt template
                prompt_template = """Você é o **SERPRO Assistant**, um assistente virtual institucional já em conversa ativa com o usuário.
➡️ **Regras de conduta:**
- NÃO se apresente novamente - você já está conversando com o usuário
- Responda apenas perguntas relacionadas aos serviços descritos no Caderno
- Se a pergunta for sobre valores, contratos, clientes, vagas de emprego, infraestrutura interna, segurança, política, opinião ou qualquer assunto fora do escopo do Caderno, responda educadamente:
  'Esta informação não faz parte do Caderno de Serviços do SERPRO.'
- Baseie todas as respostas apenas nas informações retornadas pelos resultados da pesquisa
- Nunca invente ou assuma informações externas
- Seja conciso e objetivo, mas mantenha a cordialidade

➡️ **ATENÇÃO ESPECIAL SOBRE CONTEXTO CONVERSACIONAL:**
- O contexto fornecido na pergunta serve APENAS para entender referências implícitas (como "e isso?", "explique melhor")
- NUNCA assuma que algo mencionado no contexto conversacional está no Caderno
- Sempre valide se a informação existe nos $search_results$ abaixo
- Se não encontrar nos resultados, diga explicitamente: "Não encontrei essa informação específica no Caderno de Serviços"

➡️ **Tarefa:**
Use os resultados abaixo para redigir uma resposta técnica, cordial e institucional sobre o tema solicitado.

$search_results$

Pergunta:
$input_text$"""
            # APPROACH 1: Payload simplificado SEM generationConfiguration
            payload = {
                "input": {"text": question},
                "retrieveAndGenerateConfiguration": {
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.config.KNOWLEDGE_BASE_ID,
                        "modelArn": self.config.MODEL_ARN,
                        
                        "generationConfiguration": {
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                    "maxTokens": self.config.MAX_TOKENS,
                                    "temperature": self.config.TEMPERATURE,
                                    "topP": self.config.TOP_P,
                                }
                            },
                            "promptTemplate": {
                                "textPromptTemplate": prompt_template
                            },
                        },
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": self.config.NUMBER_OF_RESULTS
                            }
                        }
                        # ✅ REMOVIDO: generationConfiguration - usa configuração padrão do Bedrock
                    }
                }
            }

            # Adicionar sessionId se fornecido
            if session_id:
                payload["sessionId"] = session_id

            print("\n@@ ENVIADO AO BEDROCK @@")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print("@@-----------------------")

            # --- ENVIO PARA A API ---
            response = self.client.retrieve_and_generate(**payload)

            # --- LOG DA RESPOSTA ---
            print("\n@@ RESPOSTA DO BEDROCK @@")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            print("@@-----------------------\n")
            
            response_time_ms = int((time.time() - start_time) * 1000)
            answer = response.get("output", {}).get("text", "Não foi possível gerar uma resposta.")
            token_usage = self._extract_token_usage(response)
            
            # Extrair citações para debug
            citations = response.get("citations", [])
            retrieved_references = []
            
            for citation in citations:
                for ref in citation.get("retrievedReferences", []):
                    ref_text = ref.get("content", {}).get("text", "")
                    if ref_text:
                        retrieved_references.append(ref_text[:200] + "..." if len(ref_text) > 200 else ref_text)
            
            print(f"[DEBUG] Citações encontradas: {len(citations)}")
            print(f"[DEBUG] Referências recuperadas: {len(retrieved_references)}")
            if retrieved_references:
                print(f"[DEBUG] Primeira referência: {retrieved_references[0]}")
            
            # Salva no banco usando a pergunta original (sem contexto)
            if save_to_db:
                question_to_save = original_question if original_question else question
                self.db.save_interaction(
                    question=question_to_save,
                    answer=answer,
                    input_tokens=token_usage["input_tokens"],
                    output_tokens=token_usage["output_tokens"],
                    model_id=self.config.MODEL_ARN.split("/")[-1],
                    session_id=session_id,
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
                "session_id": response.get("sessionId"),
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
                "success": False
            }

    def ask_detalhado(
        self,
        question: str,
        session_id: Optional[str] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        Versão detalhada com retrieve separado para debug completo.
        
        Args:
            question: Pergunta a ser feita
            session_id: ID opcional da sessão
            save_to_db: Se deve salvar no banco
            
        Returns:
            Dicionário com informações detalhadas da resposta
        """
        try:
            # Primeiro: retrieve para debug detalhado
            retrieve_response = self.client.retrieve(
                knowledgeBaseId=self.config.KNOWLEDGE_BASE_ID,
                retrievalQuery={"text": question},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": self.config.NUMBER_OF_RESULTS
                    }
                }
            )
            
            retrieval_results = retrieve_response.get("retrievalResults", [])
            
            print(f"\n[DEBUG DETALHADO] Resultados do retrieve:")
            for i, result in enumerate(retrieval_results):
                content = result.get("content", {}).get("text", "")
                score = result.get("score", 0)
                location = result.get("location", {})
                print(f"  {i+1}. Score: {score:.3f}")
                print(f"     Conteúdo: {content[:150]}...")
                print(f"     Localização: {location}")
            
            # Agora usar o método principal
            return self.ask(question, session_id, save_to_db, question, True)
            
        except Exception as e:
            return {
                "answer": f"Erro no retrieve detalhado: {str(e)}",
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