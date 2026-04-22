import streamlit as st
import psycopg2
import pandas as pd
import hashlib
import plotly.express as px
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURAÇÃO E SEGURANÇA ---
st.set_page_config(page_title="Conselho Diva Lima - Gestão", layout="wide")

def hash_password(password):
    if not password:
        return ""
    return hashlib.sha256(str.encode(password)).hexdigest()

# Credenciais de conexão (Supabase)
DB_URI = "postgresql://postgres:1lfDYaz3t0camT63@db.cjnsmuidekypdrohyyfw.supabase.co:5432/postgres?sslmode=require"

def get_connection():
    try:
        return psycopg2.connect(DB_URI, connect_timeout=5)
    except:
        return None

# --- 2. INICIALIZAÇÃO DO BANCO ---
def inicializar_sistema():
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, login TEXT UNIQUE, senha TEXT);")
        cur.execute("CREATE TABLE IF NOT EXISTS turmas (id SERIAL PRIMARY KEY, nome_turma TEXT UNIQUE);")
        cur.execute("CREATE TABLE IF NOT EXISTS alunos (id SERIAL PRIMARY KEY, nome_aluno TEXT, turma_vinculada TEXT);")
        cur.execute("""CREATE TABLE IF NOT EXISTS registros (
            id SERIAL PRIMARY KEY, aluno TEXT, turma TEXT, bimestre TEXT, 
            disciplina TEXT, desempenho TEXT, observacoes TEXT, data_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );""")
        
        cur.execute("ALTER TABLE registros ADD COLUMN IF NOT EXISTS data_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS vinculos_professores (
            id SERIAL PRIMARY KEY, login_usuario TEXT, turma TEXT, disciplina TEXT
        );""")
        cur.execute("""CREATE TABLE IF NOT EXISTS periodos_lancamento (
            bimestre TEXT PRIMARY KEY, data_inicio DATE, data_fim DATE
        );""")
        
        cur.execute("SELECT 1 FROM usuarios WHERE login = 'admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO usuarios (login, senha) VALUES ('admin', %s)", (hash_password(""),))
        
        for b in ["1º Bim", "2º Bim", "3º Bim", "4º Bim"]:
            cur.execute("INSERT INTO periodos_lancamento (bimestre, data_inicio, data_fim) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", (b, datetime.now().date(), datetime.now().date()))
            
        conn.commit()
        conn.close()

inicializar_sistema()

# --- 3. CONTROLE DE ACESSO ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        col_logo1, col_logo2 = st.columns([1, 4])
        with col_logo1:
            st.image("https://cjnsmuidekypdrohyyfw.supabase.co/storage/v1/object/sign/Logo%20Escola%20Diva%20Lima/Logo%20escola.png?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9kMDIxNjhjZi04ZjM1LTQ5ODEtYjgxMy1kOWQ1OTgyN2VmMTEiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJMb2dvIEVzY29sYSBEaXZhIExpbWEvTG9nbyBlc2NvbGEucG5nIiwiaWF0IjoxNzc2ODE5MjU0LCJleHAiOjE5MzQ0OTkyNTR9.ihPSTfODzvyptet78ahTiG7bkDvGngZnsafxeXiWocc", width=80)
        with col_logo2:
            st.title("Portal Diva Lima")
            
        u_login = st.text_input("Usuário")
        u_senha = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            conn = get_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT senha FROM usuarios WHERE login = %s", (u_login,))
                result = cur.fetchone()
                if result and result[0] == hash_password(u_senha):
                    st.session_state['logado'] = True
                    st.session_state['usuario_nome'] = u_login
                    st.rerun()
                else:
                    st.error("Login ou senha inválidos.")
                conn.close()
else:
    # --- 4. INTERFACE PRINCIPAL ---
    st.sidebar.image("https://cjnsmuidekypdrohyyfw.supabase.co/storage/v1/object/sign/Logo%20Escola%20Diva%20Lima/Logo%20escola.png?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9kMDIxNjhjZi04ZjM1LTQ5ODEtYjgxMy1kOWQ1OTgyN2VmMTEiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJMb2dvIEVzY29sYSBEaXZhIExpbWEvTG9nbyBlc2NvbGEucG5nIiwiaWF0IjoxNzc2ODE5MjU0LCJleHAiOjE5MzQ0OTkyNTR9.ihPSTfODzvyptet78ahTiG7bkDvGngZnsafxeXiWocc", width=80)
    st.sidebar.title(f"👤 {st.session_state['usuario_nome']}")
    
    menu_opcoes = ["📝 Lançar desempenho"]
    if st.session_state['usuario_nome'] == 'admin':
        menu_opcoes.append("👥 Cadastros")
    
    menu_opcoes.append("🔐 Segurança")
    menu_opcoes.extend(["📊 Relatórios & Dashboard", "🚪 Sair"])
    
    opcao = st.sidebar.radio("Navegação", menu_opcoes)

    if opcao == "🚪 Sair":
        st.session_state['logado'] = False
        st.rerun()

    elif opcao == "📝 Lançar desempenho":
        st.header("📝 Lançamento de Desempenho")
        conn = get_connection()
        if conn:
            if st.session_state['usuario_nome'] == 'admin':
                df_t = pd.read_sql("SELECT nome_turma FROM turmas ORDER BY nome_turma", conn)
                lista_disciplinas = ["Português", "Matemática", "História", "Geografia", "Ciências", "Artes", "Ensino Religioso", "Projeto de Vida", "Inglês", "Espanhol", "Educação Física"]
            else:
                df_t = pd.read_sql("SELECT DISTINCT turma AS nome_turma FROM vinculos_professores WHERE login_usuario = %s", conn, params=(st.session_state['usuario_nome'],))
                df_d = pd.read_sql("SELECT DISTINCT disciplina FROM vinculos_professores WHERE login_usuario = %s", conn, params=(st.session_state['usuario_nome'],))
                lista_disciplinas = df_d['disciplina'].tolist() if not df_d.empty else []

            turmas = df_t['nome_turma'].tolist() if not df_t.empty else ["Nenhuma vinculada"]
            
            c1, c2 = st.columns(2)
            with c1:
                t_sel = st.selectbox("Turma", turmas)
                bim = st.selectbox("Bimestre", ["1º Bim", "2º Bim", "3º Bim", "4º Bim"])
            
            df_a = pd.read_sql("SELECT nome_aluno FROM alunos WHERE turma_vinculada = %s ORDER BY nome_aluno", conn, params=(t_sel,))
            alunos = df_a['nome_aluno'].tolist() if not df_a.empty else ["Nenhum aluno"]
            
            with c2:
                al_sel = st.selectbox("Aluno", alunos)
                disc = st.selectbox("Disciplina", lista_disciplinas)

            des = st.radio("Desempenho:", ["Aprovado após recuperação", "Reprovado"], horizontal=True)
            
            st.write("**Valores e atitudes:**")
            v_a_opcoes = ["Não faz tarefa em sala", "Não faz tarefa em casa", "Conversa muito", "Não traz material", "Não apresenta trabalhos", "Indisciplinado"]
            v_a_selecionados = st.multiselect("Selecione os itens aplicáveis:", v_a_opcoes)
            
            obs = st.text_area("Observações")
            
            pode_gravar = True
            cur = conn.cursor()
            cur.execute("SELECT data_inicio, data_fim FROM periodos_lancamento WHERE bimestre = %s", (bim,))
            periodo = cur.fetchone()
            hoje = datetime.now().date()
            if periodo:
                if not (periodo[0] <= hoje <= periodo[1]):
                    pode_gravar = False
                    st.error(f"O período de lançamento para o {bim} está bloqueado ({periodo[0].strftime('%d/%m/%Y')} até {periodo[1].strftime('%d/%m/%Y')}).")

            if st.button("💾 SALVAR REGISTRO", disabled=not pode_gravar):
                with st.spinner("Salvando..."):
                    obs_final = obs
                    if v_a_selecionados:
                        txt_va = "Valores e atitudes: " + ", ".join(v_a_selecionados)
                        obs_final = f"{txt_va}\n{obs}" if obs else txt_va
                        
                    cur = conn.cursor()
                    cur.execute("INSERT INTO registros (aluno, turma, bimestre, disciplina, desempenho, observacoes) VALUES (%s,%s,%s,%s,%s,%s)",
                                (al_sel, t_sel, bim, disc, des, obs_final))
                    conn.commit()
                    st.success(f"Registro de {al_sel} x salvo!")
            conn.close()

    elif opcao == "🔐 Segurança":
        st.header("🔐 Segurança da Conta")
        
        if st.session_state['usuario_nome'] == 'admin':
            tab_minha, tab_reset = st.tabs(["Minha Senha", "Resetar Senha de Usuários"])
            
            with tab_minha:
                senha_atual = st.text_input("Senha Atual", type="password", key="sec_at")
                nova_senha = st.text_input("Nova Senha (deixe em branco para remover)", type="password", key="sec_nv")
                confirma_senha = st.text_input("Confirmar Nova Senha", type="password", key="sec_cf")
                if st.button("Atualizar Minha Senha"):
                    if nova_senha != confirma_senha:
                        st.error("As novas senhas não coincidem.")
                    else:
                        conn = get_connection()
                        if conn:
                            cur = conn.cursor()
                            cur.execute("SELECT senha FROM usuarios WHERE login = %s", (st.session_state['usuario_nome'],))
                            res = cur.fetchone()
                            if res and res[0] == hash_password(senha_atual):
                                cur.execute("UPDATE usuarios SET senha = %s WHERE login = %s", (hash_password(nova_senha), st.session_state['usuario_nome']))
                                conn.commit()
                                st.success("Sua senha foi alterada com sucesso!")
                            else:
                                st.error("Senha atual incorreta.")
                            conn.close()

            with tab_reset:
                st.subheader("Resetar Senha de Outro Usuário")
                conn = get_connection()
                if conn:
                    df_users = pd.read_sql("SELECT login FROM usuarios WHERE login != 'admin'", conn)
                    user_reset = st.selectbox("Selecionar Usuário para Reset", df_users['login'].tolist() if not df_users.empty else [])
                    nova_senha_admin = st.text_input("Nova Senha Temporária (deixe em branco para remover)", type="password", key="pwd_adm_rs")
                    
                    if st.button("Resetar Senha do Usuário"):
                        if user_reset:
                            cur = conn.cursor()
                            cur.execute("UPDATE usuarios SET senha = %s WHERE login = %s", (hash_password(nova_senha_admin), user_reset))
                            conn.commit()
                            st.success(f"Senha de {user_reset} redefinida!")
                    conn.close()
        
        else:
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha (deixe em branco para remover)", type="password")
            confirma_senha = st.text_input("Confirmar Nova Senha", type="password")
            
            if st.button("Confirmar Alteração", key="btn_update_p"):
                if nova_senha != confirma_senha:
                    st.error("As novas senhas não coincidem.")
                else:
                    conn = get_connection()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("SELECT senha FROM usuarios WHERE login = %s", (st.session_state['usuario_nome'],))
                        res = cur.fetchone()
                        if res and res[0] == hash_password(senha_atual):
                            cur.execute("UPDATE usuarios SET senha = %s WHERE login = %s", (hash_password(nova_senha), st.session_state['usuario_nome']))
                            conn.commit()
                            st.success("Sua senha foi alterada com sucesso!")
                        else:
                            st.error("Senha atual incorreta.")
                        conn.close()

    elif opcao == "👥 Cadastros":
        st.header("⚙️ Painel de Cadastros")
        tab1, tab2, tab3, tab4 = st.tabs(["👤 Usuários & Vínculos", "🏫 Turmas", "🎓 Alunos", "📅 Períodos"])

        with tab1:
            st.subheader("Gerenciar Acessos e Vínculos")
            conn = get_connection()
            if conn:
                df_t_vinc = pd.read_sql("SELECT nome_turma FROM turmas ORDER BY nome_turma", conn)
                turmas_disponiveis = df_t_vinc['nome_turma'].tolist()
                disciplinas_list = ["Português", "Matemática", "História", "Geografia", "Ciências", "Artes", "Ensino Religioso", "Projeto de Vida", "Inglês", "Espanhol", "Educação Física"]
                
                tipo_acao = st.radio("O que deseja fazer?", ["Vincular usuário existente", "Cadastrar novo usuário com vínculos", "Editar Nome de Usuário", "Excluir Usuário"], horizontal=True)
                
                st.divider()
                
                if tipo_acao == "Vincular usuário existente":
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        df_users_list = pd.read_sql("SELECT login FROM usuarios WHERE login != 'admin' ORDER BY login", conn)
                        user_para_vincular = st.selectbox("Selecione o Usuário", df_users_list['login'].tolist())
                    with col_v2:
                        vinc_turmas = st.multiselect("Adicionar Turmas", turmas_disponiveis)
                        vinc_discs = st.multiselect("Adicionar Disciplinas", disciplinas_list)
                    
                    if st.button("Atualizar Vínculos"):
                        if not vinc_turmas or not vinc_discs:
                            st.warning("Selecione ao menos uma turma e uma disciplina.")
                        else:
                            cur = conn.cursor()
                            for t in vinc_turmas:
                                for d in vinc_discs:
                                    cur.execute("""
                                        INSERT INTO vinculos_professores (login_usuario, turma, disciplina) 
                                        SELECT %s, %s, %s 
                                        WHERE NOT EXISTS (
                                            SELECT 1 FROM vinculos_professores WHERE login_usuario=%s AND turma=%s AND disciplina=%s
                                        )""", (user_para_vincular, t, d, user_para_vincular, t, d))
                            conn.commit()
                            st.success(f"Novos vínculos adicionados para {user_para_vincular}!")
                
                elif tipo_acao == "Cadastrar novo usuário com vínculos":
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        new_user = st.text_input("Novo Usuário Login")
                        new_pass = st.text_input("Senha Inicial (deixe em branco para nenhuma)", type="password")
                    with col_v2:
                        vinc_turmas = st.multiselect("Vincular Turmas", turmas_disponiveis)
                        vinc_discs = st.multiselect("Vincular Disciplinas", disciplinas_list)

                    if st.button("Confirmar Cadastro Completo"):
                        if not new_user or not vinc_turmas or not vinc_discs:
                            st.warning("Preencha os campos obrigatórios (Login, Turmas e Disciplinas).")
                        else:
                            cur = conn.cursor()
                            try:
                                cur.execute("INSERT INTO usuarios (login, senha) VALUES (%s, %s)", (new_user, hash_password(new_pass)))
                                for t in vinc_turmas:
                                    for d in vinc_discs:
                                        cur.execute("INSERT INTO vinculos_professores (login_usuario, turma, disciplina) VALUES (%s, %s, %s)", (new_user, t, d))
                                conn.commit()
                                st.success(f"Usuário {new_user} cadastrado e vinculado!")
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Erro ao cadastrar: Usuário já existe ou erro no banco.")

                elif tipo_acao == "Editar Nome de Usuário":
                    col_e1, col_e2 = st.columns(2)
                    df_users_edit = pd.read_sql("SELECT login FROM usuarios WHERE login != 'admin' ORDER BY login", conn)
                    with col_e1:
                        user_antigo = st.selectbox("Usuário Atual", df_users_edit['login'].tolist())
                    with col_e2:
                        user_novo_nome = st.text_input("Novo Nome de Login")
                    
                    if st.button("Salvar Alteração de Nome"):
                        if not user_novo_nome:
                            st.error("O novo nome não pode ser vazio.")
                        else:
                            cur = conn.cursor()
                            try:
                                cur.execute("UPDATE usuarios SET login = %s WHERE login = %s", (user_novo_nome, user_antigo))
                                cur.execute("UPDATE vinculos_professores SET login_usuario = %s WHERE login_usuario = %s", (user_novo_nome, user_antigo))
                                conn.commit()
                                st.success(f"Usuário alterado de {user_antigo} para {user_novo_nome}. Vínculos preservados!")
                                st.rerun()
                            except:
                                conn.rollback()
                                st.error("Erro ao atualizar: Nome de usuário já pode estar em uso.")

                elif tipo_acao == "Excluir Usuário":
                    df_users_del = pd.read_sql("SELECT login FROM usuarios WHERE login != 'admin' ORDER BY login", conn)
                    user_excluir = st.selectbox("Selecione o Usuário para remover permanentemente", df_users_del['login'].tolist())
                    st.warning(f"Isso removerá o usuário {user_excluir} e todos os seus vínculos de turmas/disciplinas.")
                    if st.button("❌ EXCLUIR DEFINITIVAMENTE"):
                        cur = conn.cursor()
                        cur.execute("DELETE FROM vinculos_professores WHERE login_usuario = %s", (user_excluir,))
                        cur.execute("DELETE FROM usuarios WHERE login = %s", (user_excluir,))
                        conn.commit()
                        st.success(f"Usuário {user_excluir} removido com sucesso.")
                        st.rerun()
                
                st.divider()
                st.write("📋 **Vínculos Atuais**")
                df_vinc_ver = pd.read_sql("SELECT login_usuario as professor, turma, disciplina FROM vinculos_professores ORDER BY login_usuario", conn)
                st.dataframe(df_vinc_ver, use_container_width=True)
                
                if not df_vinc_ver.empty:
                   st.write("🗑️ **Remover Vínculo Específico**")
                   vinc_del = st.selectbox("Selecione o vínculo para remover", df_vinc_ver.index.tolist(), format_func=lambda x: f"{df_vinc_ver.loc[x, 'professor']} - {df_vinc_ver.loc[x, 'turma']} ({df_vinc_ver.loc[x, 'disciplina']})")
                   if st.button("Remover Vínculo Selecionado"):
                       row = df_vinc_ver.loc[vinc_del]
                       cur = conn.cursor()
                       cur.execute("DELETE FROM vinculos_professores WHERE login_usuario=%s AND turma=%s AND disciplina=%s", (row['professor'], row['turma'], row['disciplina']))
                       conn.commit()
                       st.success("Vínculo removido.")
                       st.rerun()
                conn.close()

        with tab2:
            st.subheader("Gerenciar Turmas")
            c1, c2 = st.columns([1, 1])
            with c1:
                n_t_input = st.text_area("Adicionar Turmas (Cole do Excel)", placeholder="6º A\n6º B")
                if st.button("Cadastrar Turmas"):
                    linhas = n_t_input.replace(",", "\n").split("\n")
                    lista_turmas = [t.strip() for t in linhas if t.strip()]
                    conn = get_connection(); cur = conn.cursor()
                    for t in lista_turmas:
                        cur.execute("INSERT INTO turmas (nome_turma) VALUES (%s) ON CONFLICT DO NOTHING", (t,))
                    conn.commit(); conn.close()
                    st.success("Processamento concluído!")
                    st.rerun()
            with c2:
                st.write("🗑️ **Excluir Turma**")
                conn = get_connection()
                if conn:
                    df_t_list = pd.read_sql("SELECT id, nome_turma FROM turmas ORDER BY nome_turma", conn)
                    t_para_excluir = st.selectbox("Selecione para remover", df_t_list['nome_turma'].tolist() if not df_t_list.empty else [])
                    if st.button("❌ Remover Turma"):
                        cur = conn.cursor()
                        cur.execute("DELETE FROM turmas WHERE nome_turma = %s", (t_para_excluir,))
                        conn.commit(); conn.close()
                        st.warning(f"Turma {t_para_excluir} removida.")
                        st.rerun()

        with tab3:
            st.subheader("Gerenciar Alunos")
            conn = get_connection()
            if conn:
                df_t = pd.read_sql("SELECT nome_turma FROM turmas ORDER BY nome_turma", conn)
                t_vinc = st.selectbox("Selecione a Turma:", df_t['nome_turma'].tolist() if not df_t.empty else [])
                
                df_exibicao = pd.read_sql("SELECT id, nome_aluno FROM alunos WHERE turma_vinculada = %s ORDER BY nome_aluno", conn, params=(t_vinc,))
                
                if not df_exibicao.empty:
                    st.info(f"Alunos cadastrados na turma {t_vinc}:")
                    for index, row in df_exibicao.iterrows():
                        col_al, col_ex = st.columns([0.9, 0.1])
                        col_al.write(f"{row['nome_aluno']}")
                        if col_ex.button("x", key=f"del_{row['id']}"):
                            cur = conn.cursor()
                            cur.execute("DELETE FROM alunos WHERE id = %s", (row['id'],))
                            conn.commit()
                            st.rerun()
                else:
                    st.warning(f"Nenhum aluno cadastrado na turma {t_vinc} ainda.")

                n_a_input = st.text_area("Lista de Alunos para Adicionar (Cole do Excel)", height=200, value="", key=f"add_alunos_{t_vinc}")
                
                if st.button("Cadastrar Alunos"):
                    linhas = n_a_input.replace(",", "\n").split("\n")
                    lista_als = [a.strip() for a in linhas if a.strip()]
                    cur = conn.cursor()
                    for al in lista_als:
                        cur.execute("INSERT INTO alunos (nome_aluno, turma_vinculada) VALUES (%s, %s)", (al, t_vinc))
                    conn.commit()
                    st.success("Alunos cadastrados!")
                    st.rerun()
                
                st.divider()
                st.write(f"**Limpar Turma {t_vinc}**")
                st.warning("⚠️ Isso removerá TODOS os alunos desta turma.")
                if st.button(f"🔥 Limpar turma"):
                    cur = conn.cursor()
                    cur.execute("DELETE FROM alunos WHERE turma_vinculada = %s", (t_vinc,))
                    conn.commit()
                    st.success(f"Todos os alunos da turma {t_vinc} foram removidos!")
                    st.rerun()
                
                conn.close()

        with tab4:
            st.subheader("Configurar Períodos de Lançamento")
            conn = get_connection()
            if conn:
                df_per = pd.read_sql("SELECT * FROM periodos_lancamento", conn)
                novos_periodos = {}
                for index, row in df_per.iterrows():
                    col1, col2, col3 = st.columns([1, 2, 2])
                    with col1:
                        st.write(f"**{row['bimestre']}**")
                    with col2:
                        di = st.date_input(f"Início", row['data_inicio'], key=f"di_{row['bimestre']}", format="DD/MM/YYYY")
                    with col3:
                        df = st.date_input(f"Fim", row['data_fim'], key=f"df_{row['bimestre']}", format="DD/MM/YYYY")
                    novos_periodos[row['bimestre']] = (di, df)
                
                if st.button("💾 SALVAR TUDO", key="btn_salvar_periodos"):
                    cur = conn.cursor()
                    for bim, datas in novos_periodos.items():
                        cur.execute("UPDATE periodos_lancamento SET data_inicio = %s, data_fim = %s WHERE bimestre = %s", (datas[0], datas[1], bim))
                    conn.commit()
                    st.success("Todos os períodos foram atualizados com sucesso!")
                    st.rerun()
                conn.close()

    elif opcao == "📊 Relatórios & Dashboard":
        st.header("📊 Painel de Resultados")
        conn = get_connection()
        if conn:
            try:
                df_full = pd.read_sql("SELECT id, aluno, turma, bimestre, disciplina, desempenho, observacoes, data_registro FROM registros ORDER BY data_registro DESC", conn)
            except:
                df_full = pd.read_sql("SELECT id, aluno, turma, bimestre, disciplina, desempenho, observacoes FROM registros", conn)
            
            if not df_full.empty:
                st.subheader("🔍 Filtros de Busca")
                col1, col2, col3 = st.columns(3)
                f_turma = col1.multiselect("Filtrar Turma", df_full['turma'].unique())
                f_bim = col2.multiselect("Filtrar Bimestre", df_full['bimestre'].unique())
                f_disc = col3.multiselect("Filtrar Disciplina", df_full['disciplina'].unique())

                df_filtered = df_full.copy()
                if f_turma: df_filtered = df_filtered[df_filtered['turma'].isin(f_turma)]
                if f_bim: df_filtered = df_filtered[df_filtered['bimestre'].isin(f_bim)]
                if f_disc: df_filtered = df_filtered[df_filtered['disciplina'].isin(f_disc)]

                st.divider()
                st.subheader("📈 Visão Geral de Desempenho")
                col_graph1, col_graph2 = st.columns([1, 1])
                
                with col_graph1:
                    fig_pizza = px.pie(df_filtered, names='desempenho', title="Distribuição de Desempenho", 
                                     color='desempenho', color_discrete_map={'Aprovado após recuperação':'orange', 'Reprovado':'red'})
                    st.plotly_chart(fig_pizza, use_container_width=True)
                
                with col_graph2:
                    st.write(f"Total de registros filtrados: **{len(df_filtered)}**")
                    st.dataframe(df_filtered['desempenho'].value_counts())

                st.divider()
                st.subheader("📄 Tabela de Dados")
                st.dataframe(df_filtered, use_container_width=True)

                df_export = df_filtered.copy()
                if 'data_registro' in df_export.columns:
                    df_export['data_registro'] = pd.to_datetime(df_export['data_registro']).dt.tz_localize(None)

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Relatorio')
                
                st.download_button(
                    label="📥 Baixar Relatório em Excel",
                    data=output.getvalue(),
                    file_name=f"relatorio_diva_lima.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Nenhum registro encontrado.")
            conn.close()