import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import gspread
from google.oauth2.service_account import Credentials

# Configuração da Página
st.set_page_config(page_title="Diário de Obras ITON", page_icon="🏗️", layout="wide")

# ==========================================
# 1. SISTEMA DE LOGIN COM NÍVEIS DE ACESSO
# ==========================================
USUARIOS = {
    "lucas": {"senha": "123", "nome": "Lucas (Admin)", "papel": "admin"},
    "lider1": {"senha": "123", "nome": "Líder Toyota", "papel": "lider"},
    "lider2": {"senha": "123", "nome": "Líder Unilever", "papel": "lider"}
}

def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🏗️ Acesso ao Diário de Obras</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", use_container_width=True):
                if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                    st.session_state["logged_in"] = True
                    st.session_state["usuario_atual"] = usuario
                    st.session_state["nome_usuario"] = USUARIOS[usuario]["nome"]
                    st.session_state["papel_usuario"] = USUARIOS[usuario]["papel"]
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
        # Pega a chave que escondemos lá no painel do Streamlit
        credenciais_dict = json.loads(st.secrets["google_credentials"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(credenciais_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo link direto para evitar o erro 200
        planilha = client.open_by_url("https://docs.google.com/spreadsheets/d/1IprM-oJyFe7JQ2CP_OeJuv4LJc3ADRLs/edit?gid=1455764483#gid=1455764483").sheet1
        return planilha
    except Exception as e:
        st.error(f"Erro ao conectar com o Google: {e}")
        st.stop()

planilha_google = conectar_google()

# ==========================================
# 3. CABEÇALHO
# ==========================================
col_titulo, col_user = st.columns([3, 1])
with col_titulo:
    st.title("Lançamento - Diário de Obras")
with col_user:
    st.write(f"👤 Logado como: **{st.session_state['nome_usuario']}**")
    if st.button("Sair (Logout)"):
        st.session_state["logged_in"] = False
        st.rerun()

st.divider()

# ==========================================
# LISTAS DE DADOS
# ==========================================
LISTA_OBRAS = [
    "Toyota - Prensa", "Toyota - Pintura", "Toyota - Outros",
    "Unilever - Aguaí", "Unilever - Vinhedo", "Unilever - Betim",
    "Suspensys"
]
LISTA_COLABORADORES = ["Jorge", "Carlos Silva", "João Pedro", "Marcos Antônio", "Francisco Damásio", "Lucas Biazoto"]
LISTA_COLABORADORES.sort()

# ==========================================
# 4. CRIAÇÃO DAS ABAS
# ==========================================
if st.session_state["papel_usuario"] == "admin":
    aba_lancamento, aba_relatorios = st.tabs(["📝 Novo Lançamento", "📊 Relatórios e Filtros (Admin)"])
else:
    aba_lancamento, aba_relatorios = st.tabs(["📝 Novo Lançamento", "🔒 Área Restrita"])

# ABA DE LANÇAMENTO (Todos veem)
with aba_lancamento:
    st.markdown("### Preencha as informações do dia")
    
    col1, col2 = st.columns(2)
    with col1:
        data_obra = st.date_input("📅 Data da Atividade")
        obra_selecionada = st.selectbox("🏗️ Selecione a Obra:", LISTA_OBRAS)
        colaboradores_selecionados = st.multiselect("👷 Equipe Presente (Selecione todos):", LISTA_COLABORADORES)
    
    with col2:
        hora_inicio = st.time_input("⏰ Horário de Início", value=datetime.strptime('07:00', '%H:%M').time())
        hora_fim = st.time_input("⏰ Horário de Término", value=datetime.strptime('17:00', '%H:%M').time())
        observacao = st.text_area("📝 Observações (Faltas, atrasos, ocorrências):")

    if st.button("✅ Registrar Diário de Obra na Nuvem", type="primary", use_container_width=True):
        if not colaboradores_selecionados:
            st.error("⚠️ Você precisa selecionar pelo menos um colaborador!")
        else:
            with st.spinner('Salvando no Google Drive...'):
                t1 = datetime.combine(date.today(), hora_inicio)
                t2 = datetime.combine(date.today(), hora_fim)
                
                if t2 < t1: t2 += timedelta(days=1)
                    
                diferenca = t2 - t1
                horas_totais = diferenca.total_seconds() / 3600
                
                if horas_totais > 4: hgt = horas_totais - 1.0
                else: hgt = horas_totais

                # Prepara a linha para o Excel (Apenas valores, nada de CSV local)
                nova_linha = [
                    data_obra.strftime("%d/%m/%Y"),
                    st.session_state["nome_usuario"],
                    obra_selecionada,
                    ", ".join(colaboradores_selecionados),
                    hora_inicio.strftime("%H:%M"),
                    hora_fim.strftime("%H:%M"),
                    round(horas_totais, 2),
                    round(hgt, 2),
                    observacao
                ]

                # INSERE DIRETAMENTE NO GOOGLE SHEETS
                planilha_google.append_row(nova_linha)
                
                st.success(f"Diário salvo com sucesso no Google Drive! {len(colaboradores_selecionados)} pessoas registradas.")

# ABA DE RELATÓRIOS (Admin)
with aba_relatorios:
    if st.session_state["papel_usuario"] != "admin":
        st.warning("⚠️ O acesso aos relatórios consolidados é restrito ao Administrador.")
    else:
        st.markdown("### 🔍 Histórico Direto do Google Drive")
        
        if st.button("🔄 Atualizar Dados do Drive"):
            st.cache_resource.clear()
            st.rerun()

        # Puxa os dados ao vivo da planilha
        dados_nuvem = planilha_google.get_all_records()
        
        if not dados_nuvem:
            st.info("A planilha do Google ainda está vazia.")
        else:
            df = pd.DataFrame(dados_nuvem)
            df['Data_Real'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
            
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                filtro_obra = st.selectbox("Filtrar por Obra:", ["Todas as Obras"] + LISTA_OBRAS)
            with f_col2:
                filtro_nome = st.selectbox("Pesquisar Colaborador:", ["Todos"] + LISTA_COLABORADORES)
            with f_col3:
                data_min = df['Data_Real'].min().date()
                data_max = df['Data_Real'].max().date()
                filtro_datas = st.date_input("Período:", [data_min, data_max])

            df_filtrado = df.copy()
            if filtro_obra != "Todas as Obras":
                df_filtrado = df_filtrado[df_filtrado['Obra'] == filtro_obra]
            if filtro_nome != "Todos":
                df_filtrado = df_filtrado[df_filtrado['Colaboradores'].astype(str).str.contains(filtro_nome, na=False)]
            if len(filtro_datas) == 2:
                df_filtrado = df_filtrado[(df_filtrado['Data_Real'].dt.date >= filtro_datas[0]) & (df_filtrado['Data_Real'].dt.date <= filtro_datas[1])]

            df_filtrado = df_filtrado.drop(columns=['Data_Real'])

            st.divider()
            st.markdown(f"**Resultados Encontrados:** {len(df_filtrado)} registros")
            st.dataframe(df_filtrado, use_container_width=True)

            # Usa pd.to_numeric para garantir que os valores lidos da planilha sejam somados como números
            total_hgt = pd.to_numeric(df_filtrado['HGT'].replace(',', '.', regex=True), errors='coerce').sum()
            st.metric("⏱️ Total de Horas HGT Filtradas", f"{total_hgt} horas")
