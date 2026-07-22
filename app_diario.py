import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta

# Configuração da Página
st.set_page_config(page_title="Diário de Obras ITON", page_icon="🏗️", layout="wide")

# ==========================================
# 1. SISTEMA DE LOGIN COM NÍVEIS DE ACESSO
# ==========================================
# Aqui você cadastra quem pode entrar. 'papel' define o que a pessoa pode ver.
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
# 2. BANCO DE DADOS
# ==========================================
ARQUIVO_DADOS = "historico_diario_obras.csv"

@st.cache_data(ttl=0)
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        return pd.read_csv(ARQUIVO_DADOS, sep=';', encoding='utf-8')
    else:
        return pd.DataFrame(columns=[
            "Data", "Supervisor", "Obra", "Colaboradores", 
            "Hora Início", "Hora Término", "Horas Totais", "HGT (Sem Almoço)", "Observação"
        ])

if 'banco_diario' not in st.session_state:
    st.session_state['banco_diario'] = carregar_dados()

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
LISTA_COLABORADORES = ["Jorge", "Carlos Silva", "João Pedro", "Marcos Antônio", "Francisco Damásio"]
LISTA_COLABORADORES.sort()

# ==========================================
# 4. CRIAÇÃO DAS ABAS (Admin vê duas, Líder vê uma)
# ==========================================
if st.session_state["papel_usuario"] == "admin":
    aba_lancamento, aba_relatorios = st.tabs(["📝 Novo Lançamento", "📊 Relatórios e Filtros (Admin)"])
else:
    aba_lancamento, aba_relatorios = st.tabs(["📝 Novo Lançamento", "🔒 Área Restrita"]), None

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

    # Botão de Salvar e Cálculos
    if st.button("✅ Registrar Diário de Obra", type="primary", use_container_width=True):
        if not colaboradores_selecionados:
            st.error("⚠️ Você precisa selecionar pelo menos um colaborador!")
        else:
            # Lógica para calcular a diferença de horas
            t1 = datetime.combine(date.today(), hora_inicio)
            t2 = datetime.combine(date.today(), hora_fim)
            
            # Se passou da meia noite, adiciona 1 dia no t2
            if t2 < t1:
                t2 += timedelta(days=1)
                
            diferenca = t2 - t1
            horas_totais = diferenca.total_seconds() / 3600
            
            # HGT = Horas Totais - 1 hora de almoço. (Se trabalhou menos de 4h, não desconta almoço)
            if horas_totais > 4:
                hgt = horas_totais - 1.0
            else:
                hgt = horas_totais

            # Salvar no banco
            novo_registro = pd.DataFrame([{
                "Data": data_obra.strftime("%d/%m/%Y"),
                "Supervisor": st.session_state["nome_usuario"],
                "Obra": obra_selecionada,
                "Colaboradores": ", ".join(colaboradores_selecionados),
                "Hora Início": hora_inicio.strftime("%H:%M"),
                "Hora Término": hora_fim.strftime("%H:%M"),
                "Horas Totais": round(horas_totais, 2),
                "HGT (Sem Almoço)": round(hgt, 2),
                "Observação": observacao
            }])

            st.session_state['banco_diario'] = pd.concat([st.session_state['banco_diario'], novo_registro], ignore_index=True)
            st.session_state['banco_diario'].to_csv(ARQUIVO_DADOS, sep=';', index=False, encoding='utf-8')
            
            st.success(f"Diário salvo! Foram geradas {round(hgt, 2)} horas (HGT) para {len(colaboradores_selecionados)} pessoas.")

# ABA DE RELATÓRIOS (Somente o Admin, que é o Lucas, consegue ver isso e fazer os filtros)
if aba_relatorios:
    with aba_relatorios:
        if st.session_state["papel_usuario"] != "admin":
            st.warning("Você não tem acesso a esta área.")
        else:
            st.markdown("### 🔍 Filtros Avançados de Horas Trabalhadas")
            df = st.session_state['banco_diario'].copy()

            if df.empty:
                st.info("Nenhum diário registrado ainda.")
            else:
                # Converte a coluna Data para formato de data real para poder filtrar
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

                # Aplica os filtros
                df_filtrado = df.copy()
                if filtro_obra != "Todas as Obras":
                    df_filtrado = df_filtrado[df_filtrado['Obra'] == filtro_obra]
                
                if filtro_nome != "Todos":
                    # Procura se o nome está dentro da lista de nomes salvos na linha
                    df_filtrado = df_filtrado[df_filtrado['Colaboradores'].str.contains(filtro_nome, na=False)]
                
                if len(filtro_datas) == 2:
                    df_filtrado = df_filtrado[(df_filtrado['Data_Real'].dt.date >= filtro_datas[0]) & (df_filtrado['Data_Real'].dt.date <= filtro_datas[1])]

                # Remove a coluna temporária de data real
                df_filtrado = df_filtrado.drop(columns=['Data_Real'])

                # Mostra Resultados
                st.divider()
                st.markdown(f"**Resultados Encontrados:** {len(df_filtrado)} registros")
                st.dataframe(df_filtrado, use_container_width=True)

                total_hgt = df_filtrado['HGT (Sem Almoço)'].sum()
                st.metric("⏱️ Total de Horas HGT no período filtrado", f"{total_hgt} horas")

                csv_diario = df_filtrado.to_csv(sep=';', index=False, encoding='utf-8')
                st.download_button("📥 Baixar Relatório (Excel)", data=csv_diario, file_name="relatorio_diario_obras.csv", mime="text/csv")
