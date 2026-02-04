import streamlit as st
import pandas as pd
import json
import os
import textwrap
from datetime import datetime, timedelta
import plotly.express as px
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Painel Aroeira", layout="wide")

# --- CONTROLE DE ROTAÇÃO ---
# Atualiza a cada 10 segundos
count = st_autorefresh(interval=10000, key="datarefresh")

# --- CORES E LISTAS ---
COR_AROEIRA = "#2E7D32" 
COR_AROEIRA_CLARO = "#E8F5E9" 
COR_OCUPADO = "#D32F2F" 
COR_OCUPADO_CLARO = "#FFEBEE" 
COR_FUNDO = "#F5F7F8" 
LISTA_TODAS_SALAS = ["Sala ADM 01", "Sala ADM 02", "Sala ADM 03", "Sala ADM 04"]

index_sala = count % len(LISTA_TODAS_SALAS)
SALA_EM_FOCO = LISTA_TODAS_SALAS[index_sala]

# --- CSS (MANTIDO O ESTILO GIGANTE) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800;900&display=swap');

    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100%;
    }}
    
    .stApp {{ background-color: {COR_FUNDO}; }}
    #MainMenu, header, footer {{visibility: hidden;}}

    /* TÍTULO PRINCIPAL */
    .titulo-principal {{
        font-family: 'Montserrat', sans-serif;
        font-size: 48px; 
        font-weight: 900;
        color: {COR_AROEIRA};
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }}

    /* CARDS SUPERIORES */
    .card-container-outer {{
        background: transparent;
        padding: 5px;
        border-radius: 24px;
        height: 580px;
    }}

    .card-statico-inner {{
        background: white;
        border-radius: 20px;
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
        box-shadow: 0 10px 20px rgba(0,0,0,0.08);
    }}
    
    /* CABEÇALHO DO CARD */
    .card-header-status {{
        height: 140px; 
        text-align: center;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0px; 
    }}

    /* NOME DA SALA - GIGANTE (100px) */
    .card-titulo-grande {{
        font-family: 'Montserrat', sans-serif !important;
        font-size: 100px !important; 
        font-weight: 900 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.0 !important; 
        text-transform: uppercase;
        white-space: nowrap; 
    }}

    .card-body-content {{
        padding: 15px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: flex-start; 
        align-items: center;
    }}
    
    /* STATUS (LIVRE/OCUPADO) */
    .status-texto-zao {{
        font-family: 'Montserrat', sans-serif;
        font-size: 28px; 
        font-weight: 800;
        margin-bottom: 10px;
        text-align: center;
        margin-top: 15px;
    }}
    
    /* BOX DE SUGESTÕES */
    .sugestao-box-estilizada {{
        font-family: 'Montserrat', sans-serif;
        font-size: 34px; 
        color: #333;
        font-weight: 800;
        background-color: #f0f2f5;
        padding: 15px;
        border-radius: 15px;
        width: 100%;
        text-align: center;
        border-left: 10px solid {COR_AROEIRA};
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        line-height: 1.3;
    }}

    .titulo-vagas {{
        font-size: 18px;
        color: #555;
        text-transform: uppercase;
        margin-bottom: 5px;
        font-weight: 900;
    }}

    /* TÍTULO DA GRADE DE FOCO */
    .titulo-grade-foco {{
        font-family: 'Montserrat', sans-serif;
        font-size: 40px;
        color: #333;
        text-align: left;
        font-weight: 800;
        padding: 15px 30px;
        border-left: 15px solid {COR_AROEIRA};
        margin-top: 20px;
        margin-bottom: 20px;
        background: white;
        border-radius: 0 25px 25px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        display: inline-block;
    }}
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def carregar_dados():
    # SEU CAMINHO MANTIDO
    caminho_arquivo = r"C:\Users\arthurarantes\OneDrive - Bioenergética Aroeira\Área de trabalho Arthur TI\base aplicativo painel de voo\dados_reuniao.json"
    df_base = pd.DataFrame({"SALA": LISTA_TODAS_SALAS})

    if not os.path.exists(caminho_arquivo): 
        return df_base

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        if isinstance(content, dict): content = [content]
        if not content: return df_base

        df = pd.DataFrame(content)
        df = df.rename(columns={"Sala": "SALA_RAW", "HorárioInício": "Inicio", "HorárioFim": "Fim", "Organizador": "Organizador"})

        def limpar_nome_sala(nome):
            if not nome: return "Indefinida"
            nome_limpo = nome.split(";")[-1].strip()
            nome_limpo = nome_limpo.replace("Calendar - ", "").replace("Sala de Reunião", "Sala")
            return nome_limpo

        df['SALA'] = df['SALA_RAW'].apply(limpar_nome_sala)
        df['Inicio'] = pd.to_datetime(df['Inicio'])
        df['Fim'] = pd.to_datetime(df['Fim'])
        
        df['Inicio'] = df['Inicio'].dt.tz_localize(None) - timedelta(hours=3)
        df['Fim'] = df['Fim'].dt.tz_localize(None) - timedelta(hours=3)

        df['Nome_Original'] = df['Organizador'].apply(lambda x: x.split('@')[0].title() if x else "Reservado")
        
        df['Duracao_Minutos'] = (df['Fim'] - df['Inicio']).dt.total_seconds() / 60

        def formatar_label(row):
            nome = row['Nome_Original']
            duracao = row['Duracao_Minutos']
            if duracao < 15:
                return nome[:10] + "."
            return "<br>".join(textwrap.wrap(nome, width=12))

        df['Label_Final'] = df.apply(formatar_label, axis=1)
        
        return pd.merge(df_base, df, on="SALA", how="left")
    except Exception:
        return df_base

# --- LÓGICA SIMPLIFICADA (Top 3 Vagas) ---
def obter_proximas_3_vagas(df_sala, agora):
    fim_expediente = agora.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # Se já passou das 17h, manda voltar amanhã
    limite_mensagem = agora.replace(hour=17, minute=0, second=0, microsecond=0)
    if agora >= limite_mensagem: 
        return "Volte amanhã<br>para mais vagas"

    reunioes = df_sala[df_sala['Fim'] > agora].sort_values('Inicio')
    lista_vagas = []
    cursor_tempo = agora
    
    for _, row in reunioes.iterrows():
        inicio_reuniao = row['Inicio']
        if inicio_reuniao > cursor_tempo:
            gap_minutos = (inicio_reuniao - cursor_tempo).total_seconds() / 60
            if gap_minutos >= 15:
                inicio_str = cursor_tempo.strftime('%H:%M')
                fim_str = inicio_reuniao.strftime('%H:%M')
                lista_vagas.append(f"{inicio_str} às {fim_str}")
        cursor_tempo = max(cursor_tempo, row['Fim'])

    if cursor_tempo < fim_expediente:
        gap_final = (fim_expediente - cursor_tempo).total_seconds() / 60
        if gap_final >= 15:
            inicio_str = cursor_tempo.strftime('%H:%M')
            fim_str = fim_expediente.strftime('%H:%M')
            lista_vagas.append(f"{inicio_str} às {fim_str}")

    if not lista_vagas:
        return "Volte amanhã<br>para mais vagas"

    # Retorna APENAS AS 3 PRIMEIRAS (Sem rotação, evita erro JS)
    return "<br>".join(lista_vagas[:3])

df = carregar_dados()
agora = datetime.now()

# --- HEADER ---
# Garante que o Python procure a logo na mesma pasta do script
pasta_script = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(pasta_script, "logo_nova.png")

col1, col2, col3 = st.columns([1.5, 6, 1.5])
with col1:
    # Tenta carregar a logo do caminho relativo correto
    if os.path.exists(caminho_logo):
        st.image(caminho_logo, width=180)
    else:
        st.write("")
        
with col2:
    st.markdown('<div class="titulo-principal">PAINEL DE SALAS</div>', unsafe_allow_html=True)
with col3:
    hora_formatada = agora.strftime("%H:%M")
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
        <div style="font-size: 65px; font-weight: 900; color: #333; font-family: 'Montserrat', sans-serif; letter-spacing: 2px;">
            {hora_formatada}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 1. PARTE SUPERIOR: CARDS ESTÁTICOS
if not df.empty:
    cols_static = st.columns(len(LISTA_TODAS_SALAS), gap="medium")
    
    for i, sala in enumerate(LISTA_TODAS_SALAS):
        df_sala = df[df['SALA'] == sala].dropna(subset=['Inicio'])
        
        status_texto = "LIVRE"
        ocupado_ate = ""
        for _, row in df_sala.iterrows():
            if row['Inicio'] <= agora <= row['Fim']:
                status_texto = "OCUPADO"
                ocupado_ate = row['Fim'].strftime('%H:%M')
                break
        
        texto_vagas = obter_proximas_3_vagas(df_sala, agora)

        if status_texto == "LIVRE":
            bg_header = COR_AROEIRA
            txt_header = "white"
            txt_status = COR_AROEIRA
            ico_status = "🟢 DISPONÍVEL"
        else:
            bg_header = COR_OCUPADO
            txt_header = "white"
            txt_status = COR_OCUPADO
            ico_status = f"🔴 ATÉ {ocupado_ate}"

        if sala == SALA_EM_FOCO:
            container_style = f"border: 4px solid {COR_AROEIRA}; transform: scale(1.03); box-shadow: 0 15px 35px rgba(46, 125, 50, 0.4);"
        else:
            container_style = "border: 1px solid transparent;"

        nome_curto = sala.replace('Sala ', '').replace('ADM ', 'ADM ')

        with cols_static[i]:
            st.markdown(f"""
            <div class="card-container-outer" style="{container_style}">
                <div class="card-statico-inner">
                    <div class="card-header-status" style="background-color: {bg_header};">
                        <p class="card-titulo-grande" style="color: {txt_header};">{nome_curto}</p>
                    </div>
                    <div class="card-body-content">
                        <div class="status-texto-zao" style="color: {txt_status};">
                            {ico_status}
                        </div>
                        <div class="sugestao-box-estilizada">
                            <div class="titulo-vagas">Vagas Disponíveis:</div>
                            {texto_vagas}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# 2. PARTE INFERIOR: GRADE ROTATIVA (GANTT)
if not df.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    
    df_foco = df[df['SALA'] == SALA_EM_FOCO].dropna(subset=['Inicio'])
    
    st.markdown(f'<div class="titulo-grade-foco">AGENDA HOJE: {SALA_EM_FOCO.upper()}</div>', unsafe_allow_html=True)

    inicio_dia = agora.replace(hour=7, minute=0, second=0, microsecond=0)
    fim_dia = agora.replace(hour=17, minute=15, second=0, microsecond=0)

    # --- NOVAS CORES APLICADAS AQUI ---
    mapa_cores = {
        "Sala ADM 01": "#011826", # Azul marinho
        "Sala ADM 02": "#03A6A6", # Turquesa
        "Sala ADM 03": "#025959", # Verde azulado
        "Sala ADM 04": "#025940"  # Verde floresta
    }

    if not df_foco.empty:
        fig = px.timeline(
            df_foco, x_start="Inicio", x_end="Fim", y="SALA", 
            color="SALA", text="Label_Final", color_discrete_map=mapa_cores,
            height=450 
        )

        fig.update_layout(
            plot_bgcolor='rgba(255, 255, 255, 0.5)', 
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=0),
            xaxis=dict(
                title="", 
                tickformat="%H:%M", 
                side="top", 
                range=[inicio_dia, fim_dia], 
                tickmode="linear", 
                tick0=inicio_dia,  
                dtick=3600000,     
                showgrid=True, 
                gridcolor="#BDBDBD",
                gridwidth=1,
                griddash="dot", 
                tickfont=dict(size=26, family="Montserrat", weight="bold", color="#555"),
                layer="below traces"
            ),
            yaxis=dict(visible=False)
        )

        fig.update_traces(
            marker_line_color='white', 
            marker_line_width=3, 
            opacity=1,
            textposition='inside', 
            insidetextanchor='middle',
            textangle=0, 
            constraintext='none',
            textfont=dict(size=28, family="Montserrat", weight="bold", color="white")
        )

        fig.add_vline(x=agora, line_width=4, line_color="#D32F2F", line_dash="dot", opacity=0.9) 
        st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
    
    else:
        st.markdown(f"""
        <div style="background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
            <h2 style="font-family: 'Montserrat'; color: {COR_AROEIRA}; font-weight: 800; font-size: 35px;">
                🎉 Agenda Livre!
            </h2>
            <p style="font-family: 'Montserrat'; font-size: 24px; color: #666;">
                Nenhuma reunião agendada para a <strong>{SALA_EM_FOCO}</strong> entre 07:00 e 17:00.
            </p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("Carregando dados...")