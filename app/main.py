import streamlit as st
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importações
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

st.set_page_config(
    page_title="SERPRO Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo customizado
st.markdown("""
    <style>
        .main-title {
            font-size: 3rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        .subtitle {
            font-size: 1.2rem;
            text-align: center;
            color: #666;
            margin-bottom: 1rem;
        }
        .feature-box {
            background-color: #f0f2f6;
            padding: 2rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Estilos específicos para tema escuro */
        @media (prefers-color-scheme: dark) {
            .main-title {
                color: #64b5f6;
            }
            .subtitle {
                color: #b0b0b0;
            }
            .feature-box {
                background-color: rgba(240, 242, 246, 0.1);
            }
        }

        /* Usando variáveis CSS do Streamlit para maior compatibilidade */
        [data-theme="dark"] .main-title {
            color: #64b5f6;
        }
        
        [data-theme="dark"] .subtitle {
            color: #b0b0b0;
        }
        
        [data-theme="dark"] .feature-box {
            background-color: rgba(240, 242, 246, 0.1);
            color: #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-title">🤖 SERPRO Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Assistente Inteligente para o Caderno de Serviços</div>', unsafe_allow_html=True)

# Introdução
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    ### Bem-vindo ao SERPRO Assistant!
    
    Este é um assistente de IA especializado em responder perguntas sobre o 
    **Caderno de Serviços do SERPRO**, utilizando tecnologia de ponta com AWS Bedrock.
    """)

# Features
st.markdown("---")
st.markdown("### 🎯 Funcionalidades Disponíveis")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-box">
        <h3>💬 Chat Interativo</h3>
        <p>Faça perguntas em linguagem natural sobre os serviços do SERPRO e receba respostas precisas e contextualizadas.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <h3>📊 Métricas de Uso</h3>
        <p>Acompanhe estatísticas detalhadas de consumo de tokens, custos estimados e performance do sistema.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
        <h3>❓ Curiosidades</h3>
        <p>Descubra os temas mais abordados e explore insights sobre o uso do assistente.</p>
    </div>
    """, unsafe_allow_html=True)

# Instruções
st.markdown("---")
st.markdown("### 🚀 Como Usar")

with st.expander("📖 Guia Rápido", expanded=True):
    st.markdown("""
    1. **Navegue pelo menu lateral** para acessar as diferentes funcionalidades
    2. **No Chat**: Digite sua pergunta sobre os serviços do SERPRO
    3. **Nas Métricas**: Visualize estatísticas de uso e custos
    4. **Nas Curiosidades**: Explore as perguntas mais comuns
    
    #### 💡 Dicas para melhores resultados:
    - Seja específico em suas perguntas
    - Use termos técnicos quando apropriado
    - Pergunte sobre serviços, funcionalidades e características
    """)

    st.markdown("""
        ---

        #### 🔒 Sobre a Privacidade
        Todas as interações realizadas no chat são registradas para fins de análise e melhoria contínua.  
        Os dados armazenados incluem apenas:
        - A pergunta enviada  
        - A resposta gerada  
        - Métricas técnicas (tokens utilizados e tempo de resposta)  
        
        Essas informações **não possuem qualquer vínculo com dados pessoais ou de identificação do usuário**.  
        São utilizadas **exclusivamente** para:
        - Avaliar a qualidade e precisão das respostas fornecidas  
        - Identificar dúvidas recorrentes e temas mais abordados  
        - Apoiar a elaboração de **relatórios de uso e aprimoramento do sistema**  

        ✅ A privacidade do usuário é totalmente preservada, garantindo que nenhuma informação sensível ou pessoal seja armazenada.
        """)

# Informações técnicas
st.markdown("---")
st.markdown("### ⚙️ Tecnologias Utilizadas")

tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)

with tech_col1:
    st.info("**AWS Bedrock**\nPlataforma de IA")

with tech_col2:
    st.info("**Claude 3 Haiku**\nModelo de Linguagem")

with tech_col3:
    st.info("**Streamlit**\nInterface Web")

with tech_col4:
    st.info("**SQLite**\nArmazenamento de Dados")



# Privacidade e Monitoramento
st.markdown("---")
st.markdown("### 🔒 Privacidade e Monitoramento de Uso")

st.markdown("""
O **SERPRO Assistant** registra todas as interações realizadas no chat, incluindo:
- A **pergunta enviada** pelo usuário  
- A **resposta gerada** pelo assistente  
- As **métricas de desempenho**, como quantidade de tokens utilizados e tempo de geração da resposta  

Essas informações **não possuem qualquer vínculo com dados pessoais ou de identificação do usuário**.  
São utilizadas **exclusivamente** para:
- Avaliar a qualidade e precisão das respostas fornecidas  
- Identificar dúvidas recorrentes e temas mais abordados  
- Apoiar a elaboração de **relatórios de uso e aprimoramento do sistema**  

✅ A privacidade do usuário é totalmente preservada, garantindo que nenhuma informação sensível ou pessoal seja armazenada.
""")


# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    Projeto de Portfólio | 2025
</div>
""", unsafe_allow_html=True)