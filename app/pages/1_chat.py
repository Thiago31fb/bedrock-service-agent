import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import os


# Adiciona o diretório raiz ao path para importações
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from agent.assistant import Assistant

st.set_page_config(
    page_title="Chat - SERPRO Assistant",
    page_icon="💬",
    layout="wide"
)

# Inicialização do session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Session ID gerenciado pelo Bedrock (None inicialmente)
if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "assistant" not in st.session_state:
    st.session_state.assistant = Assistant(db_path="dataBase/agent_metrics.db")

# CSS customizado
st.markdown("""
    <style>
        .chat-message {
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .user-message {
            background-color: rgba(33, 150, 243, 0.1);
            border-left: 5px solid #2196F3;
            color: inherit;
        }
        .assistant-message {
            background-color: rgba(76, 175, 80, 0.1);
            border-left: 5px solid #4CAF50;
            color: inherit;
        }
        .metrics-box {
            background-color: rgba(255, 193, 7, 0.1);
            padding: 1rem;
            border-radius: 5px;
            margin-top: 0.5rem;
            font-size: 0.9rem;
            border: 1px solid rgba(255, 193, 7, 0.3);
        }

        /* Estilos específicos para tema escuro */
        @media (prefers-color-scheme: dark) {
            .user-message {
                background-color: rgba(33, 150, 243, 0.2);
                border-left: 5px solid #64b5f6;
            }
            .assistant-message {
                background-color: rgba(76, 175, 80, 0.2);
                border-left: 5px solid #81c784;
            }
            .metrics-box {
                background-color: rgba(255, 193, 7, 0.2);
                border: 1px solid rgba(255, 193, 7, 0.4);
            }
        }
    </style>
""", unsafe_allow_html=True)

# Título
st.title("💬 Chat com SERPRO Assistant")
st.markdown("Faça perguntas sobre o Caderno de Serviços do SERPRO")
st.metric(
    "Modelo",
    '',
    help = os.getenv("BEDROCK_MODEL_ID")
)
st.markdown("---")

# Sidebar com informações
with st.sidebar:
    st.header("ℹ️ Sobre o Chat")
    st.info("""
    Este chat utiliza IA para responder perguntas sobre o Caderno de Serviços do SERPRO.
    
    **Como usar:**
    - Digite sua pergunta no campo abaixo
    - Aguarde a resposta do assistente
    - As métricas de tokens serão exibidas abaixo de cada resposta
    
    **Gerenciamento de Sessão:**
    - O Bedrock gerencia automaticamente o contexto da conversa
    - Cada conversa tem um Session ID único
    """)
    
    st.markdown("---")
    
    st.header("📋 Exemplos de Perguntas")
    st.markdown("""
    - Quais são os serviços de Data Center?
    - O que é IaaS?
    - Como funciona a hospedagem virtualizada?
    - Quais são os SLAs oferecidos?
    - O que significa WAF?
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None  # Reset session ID
        st.rerun()
    
    # Estatísticas da sessão atual
    st.markdown("---")
    st.header("📊 Sessão Atual")
    st.metric("Mensagens", len(st.session_state.messages) // 2)
    
    # Mostra Session ID se disponível
    if st.session_state.session_id:
        st.markdown("---")
        st.text_input(
            "Session ID",
            value=st.session_state.session_id,
            disabled=True,
            help="ID único da sessão gerenciado pelo Bedrock"
        )

# Container para o chat
chat_container = st.container()

# Exibe mensagens anteriores
with chat_container:
    for message in st.session_state.messages:
        message_class = "user-message" if message["role"] == "user" else "assistant-message"
        icon = "👤" if message["role"] == "user" else "🤖"
        
        st.markdown(f"""
            <div class="chat-message {message_class}">
                <strong>{icon} {"Você" if message["role"] == "user" else "SERPRO Assistant"}</strong>
                <p style="margin-top: 0.5rem;">{message["content"]}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Exibe métricas se for uma resposta do assistente
        if message["role"] == "assistant" and "metrics" in message:
            metrics = message["metrics"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔤 Tokens Entrada", metrics.get("input_tokens", 0))
            with col2:
                st.metric("🔤 Tokens Saída", metrics.get("output_tokens", 0))
            with col3:
                st.metric("📊 Total", metrics.get("total_tokens", 0))
            with col4:
                st.metric("⏱️ Tempo", f"{metrics.get('response_time_ms', 0)}ms")

# Input do usuário
st.markdown("---")
user_input = st.chat_input("Digite sua pergunta aqui...")

if user_input:
    # Adiciona mensagem do usuário
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Exibe mensagem do usuário imediatamente
    with chat_container:
        st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 Você</strong>
                <p style="margin-top: 0.5rem;">{user_input}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Mostra spinner enquanto processa
    with st.spinner("🤔 Processando sua pergunta..."):
        try:
            # Chama o assistente com histórico e session_id
            result = st.session_state.assistant.ask(
                question=user_input,
                conversation_history=st.session_state.messages,
                session_id=st.session_state.session_id  # Passa o session_id atual
            )

            if result["success"]:
                # Atualiza o session_id com o retornado pelo Bedrock
                st.session_state.session_id = result.get("session_id")
                
                # Adiciona resposta do assistente
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "metrics": {
                        "input_tokens": result["input_tokens"],
                        "output_tokens": result["output_tokens"],
                        "total_tokens": result["total_tokens"],
                        "response_time_ms": result["response_time_ms"]
                    }
                })
                
                # Recarrega a página para mostrar a resposta
                st.rerun()
            else:
                st.error(f"❌ Erro: {result.get('error', 'Erro desconhecido')}")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar pergunta: {str(e)}")

# Aviso sobre refresh
if len(st.session_state.messages) > 0:
    st.info("ℹ️ **Atenção:** Se você recarregar a página, o histórico da conversa será perdido.")

# Rodapé
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 1rem;">
            💡 <strong>Dica:</strong> Quanto mais específica a pergunta, melhor a resposta!
        </div>
    """, unsafe_allow_html=True)