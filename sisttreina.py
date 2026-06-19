import streamlit as st
import psycopg2
import pandas as pd
from datetime import date, datetime, timedelta
import plotly.express as px

# =========================
# CONFIGURACAO DA PAGINA
# =========================

st.set_page_config(
    page_title="Gestao de Treinamentos - Harman 2026",
    layout="wide"
)

# Estilizacao profissional, correcao do esmaecimento no celular e tratamento de fontes
st.markdown("""
<style>
.main { background-color: #F4F7FA; }
[data-testid="stSidebar"]{ background-color:#0A2D62; }
[data-testid="stSidebar"] *{ color:white; }

/* Remove o efeito escuro/esmaecido ao editar campos numericos no celular */
[data-testid="stAppViewBlockContainer"] {
    opacity: 1 !important;
}
div[data-testid="stBlock"] {
    opacity: 1 !important;
}
.stApp [data-testid="stDecoration"] {
    background-image: linear-gradient(90deg, #0A2D62, #2ECC71);
}

/* Estilo dos cards de metricas */
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
</style>
""", unsafe_allow_html=True)

# Indicador visual discreto de carregamento no topo da tela
with st.spinner("Processando dados..."):
    pass

# =========================
# URL DAS LOGOS
# =========================
URL_LOGO_MULTITECH = "https://tse3.mm.bing.net/th/id/OIP.L8zPK2KlscAyAmNBldf3bgHaHa?pid=Api&P=0&h=180"
URL_LOGO_HARMAN = "https://svgbrand.com/uploads/images/webp/202311/SVG_Brand_harman_international.webp"

# =========================
# CONEXAO COM BANCO EM NUVEM (POSTGRESQL)
# =========================

def conectar_nuvem():
    try:
        cfg = st.secrets["postgres"]
        conexao = psycopg2.connect(
            host=cfg["host"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            port=cfg["port"]
        )
        return conexao
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados em nuvem: {e}")
        st.stop()

conn = conectar_nuvem()
cursor = conn.cursor()

# Garantia da existencia das tabelas
cursor.execute("""
CREATE TABLE IF NOT EXISTS cursos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE,
    saldo_contratado INTEGER DEFAULT 0,
    alunos_realizados INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS turmas (
    id SERIAL PRIMARY KEY,
    data DATE,
    cliente VARCHAR(100),
    curso VARCHAR(100),
    instrutor VARCHAR(100),
    alunos INTEGER,
    status VARCHAR(50)
);
CREATE TABLE IF NOT EXISTS movimentacoes (
    id SERIAL PRIMARY KEY,
    data DATE,
    curso VARCHAR(100),
    tipo VARCHAR(50),
    quantidade INTEGER,
    observacao TEXT
);
""")
conn.commit()

# ==================================================
# BARRA LATERAL (MENU SIDEBAR)
# ==================================================

with st.sidebar:
    st.markdown("<p style='text-align: center; font-size: 11px; color: #BACAD6; letter-spacing: 1px;'>PARCERIA COMERCIAL</p>", unsafe_allow_html=True)
    side_logo1, side_logo2 = st.columns(2)
    with side_logo1: st.image(URL_LOGO_MULTITECH, use_container_width=True)
    with side_logo2: st.image(URL_LOGO_HARMAN, use_container_width=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Menu de Navegacao", ["Dashboard", "Agendar Turma", "Controle de Saldo", "Historico e Reciclagens"])

# ==================================================
# CABECALHO PRINCIPAL DA PAGINA
# ==================================================

head_col1, head_col2, head_col3 = st.columns([1, 5, 2])
with head_col1: st.image(URL_LOGO_MULTITECH, width=75)
with head_col2:
    st.title("Sistema de Gestao de Treinamentos")
    st.caption("MultiTech Treinamentos Industriais - Cliente: Harman")
with head_col3: st.image(URL_LOGO_HARMAN, width=160)

st.markdown("<br>", unsafe_allow_html=True)

# ==================================================
# DASHBOARD
# ==================================================

if menu == "Dashboard":
    cursos = pd.read_sql("SELECT * FROM cursos", conn)
    cursos["saldo_atual"] = cursos["saldo_contratado"] - cursos["alunos_realizados"]
    total_alunos = cursos["alunos_realizados"].sum()
    saldo_geral = cursos["saldo_atual"].sum()
    
    cursor.execute("SELECT COUNT(*) FROM turmas;")
    total_turmas = cursor.fetchone()[0]

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
    col_grafico1, col_grafico2 = st.columns([3, 2])

    with col_grafico1:
        st.subheader("Resumo de Saldos Oficiais por Curso")
        st.dataframe(cursos[["nome", "saldo_contratado", "alunos_realizados", "saldo_atual"]], use_container_width=True, hide_index=True)

    with col_grafico2:
        st.subheader("Relacao Global: Realizados x Disponiveis")
        saldo_grafico = saldo_geral if saldo_geral > 0 else 0
        dados_pizza = pd.DataFrame({
            "Status": ["Alunos Ja Treinados", "Saldo Geral Disponivel (Vagas)"],
            "Quantidade": [int(total_alunos), int(saldo_grafico)]
        })
        fig = px.pie(dados_pizza, values="Quantidade", names="Status", color_discrete_sequence=["#0A2D62", "#2ECC71"], hole=0.3)
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250)
        st.plotly_chart(fig, use_container_width=True)

    negativos = cursos[cursos["saldo_atual"] < 0]
    for _, row in negativos.iterrows():
        st.error(f"Atencao: O curso {row['nome']} esta com saldo negativo ({row['saldo_atual']} vagas). Necessita de nova recarga urgente!")

# ==================================================
# AGENDAR TURMA
# ==================================================

elif menu == "Agendar Turma":
    st.subheader("Nova Turma")
    data = st.date_input("Data", date.today())
    cliente = st.text_input("Cliente", value="Harman")
    instrutor = st.text_input("Instrutor")
    curso = st.selectbox("Curso", ["NR12", "Normas Técnicas de Solda"])

    cursos = pd.read_sql("SELECT * FROM cursos WHERE nome = %s", conn, params=(curso,))
    if not cursos.empty:
        saldo_atual = cursos.iloc[0]["saldo_contratado"] - cursos.iloc[0]["alunos_realizados"]
        st.info(f"Saldo disponivel para este curso: {saldo_atual} vagas")
    else:
        saldo_atual = 0

    alunos = st.number_input("Quantidade de Alunos", min_value=1, max_value=500, value=10)
    status = st.selectbox("Status", ["Agendada", "Realizada"])

    if st.button("Salvar Turma"):
        cursor.execute("INSERT INTO turmas (data, cliente, curso, instrutor, alunos, status) VALUES (%s,%s,%s,%s,%s,%s);", (data, cliente, curso, instrutor, alunos, status))
        if status == "Realizada":
            cursor.execute("INSERT INTO cursos (nome, saldo_contratado, alunos_realizados) VALUES (%s, 0, %s) ON CONFLICT (nome) DO UPDATE SET alunos_realizados = cursos.alunos_realizados + EXCLUDED.alunos_realizados;", (curso, alunos))
        conn.commit()
        st.success("Turma cadastrada com sucesso e salva na Nuvem!")
        st.rerun()

# ==================================================
# CONTROLE DE SALDO
# ==================================================

elif menu == "Controle de Saldo":
    st.subheader("Auditoria e Controle de Saldos")
    
    cursos = pd.read_sql("SELECT * FROM cursos", conn)
    cursos["saldo_atual"] = cursos["saldo_contratado"] - cursos["alunos_realizados"]
    
    # Exibicao de valores e indicadores textuais detalhados por curso
    col_c1, col_c2 = st.columns(2)
    for idx, row in cursos.iterrows():
        alvo_col = col_c1 if idx % 2 == 0 else col_c2
        with alvo_col:
            status_texto = "POSITIVO (Disponivel)" if row['saldo_atual'] >= 0 else "NEGATIVO (Excedido)"
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #E0E0E0; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #0A2D62;">{row['nome']}</h4>
                <p style="margin: 5px 0; font-size: 14px; color: #555;">Contratado: <b>{row['saldo_contratado']}</b> | Treinado: <b>{row['alunos_realizados']}</b></p>
                <p style="margin: 0; font-size: 15px; color: {'#2ECC71' if row['saldo_atual'] >= 0 else '#E74C3C'};">
                    Saldo Restante: <b>{row['saldo_atual']} vagas</b> ({status_texto})
                </p>
            </div>
            """, unsafe_allow_html=True)
            
    # Grafico comparativo de Saldos
    if not cursos.empty:
        df_melted = pd.melt(cursos, id_vars=['nome'], value_vars=['saldo_contratado', 'alunos_realizados', 'saldo_atual'],
                            var_name='Metrica', value_name='Vagas')
        df_melted['Metrica'] = df_melted['Metrica'].replace({
            'saldo_contratado': 'Contratado Total',
            'alunos_realizados': 'Alunos Treinados',
            'saldo_atual': 'Saldo Restante'
        })
        fig_saldo = px.bar(df_melted, x='nome', y='Vagas', color='Metrica', barmode='group',
                           color_discrete_sequence=["#0A2D62", "#34495E", "#2ECC71"],
                           labels={'nome': 'Curso', 'Vagas': 'Quantidade de Vagas'})
        fig_saldo.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_saldo, use_container_width=True)

    st.divider()
    st.subheader("Adicionar Nova Recarga")
    curso_recarga = st.selectbox("Selecionar Curso para Recarga", ["NR12", "Normas Técnicas de Solda"])
    qtd = st.number_input("Quantidade Contratada", min_value=1, max_value=10000, value=10)
    obs = st.text_input("Observacao / Numero do Pedido")

    if st.button("Confirmar Recarga"):
        cursor.execute("INSERT INTO cursos (nome, saldo_contratado, alunos_realizados) VALUES (%s, %s, 0) ON CONFLICT (nome) DO UPDATE SET saldo_contratado = cursos.saldo_contratado + EXCLUDED.saldo_contratado;", (curso_recarga, qtd))
        cursor.execute("INSERT INTO movimentacoes (data, curso, tipo, quantidade, observacao) VALUES (%s, %s, 'RECARGA', %s, %s);", (date.today(), curso_recarga, qtd, obs))
        conn.commit()
        st.success("Saldo atualizado com sucesso na Nuvem!")
        st.rerun()

# ==================================================
# HISTORICO E RECICLAGENS (COM OPCAO DE APAGAR)
# ==================================================

elif menu == "Historico e Reciclagens":
    st.subheader("Historico de Turmas e Controle de Reciclagem")
    st.markdown("Regra do Sistema: Todo treinamento possui validade recomendada de 2 anos (730 dias). Abaixo voce acompanha os prazos e os alertas de renovacao por turma.")

    df = pd.read_sql("SELECT id, data, cliente, curso, alunos, status FROM turmas ORDER BY id DESC", conn)

    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['Data de Vencimento'] = df['data'] + timedelta(days=730)
        
        data_hoje = datetime.combine(date.today(), datetime.min.time())
        df['Dias Restantes'] = (df['Data de Vencimento'] - data_hoje).dt.days

        def avaliar_reciclagem(dias):
            if dias < 0:
                return "VENCIDO (Agendar Atualizacao)"
            elif dias <= 60:
                return "EXPIRANDO (Providenciar Reciclagem)"
            else:
                return "Regular"

        df['Status Reciclagem'] = df['Dias Restantes'].apply(avaliar_reciclagem)

        df['data'] = df['data'].dt.strftime('%d/%m/%Y')
        df['Data de Vencimento'] = df['Data de Vencimento'].dt.strftime('%d/%m/%Y')

        # Exibe a tabela incluindo o ID da turma para facilitar a remocao
        st.dataframe(
            df[["id", "data", "cliente", "curso", "alunos", "Data de Vencimento", "Status Reciclagem"]],
            use_container_width=True,
            hide_index=True
        )

        excel_file = "historico_reciclagem_harman.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as arquivo:
            st.download_button("Exportar Relatorio para Excel", arquivo, file_name=excel_file)
            
        st.divider()
        
        # Painel Operacional para Remover Turma
        st.subheader("Painel de Exclusao de Turmas")
        st.caption("A exclusao removera o registro permanentemente e devolvera as vagas correspondentes ao saldo do curso.")
        id_para_apagar = st.number_input("Digite o ID da turma que deseja apagar", min_value=1, step=1)
        
        if st.button("Apagar Turma do Registro"):
            # Buscar dados da turma antes de apagar para fazer o estorno do saldo
            cursor.execute("SELECT curso, alunos, status FROM turmas WHERE id = %s;", (id_para_apagar,))
            resultado = cursor.fetchone()
            
            if resultado:
                v_curso, v_alunos, v_status = resultado
                # Remove do banco
                cursor.execute("DELETE FROM turmas WHERE id = %s;", (id_para_apagar,))
                # Se a turma estava realizada, estorna a quantidade do campo alunos_realizados
                if v_status == "Realizada":
                    cursor.execute("UPDATE cursos SET alunos_realizados = alunos_realizados - %s WHERE nome = %s;", (v_alunos, v_curso))
                conn.commit()
                st.success(f"Turma com ID {id_para_apagar} foi removida com sucesso!")
                st.rerun()
            else:
                st.error("ID de turma nao encontrado no banco de dados.")
    else:
        st.warning("Nenhuma turma ativa registrada no banco de dados ate o momento.")