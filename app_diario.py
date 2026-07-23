import streamlit as st
from datetime import datetime, date, timedelta
import json
import gspread
from google.oauth2.service_account import Credentials
import traceback

# Configuração da Página para ficar bem limpa e intuitiva
st.set_page_config(page_title="Lançamento de Diário - ITON", page_icon="🏗️", layout="centered")

# ==========================================
# 1. SISTEMA DE LOGIN (LÍDERES CONFIGURADOS)
# ==========================================
USUARIOS = {
    "lucas": {"senha": "123", "nome": "Lucas Biazoto (Admin)", "papel": "admin"},
    "kauai": {"senha": "123", "nome": "Kauai Darlei dos Santos Vieira", "papel": "lider"},
    "diego": {"senha": "123", "nome": "Diego de Faria Santos", "papel": "lider"},
    "jefferson": {"senha": "123", "nome": "Jefferson Santos Nascimento", "papel": "lider"},
    "gilberto": {"senha": "123", "nome": "Gilberto Bento de Souza Santos", "papel": "lider"}
}

def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center; color: #172333;'>🏗️ Diário de Obras - ITON</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Faça o login para registrar a diária da sua equipe.</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            usuario = st.text_input("👤 Usuário (Seu primeiro nome)", key="login_user").lower().strip()
            senha = st.text_input("🔑 Senha", type="password", key="login_pass")
            
            if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
                if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                    st.session_state["logged_in"] = True
                    st.session_state["usuario_atual"] = usuario
                    st.session_state["nome_usuario"] = USUARIOS[usuario]["nome"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 2. CONEXÃO COM O GOOGLE SHEETS
# ==========================================
def conectar_google():
    try:
        credenciais_dict = json.loads(st.secrets["google_credentials"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(credenciais_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # ⚠️ LINK MANTIDO EXATAMENTE IGUAL AO QUE FUNCIONOU PRA VOCÊ
        LINK_DA_PLANILHA = "https://docs.google.com/spreadsheets/d/1oI9pPGXngdE1jrOaQGIRhHMfLnt_Evh9tN_9lQkLaOU/edit?gid=1342849862#gid=1342849862"
        NOME_DA_ABA = "DIÁRIO DE OBRA "
        
        documento = client.open_by_url(LINK_DA_PLANILHA)
        planilha = documento.worksheet(NOME_DA_ABA)
        
        return planilha
    except Exception as e:
        st.error("🚨 Ocorreu um erro fatal ao tentar conectar com o Google.")
        st.write("Causa exata do erro encontrada pelo sistema:")
        st.code(traceback.format_exc(), language="python")
        st.stop()

planilha_google = conectar_google()

# ==========================================
# LISTAS DE DADOS (Oficiais)
# ==========================================
LISTA_OBRAS = [
    "Unilever Aguaí", "Unilever Vinhedo", "PRIMAX - PRENSA", 
    "PRIMAX - PINTURA", "MAX TEC - PRENSA", "PRIMAX - VUTEQ", 
    "PRIMAX - SUSPENSYS", "PRIMAX - TENDA", "PRIMAX - RESINA", "PRIMAX - RECKITT"
]

LISTA_COLABORADORES = [
    "Danilo Alves de Oliveira", "Diego de Faria Santos", "Diego Sergio Simão", 
    "Evane Jacinto Pacheco", "Flavio Mateus", "Francisco Damazio Moraes", 
    "Hebert Deivison Silveira Pereira", "Jeferson Miranda do Cabo", 
    "Jefferson Santos Nascimento", "Jonathan Araújo Mendonça", 
    "Jorge Esbrisse Martins", "Kauai Darlei dos Santos Vieira", 
    "Marco Aurelio Jesus da Costa", "Paulo Cesar de Souza", "Rafael Damaciano", 
    "Robinson William dos Santos Machado", "Kauã Rodrigues Roza", "Niuleno Alves de Souza"
]
LISTA_COLABORADORES.sort() # Deixa sempre em ordem alfabética automaticamente

# ==========================================
# 3. INTERFACE DE LANÇAMENTO (Nível Criança)
# ==========================================
col_titulo, col_user = st.columns([3, 1])
with col_titulo:
    st.header("📝 Lançamento Diário")
with col_user:
    st.write(f"👤 **{st.session_state['nome_usuario'].split()[0]}**") # Mostra só o primeiro nome
    if st.button("Sair"):
        st.session_state["logged_in"] = False
        st.rerun()

st.divider()

# Formulário super simples e direto
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        data_obra = st.date_input("📅 1. Data do Serviço")
        obra_selecionada = st.selectbox("🏗️ 2. Cliente / Obra:", ["Selecione..."] + LISTA_OBRAS)
        colaboradores_selecionados = st.multiselect("👷 3. Equipe Presente (Selecione todos):", LISTA_COLABORADORES)
        
    with col2:
        hora_inicio = st.time_input("⏰ 4. Horário de Início:", value=datetime.strptime('07:00', '%H:%M').time())
        hora_fim = st.time_input("⏰ 5. Horário de Término:", value=datetime.strptime('17:00', '%H:%M').time())
        observacao = st.text_area("📝 6. Observação (Faltas, atrasos, etc):", value="")
        
    if observacao.strip() == "":
        observacao = "-" # Evita que a célula fique vazia no Excel

    st.divider()

    # Botão Gigante de Enviar
    if st.button("🚀 ENVIAR DIÁRIO PARA A NUVEM", type="primary", use_container_width=True):
        if obra_selecionada == "Selecione...":
            st.error("⚠️ Por favor, selecione qual é a Obra.")
        elif not colaboradores_selecionados:
            st.error("⚠️ Por favor, selecione pelo menos um colaborador na equipe.")
        else:
            with st.spinner('Salvando diretamente no Google Drive... Por favor, aguarde.'):
                
                # Cálculos de tempo
                t1 = datetime.combine(date.today(), hora_inicio)
                t2 = datetime.combine(date.today(), hora_fim)
                
                if t2 < t1: t2 += timedelta(days=1)
                    
                diferenca = t2 - t1
                horas_totais = diferenca.total_seconds() / 3600
                
                if horas_totais > 4: 
                    hgt = horas_totais - 1.0
                else: 
                    hgt = horas_totais

                # Prepara os dados EXATAMENTE na ordem das 10 colunas antigas
                linhas_para_adicionar = []
                data_formatada = data_obra.strftime("%d/%m/%Y")
                carimbo_agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                hora_inicio_str = hora_inicio.strftime("%H:%M")
                hora_fim_str = hora_fim.strftime("%H:%M")
                horas_totais_str = str(round(horas_totais, 2)).replace('.', ',')
                hgt_str = str(round(hgt, 2)).replace('.', ',')
                
                for colaborador in colaboradores_selecionados:
                    nova_linha = [
                        carimbo_agora,                    # Col 1: Carimbo
                        data_formatada,
