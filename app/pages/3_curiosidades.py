import streamlit as st
import sys
from pathlib import Path
from collections import Counter
import pandas as pd
import plotly.express as px

# Adiciona o diretório raiz ao path
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from dataBase import DatabaseManager

st.set_page_config(
    page_title="Curiosidades - SERPRO Assistant",
    page_icon="❓",
    layout="wide"
)

# Inicializa o banco de dados
@st.cache_resource
def get_database():
    return DatabaseManager(db_path="dataBase/agent_metrics.db")

db = get_database()

# Título
st.title("❓ Curiosidades e Insights")
st.markdown("Descubra padrões de uso e perguntas frequentes")
st.markdown("---")

# Botão de atualização
col_refresh1, col_refresh2 = st.columns([6, 1])
with col_refresh2:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# Obter dados
interaction_count = db.get_interaction_count()
all_questions = db.get_all_questions()

# Verifica se há dados suficientes
if interaction_count < 5:
    st.warning(f"""
        ⚠️ **Dados Insuficientes**
        
        Atualmente há apenas **{interaction_count}** interações registradas.
        
        Para gerar insights e curiosidades, são necessárias pelo menos **5 interações**.
        
        Continue usando o chat para acumular mais dados!
    """)
    
    st.info("💡 **Dica:** As curiosidades incluirão análises como palavras mais usadas, temas populares e estatísticas interessantes.")
    
else:
    
    # Análise de temas
    st.header("🎯 Temas Mais Abordados")
    
    # Define temas e palavras-chave relacionadas
    temas = {
        "Data Center": ["data", "center", "datacenter", "servidor", "hospedagem", "colocation", "infraestrutura"],
        "Nuvem": ["nuvem", "cloud", "iaas", "paas", "saas", "virtualização", "multicloud"],
        "Segurança": ["segurança", "waf", "firewall", "proteção", "ssl", "certificado", "privacidade", "lgpd", "biometria", "autenticidade"],
        "Rede": ["rede", "wan", "lan", "internet", "conectividade", "vpn", "infovia", "longa distância"],
        "Banco de Dados": ["banco", "dados", "database", "sql", "oracle", "postgresql", "bases", "informações"],
        "Aplicações": ["aplicação", "aplicações", "app", "sistema", "plataforma", "software", "desenvolvimento", "manutenção"],
        "SLA": ["sla", "disponibilidade", "uptime", "garantia", "acordo", "níveis de serviço"],
        "Backup": ["backup", "restore", "recuperação", "disaster", "rpo", "rto"],
        "Trânsito e Veículos": ["trânsito", "veículos", "denatran", "renavam", "renach", "recall", "emplacamento", "infrações", "cnh", "pid", "recall", "renave"],
        "Identidade Digital e Biometria": ["identidade digital", "biometria", "psbio", "datavalid", "proid", "certificado digital", "assinatura digital"],
        "Dados e Analytics": ["dados", "analytics", "daas", "govdata", "painel", "estatísticas", "inteligência", "informações"],
        "Comércio Exterior": ["comércio exterior", "comex", "aduaneira", "loja franca", "importação", "exportação", "du-e", "siscomex"],
        "Gestão e Processos": ["gestão", "processos", "consultoria", "workflow", "atendimento", "central de serviços", "suporte técnico"],
        "Documentos e Certificação": ["documentos", "certificação", "digitalização", "carimbo do tempo", "cnd", "ccir", "laudos toxicológicos", "vio"]
    }
    
    # Conta quantas perguntas mencionam cada tema
    tema_counts = {}
    for tema, keywords in temas.items():
        count = sum(1 for q in all_questions 
                   if any(kw in q.lower() for kw in keywords))
        if count > 0:
            tema_counts[tema] = count
    
    if tema_counts:
        # Ordena por contagem
        tema_counts_sorted = dict(sorted(tema_counts.items(), 
                                        key=lambda x: x[1], 
                                        reverse=True))
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Gráfico de pizza dos temas
            df_temas = pd.DataFrame(
                list(tema_counts_sorted.items()),
                columns=['Tema', 'Quantidade']
            )
            
            fig_temas = px.pie(
                df_temas,
                values='Quantidade',
                names='Tema',
                title="Distribuição de Perguntas por Tema",
                hole=0.4
            )
            
            fig_temas.update_traces(textposition='inside', textinfo='percent+label')
            fig_temas.update_layout(height=500)
            
            st.plotly_chart(fig_temas, use_container_width=True)
        
        with col2:
            st.subheader("📋 Ranking de Temas")
            for i, (tema, count) in enumerate(tema_counts_sorted.items(), 1):
                percentage = (count / interaction_count) * 100
                st.metric(
                    f"{i}º - {tema}",
                    f"{count} perguntas",
                    delta=f"{percentage:.1f}%"
                )
    else:
        st.info("Nenhum tema específico identificado ainda. Continue usando o chat!")
    
    st.markdown("---")
    
    # Estatísticas curiosas
    st.header("🎲 Estatísticas Interessantes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Pergunta mais longa
        if all_questions:
            longest_q = max(all_questions, key=len)
            st.metric(
                "📏 Pergunta Mais Longa",
                f"{len(longest_q)} caracteres"
            )
    
    with col2:
        # Pergunta mais curta
        if all_questions:
            shortest_q = min(all_questions, key=len)
            st.metric(
                "📏 Pergunta Mais Curta",
                f"{len(shortest_q)} caracteres"
            )
    
    with col3:
        # Tamanho médio das perguntas
        if all_questions:
            avg_length = sum(len(q) for q in all_questions) / len(all_questions)
            st.metric(
                "📊 Tamanho Médio",
                f"{avg_length:.0f} caracteres"
            )
    
    st.markdown("---")
    
    
    # Insights automáticos
    st.header("🧠 Insights Automáticos")
    
    insights = []
    
    # Insight 1: Tema mais popular
    if tema_counts:
        tema_popular = max(tema_counts, key=tema_counts.get)
        insights.append(f"🔥 O tema **{tema_popular}** é o mais abordado, aparecendo em **{tema_counts[tema_popular]}** perguntas.")
    
    # # Insight 2: Palavras-chave
    # if top_words:
    #     palavra_popular = top_words[0][0]
    #     freq_popular = top_words[0][1]
    #     insights.append(f"🎯 A palavra **'{palavra_popular}'** foi mencionada **{freq_popular}** vezes nas perguntas.")
    
    # Insight 3: Tamanho das perguntas
    if all_questions:
        avg_len = sum(len(q) for q in all_questions) / len(all_questions)
        if avg_len > 100:
            insights.append(f"📝 Os usuários tendem a fazer perguntas detalhadas, com média de **{avg_len:.0f}** caracteres.")
        else:
            insights.append(f"⚡ Os usuários preferem perguntas diretas e objetivas, com média de **{avg_len:.0f}** caracteres.")
    
    # Insight 4: Interações totais
    insights.append(f"📊 Já foram realizadas **{interaction_count}** interações com o assistente.")
    
    # Exibe os insights
    for insight in insights:
        st.success(insight)

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    💡 Quanto mais você usar o assistente, mais insights serão gerados!
</div>
""", unsafe_allow_html=True)