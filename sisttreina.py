import streamlit as st
import psycopg2
import pandas as pd
import base64
from datetime import date, datetime, timedelta

# CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Gestão de Treinamentos - Harman 2026",
    page_icon="🎯",
    layout="wide"
)

# ==================================================
# CONFIGURAÇÃO DE IMAGENS AND LOGOS
# ==================================================
URL_LOGO_HARMAN = "https://cdn.freelogovectors.net/wp-content/uploads/2020/03/harman-logo.png"

# Estilização Pura (Sem f-string) para garantir estabilidade absoluta do CSS e do Menu Lateral
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
div[data-testid="stDecoration"] {display: none;}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

.main { background-color: #F4F7FA; }
[data-testid="stSidebar"] { background-color:#0A2D62; }
[data-testid="stSidebar"] * { color:white; }
[data-testid="stAppViewBlockContainer"] { opacity: 1 !important; }
div[data-testid="stBlock"] { opacity: 1 !important; }

.metric-container {
    background-color: white !important;
    padding: 20px 15px;
    border-radius: 10px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    border: 1px solid #E0E0E0;
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-bottom: 15px;
}
.metric-title { color: #555555 !important; font-size: 14px; font-weight: 500; margin-bottom: 5px; }
.metric-value { color: #0A2D62 !important; font-size: 28px; font-weight: bold; }
h1, h2, h3 { color:#0A2D62; }

@media (max-width: 768px) {
    div[data-testid="stColumn"] img {
        max-width: 140px !important;
        height: auto !important;
        display: block;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-bottom: 10px;
    }
    div[data-testid="stColumn"] {
        text-align: center !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Botão para limpeza manual da memória do servidor
if st.sidebar.button("♻️ Limpar Cache e Forçar Reinício"):
    st.cache_resource.clear()
    st.rerun()

# =========================
# CONEXÃO COM BANCO EM NUVEM (POSTGRESQL)
# =========================
@st.cache_resource(ttl=60)
def conectar_nuvem():
    try:
        cfg = st.secrets["postgres"]
        conexao = psycopg2.connect(
            host=cfg["host"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            port=int(cfg["port"])
        )
        conexao.autocommit = True
        return conexao
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        st.stop()

try:
    conn = conectar_nuvem()
    with conn.cursor() as t_cur:
        t_cur.execute("SELECT 1;")
except Exception:
    st.cache_resource.clear()
    conn = conectar_nuvem()

def inicializar_banco(conexao):
    queries = [
        """CREATE TABLE IF NOT EXISTS cursos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) UNIQUE,
            saldo_contratado INTEGER DEFAULT 0,
            alunos_realizados INTEGER DEFAULT 0,
            responsavel_tecnico VARCHAR(100) DEFAULT ''
        );""",
        """CREATE TABLE IF NOT EXISTS turmas (
            id SERIAL PRIMARY KEY,
            data DATE,
            cliente VARCHAR(100),
            curso VARCHAR(100),
            instrutor VARCHAR(100),
            alunos INTEGER,
            status VARCHAR(50)
        );""",
        """CREATE TABLE IF NOT EXISTS movimentacoes (
            id SERIAL PRIMARY KEY,
            data DATE,
            curso VARCHAR(100),
            tipo VARCHAR(50),
            quantidade INTEGER,
            observacao TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS colaboradores (
            matricula VARCHAR(50) PRIMARY KEY,
            nome_completo VARCHAR(150),
            funcao VARCHAR(100),
            divisao_codigo VARCHAR(10),
            divisao_nome VARCHAR(50)
        );"""
    ]
    for q in queries:
        try:
            with conexao.cursor() as cur:
                cur.execute(q)
        except Exception:
            pass

    try:
        with conexao.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cursos;")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO cursos (nome, saldo_contratado, responsavel_tecnico) VALUES ('NR12', 0, 'MultiTech'), ('Normas Técnicas de Solda', 0, 'MultiTech');")
    except Exception:
        pass

inicializar_banco(conn)

lista_cursos_banco = []
try:
    with conn.cursor() as cursor_limpo:
        cursor_limpo.execute("SELECT nome FROM cursos ORDER BY nome;")
        lista_cursos_banco = [row[0] for row in cursor_limpo.fetchall()]
except Exception:
    pass

# ==================================================
# BARRA LATERAL (MENU SIDEBAR COM SELETOR DE OPÇÕES)
# ==================================================
with st.sidebar:
    st.markdown("<p style='text-align: center; font-size: 11px; color: #BACAD6; letter-spacing: 1px;'>PARCERIA COMERCIAL</p>", unsafe_allow_html=True)
    
    # Exibe a logo diretamente usando o Streamlit de forma limpa e nativa
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        pass
        
    st.markdown("<br>", unsafe_allow_html=True)
    menu = st.radio("Menu de Navegação", ["Dashboard", "Agendar Turma", "Controle de Saldo", "Gerenciar Alunos", "Histórico e Reciclagens"])

# Cabeçalho principal com as logos alinhadas nas pontas de forma nativa e responsiva
head_col1, head_col2, head_col3 = st.columns([1, 4, 1.2])
with head_col1: 
    try:
        st.image("logo.png", width=110)
    except Exception:
        pass
with head_col2:
    st.title("Sistema de Gestão de Treinamentos")
    st.caption("MultiTech Treinamentos Industriais — Cliente: Harman")
with head_col3:
    try:
        st.image(URL_LOGO_HARMAN, use_container_width=True)
    except Exception:
        pass
st.markdown("<br>", unsafe_allow_html=True)

# ==================================================
# DASHBOARD
# ==================================================
if menu == "Dashboard":
    try:
        cursos = pd.read_sql("SELECT * FROM cursos", conn)
        cursos["saldo_atual"] = cursos["saldo_contratado"] - cursos["alunos_realizados"]
        total_alunos = cursos["alunos_realizados"].sum()
        saldo_geral = cursos["saldo_atual"].sum()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM turmas;")
            total_turmas = cur.fetchone()[0]
    except Exception:
        cursos = pd.DataFrame(columns=["nome", "saldo_contratado", "alunos_realizados", "saldo_atual"])
        total_alunos, saldo_geral, total_turmas = 0, 0, 0

    c1, c2, c3, c4 = st.columns(4)
    metricas_dados = [
        {"col": c1, "titulo": "Cursos Ativos", "valor": str(len(cursos))},
        {"col": c2, "titulo": "Turmas Mapeadas", "valor": str(total_turmas)},
        {"col": c3, "titulo": "Alunos Treinados", "valor": str(int(total_alunos))},
        {"col": c4, "titulo": "Saldo Geral Consolidado", "valor": f"{int(saldo_geral)} vagas"}
    ]
    for item in metricas_dados:
        with item["col"]:
            st.markdown(f'<div class="metric-container"><div class="metric-title">{item["titulo"]}</div><div class="metric-value">{item["valor"]}</div></div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Resumo de Saldos Oficiais por Curso")
    if not cursos.empty:
        df_dashboard = cursos[["nome", "saldo_contratado", "alunos_realizados", "saldo_atual"]].copy()
        df_dashboard.columns = ["Nome do Curso", "Saldo Contratado", "Alunos Realizados", "Saldo Atual"]
        st.dataframe(df_dashboard, use_container_width=True, hide_index=True)
        negativos = cursos[cursos["saldo_atual"] < 0]
        for _, row in negativos.iterrows():
            st.error(f"Atenção: O curso {row['nome']} está com saldo negativo ({row['saldo_atual']} vagas). Necessita de nova recarga urgente!")
    else:
        st.info("Nenhum dado encontrado ou banco a sincronizar.")

# ==================================================
# AGENDAR TURMA
# ==================================================
elif menu == "Agendar Turma":
    st.subheader("Nova Turma")
    data = st.date_input("Data", date.today())
    cliente = st.text_input("Cliente", value="Harman")
    instrutor = st.text_input("Instrutor")
    if lista_cursos_banco:
        curso = st.selectbox("Curso", lista_cursos_banco)
        saldo_atual = 0
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT saldo_contratado, alunos_realizados FROM cursos WHERE nome = %s", (curso,))
                res_curso = cur.fetchone()
            if res_curso:
                saldo_atual = res_curso[0] - res_curso[1]
        except Exception:
            pass
        st.info(f"Saldo disponível para este curso: {saldo_atual} vagas")
        alunos = st.number_input("Quantidade de Alunos", min_value=1, max_value=500, value=10)
        status = st.selectbox("Status", ["Agendada", "Realizada"])
        if st.button("Salvar Turma"):
            try:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO turmas (data, cliente, curso, instrutor, alunos, status) VALUES (%s,%s,%s,%s,%s,%s);", (data, cliente, curso, instrutor, alunos, status))
                    if status == "Realizada":
                        cur.execute("UPDATE cursos SET alunos_realizados = alunos_realizados + %s WHERE nome = %s;", (alunos, curso))
                st.success("Turma cadastrada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar turma: {e}")
    else:
        st.warning("Cadastre um curso primeiro no separador 'Controle de Saldo'.")

# ==================================================
# CONTROLE DE SALDO
# ==================================================
elif menu == "Controle de Saldo":
    st.subheader("Auditoria e Controle de Saldos")
    try:
        cursos = pd.read_sql("SELECT * FROM cursos", conn)
        cursos["saldo_atual"] = cursos["saldo_contratado"] - cursos["alunos_realizados"]
    except Exception:
        cursos = pd.DataFrame()
    if not cursos.empty:
        col_c1, col_c2 = st.columns(2)
        for idx, row in cursos.iterrows():
            alvo_col = col_c1 if idx % 2 == 0 else col_c2
            with alvo_col:
                status_texto = "POSITIVO (Disponível)" if row['saldo_atual'] >= 0 else "NEGATIVO (Excedido)"
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #E0E0E0; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #0A2D62;">{row['nome']}</h4>
                    <p style="margin: 5px 0; font-size: 14px; color: #555;">Contratado: <b>{row['saldo_contratado']}</b> | Treinado: <b>{row['alunos_realizados']}</b></p>
                    <p style="margin: 0; font-size: 15px; color: {'#2ECC71' if row['saldo_atual'] >= 0 else '#E74C3C'};">
                        Saldo Restante: <b>{row['saldo_atual']} vagas</b> ({status_texto})
                    </p>
                </div>
                """, unsafe_allow_html=True)
    st.divider()
    tab_recarga, tab_novo_curso = st.tabs(["Adicionar Nova Recarga de Vagas", "Cadastrar Novo Curso"])
    with tab_recarga:
        st.markdown("### Adicionar Vagas a um Curso Existente")
        if lista_cursos_banco:
            curso_recarga = st.selectbox("Selecionar Curso para Recarga", lista_cursos_banco)
            qtd = st.number_input("Quantidade Contratada (Vagas)", min_value=1, max_value=10000, value=10, key="qtd_recarga")
            obs = st.text_input("Observação / Número do Pedido", key="obs_recarga")
            if st.button("Confirmar Entrada de Vagas"):
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE cursos SET saldo_contratado = saldo_contratado + %s WHERE nome = %s;", (qtd, curso_recarga))
                        cur.execute("INSERT INTO movimentacoes (data, curso, tipo, quantidade, observacao) VALUES (%s, %s, 'RECARGA', %s, %s);", (date.today(), curso_recarga, qtd, obs))
                    st.success("Recarga aplicada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro na recarga: {e}")
        else:
            st.info("Nenhum curso cadastrado para receber recargas.")
    with tab_novo_curso:
        st.markdown("### Inserir Novo Curso na Grade")
        novo_curso_nome = st.text_input("Nome do Novo Curso").strip()
        resp_tecnico = st.text_input("Instrutor / Responsável Técnico").strip()
        qtd_inicial = st.number_input("Quantidade Contratada Inicial", min_value=0, max_value=10000, value=0, key="qtd_novo")
        obs_novo = st.text_input("Observação / Número do Pedido", key="obs_novo")
        if st.button("Cadastrar Novo Curso"):
            if not novo_curso_nome:
                st.error("O nome do curso não pode ser vazio.")
            else:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO cursos (nome, saldo_contratado, alunos_realizados, responsavel_tecnico) 
                            VALUES (%s, %s, 0, %s)
                            ON CONFLICT (nome) DO NOTHING;
                        """, (novo_curso_nome, qtd_inicial, resp_tecnico))
                    st.success(f"Curso '{novo_curso_nome}' cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar curso: {e}")

# ==================================================
# GERENCIAR ALUNOS
# ==================================================
elif menu == "Gerenciar Alunos":
    st.subheader("Controle de Alunos / Colaboradores Harman")
    tab_listar, tab_cadastrar = st.tabs(["Lista de Funcionários", "Cadastrar Novo Colaborador"])
    with tab_cadastrar:
        st.markdown("### Formulário de Cadastro")
        matricula = st.text_input("Número de Matrícula").strip()
        nome_completo = st.text_input("Nome Completo").strip()
        funcao = st.text_input("Função / Cargo").strip()
        divisao_escolhida = st.radio("Divisão da Empresa", ["Lifestyle (Código 01)", "Automotive (Código 02)"])
        div_codigo, div_nome = ("01", "Lifestyle") if "Lifestyle" in divisao_escolhida else ("02", "Automotive")
        if st.button("Salvar Colaborador"):
            if not matricula or not nome_completo:
                st.error("Matrícula e Nome Completo são obrigatórios.")
            else:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO colaboradores (matricula, nome_completo, funcao, divisao_codigo, divisao_nome)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (matricula) 
                            DO UPDATE SET nome_completo = EXCLUDED.nome_completo, funcao = EXCLUDED.funcao, 
                                          divisao_codigo = EXCLUDED.divisao_codigo, divisao_nome = EXCLUDED.divisao_nome;
                        """, (matricula, nome_completo, funcao, div_codigo, div_nome))
                    st.success("Colaborador registrado com sucesso!")
                    st.rerun()
                except Exception as error:
                    st.error(f"Erro ao salvar: {error}")
    with tab_listar:
        st.markdown("### Funcionários Cadastrados")
        try:
            df_colab = pd.read_sql("SELECT matricula as \"Matrícula\", nome_completo as \"Nome Completo\", funcao as \"Função\", divisao_codigo as \"Cód. Divisão\", divisao_nome as \"Divisão\" FROM colaboradores ORDER BY nome_completo ASC", conn)
        except Exception:
            df_colab = pd.DataFrame()
        if not df_colab.empty:
            st.dataframe(df_colab, use_container_width=True, hide_index=True)
            st.divider()
            mat_excluir = st.text_input("Digite a Matrícula do funcionário que deseja remover:")
            if st.button("Remover Funcionário"):
                try:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM colaboradores WHERE matricula = %s", (mat_excluir,))
                    st.success("Removido com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao remover: {e}")
        else:
            st.info("Nenhum colaborador registrado ainda.")

# ==================================================
# HISTÓRICO E RECICLAGENS
# ==================================================
elif menu == "Histórico e Reciclagens":
    st.subheader("Histórico Geral de Treinamentos e Reciclagens")
    tab_hist, tab_status_update = st.tabs(["Histórico Geral e Vencimentos", "Atualizar Status de Agendamentos"])
    with tab_status_update:
        st.markdown("### Alterar Status de Turmas Agendadas")
        try:
            df_agendadas = pd.read_sql("SELECT id, data, curso, instrutor, alunos, status FROM turmas WHERE status = 'Agendada' ORDER BY data ASC", conn)
        except Exception:
            df_agendadas = pd.DataFrame()
        if not df_agendadas.empty:
            df_agendadas['data'] = pd.to_datetime(df_agendadas['data']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_agendadas, use_container_width=True, hide_index=True)
            st.divider()
            id_selecionado = st.number_input("Digite o ID da turma concluída:", min_value=1, step=1)
            if st.button("Confirmar Realização da Turma"):
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT curso, alunos FROM turmas WHERE id = %s AND status = 'Agendada';", (id_selecionado,))
                        registro = cur.fetchone()
                        if registro:
                            v_curso, v_alunos = registro
                            cur.execute("UPDATE turmas SET status = 'Realizada' WHERE id = %s;", (id_selecionado,))
                            cur.execute("UPDATE cursos SET alunos_realizados = alunos_realizados + %s WHERE nome = %s;", (v_alunos, v_curso))
                            st.success("Status atualizado!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
        else:
            st.info("Não existem turmas agendadas no momento.")
    with tab_hist:
        st.markdown("Regra: Validade recomendada de 2 anos (730 dias).")
        try:
            df = pd.read_sql("SELECT id, data, cliente, curso, alunos, status FROM turmas ORDER BY id DESC", conn)
        except Exception:
            df = pd.DataFrame()
        if not df.empty:
            df['data'] = pd.to_datetime(df['data'])
            df['Data de Vencimento'] = df['data'] + timedelta(days=730)
            data_hoje = datetime.combine(date.today(), datetime.min.time())
            df['Dias Restantes'] = (df['Data de Vencimento'] - data_hoje).dt.days
            df['Status Reciclagem'] = df['Dias Restantes'].apply(lambda d: "VENCIDO" if d < 0 else ("EXPIRANDO" if d <= 60 else "Regular"))
            df['data'] = df['data'].dt.strftime('%d/%m/%Y')
            df['Data de Vencimento'] = df['Data de Vencimento'].dt.strftime('%d/%m/%Y')
            st.dataframe(df[["id", "data", "cliente", "curso", "alunos", "status", "Data de Vencimento", "Status Reciclagem"]], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma turma registrada.")
