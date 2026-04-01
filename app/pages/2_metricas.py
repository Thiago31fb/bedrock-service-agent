import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Adiciona o diretório raiz ao path
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from dataBase import DatabaseManager

st.set_page_config(
    page_title="Métricas - SERPRO Assistant",
    page_icon="📊",
    layout="wide"
)

# Função para formatar números
def formata_numero(valor, prefixo=''):
    if valor < 1000:
        return f'{prefixo} {valor:.0f}'
    elif valor < 1000000:
        return f'{prefixo} {valor/1000:.1f}K'
    else:
        return f'{prefixo} {valor/1000000:.1f}M'

# Função para calcular custo estimado (baseado em preços aproximados do Claude)
def calcular_custo(input_tokens, output_tokens):
    CUSTO_INPUT_POR_MIL =  0.0003 
    CUSTO_OUTPUT_POR_MIL = 0.015  
    
    custo_input = (input_tokens / 1_000) * CUSTO_INPUT_POR_MIL
    custo_output = (output_tokens / 1_000) * CUSTO_OUTPUT_POR_MIL
    
    
    return custo_input + custo_output

# Inicializa o banco de dados
@st.cache_resource
def get_database():
    return DatabaseManager(db_path="dataBase/agent_metrics.db")

db = get_database()

# Título
st.title("📊 Métricas e Estatísticas")
st.markdown("Acompanhe o uso e performance do SERPRO Assistant")
st.markdown("---")

# Botão de atualização
col_refresh1, col_refresh2 = st.columns([6, 1])
with col_refresh2:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# Obter dados
total_tokens = db.get_total_tokens()
avg_tokens = db.get_average_tokens()
interaction_count = db.get_interaction_count()
recent_questions = db.get_recent_questions(limit=50)
stats_by_date = db.get_statistics_by_date(days=30)

# Calcula custos
custo_total = calcular_custo(
    total_tokens['total_input'],
    total_tokens['total_output']
)

# Seção 1: Métricas Principais
st.header("📈 Visão Geral")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total de Interações",
        formata_numero(interaction_count),
        help="Número total de perguntas respondidas"
    )

with col2:
    st.metric(
        "Total de Tokens",
        formata_numero(total_tokens['total']),
        help="Soma de todos os tokens processados"
    )

with col3:
    st.metric(
        "Média de Tokens/Interação",
        formata_numero(avg_tokens['avg_total']),
        help="Média de tokens por pergunta"
    )

with col4:
    st.metric(
        "Custo Estimado",
        f"${custo_total:.4f}",
        help="Custo aproximado baseado em preços do Claude 3 Haiku"
    )

st.markdown("---")

# Seção 2: Distribuição de Tokens
st.header("🔤 Análise de Tokens")

col1, col2 = st.columns(2)

with col1:
    # Gráfico de pizza - Distribuição Input vs Output
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Tokens de Entrada', 'Tokens de Saída'],
        values=[total_tokens['total_input'], total_tokens['total_output']],
        hole=0.4,
        marker_colors=['#2196F3', '#4CAF50']
    )])
    fig_pie.update_layout(
        title="Distribuição de Tokens (Total)",
        height=400
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Métricas detalhadas
    st.subheader("📊 Detalhamento")
    
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric(
            "🔵 Tokens de Entrada",
            formata_numero(total_tokens['total_input']),
            delta=f"Média: {avg_tokens['avg_input']:.0f}"
        )
    
    with metric_col2:
        st.metric(
            "🟢 Tokens de Saída",
            formata_numero(total_tokens['total_output']),
            delta=f"Média: {avg_tokens['avg_output']:.0f}"
        )
    
    st.markdown("---")
    
    # Projeção de custos
    st.subheader("💰 Projeção de Custos")
    
    custo_input = calcular_custo(total_tokens['total_input'], 0)
    custo_output = calcular_custo(0, total_tokens['total_output'])
    
    st.write(f"**Custo de Entrada:** ${custo_input:.4f}")
    st.write(f"**Custo de Saída:** ${custo_output:.4f}")
    st.write(f"**Custo Total:** ${custo_total:.4f}")
    
    if interaction_count > 0:
        custo_por_interacao = custo_total / interaction_count
        st.write(f"**Custo por Interação:** ${custo_por_interacao:.4f}")

st.markdown("---")

# Seção 3: Estatísticas por Data
if stats_by_date:
    st.header("📅 Evolução Temporal")
    
    # Prepara dados para o gráfico
    df_stats = pd.DataFrame(stats_by_date)
    df_stats['date'] = pd.to_datetime(df_stats['date'])
    df_stats = df_stats.sort_values('date')
    
    # Gráfico de linha - Interações ao longo do tempo
    fig_timeline = go.Figure()
    
    fig_timeline.add_trace(go.Scatter(
        x=df_stats['date'],
        y=df_stats['interactions'],
        mode='lines+markers',
        name='Interações',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=8)
    ))
    
    fig_timeline.update_layout(
        title="Número de Interações por Dia",
        xaxis_title="Data",
        yaxis_title="Interações",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras - Tokens por dia
        fig_tokens = go.Figure()
        
        fig_tokens.add_trace(go.Bar(
            x=df_stats['date'],
            y=df_stats['total_input'],
            name='Tokens Entrada',
            marker_color='#2196F3'
        ))
        
        fig_tokens.add_trace(go.Bar(
            x=df_stats['date'],
            y=df_stats['total_output'],
            name='Tokens Saída',
            marker_color='#4CAF50'
        ))
        
        fig_tokens.update_layout(
            title="Tokens por Dia",
            xaxis_title="Data",
            yaxis_title="Tokens",
            barmode='stack',
            height=400
        )
        
        st.plotly_chart(fig_tokens, use_container_width=True)
    
    with col2:
        # Gráfico de linha - Tempo de resposta
        fig_response = px.line(
            df_stats,
            x='date',
            y='avg_response_time',
            markers=True,
            title="Tempo Médio de Resposta por Dia"
        )
        
        fig_response.update_layout(
            xaxis_title="Data",
            yaxis_title="Tempo (ms)",
            height=400
        )
        
        fig_response.update_traces(
            line_color='#FF9800',
            marker=dict(size=8)
        )
        
        st.plotly_chart(fig_response, use_container_width=True)

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    💡 As métricas são atualizadas em tempo real conforme você usa o assistente
</div>
""", unsafe_allow_html=True)