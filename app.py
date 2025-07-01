# Importações
import os
import sqlite3
import streamlit as st
from typing import TypedDict, List
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Conectar ao banco de dados
DB_PATH = "manutencao_industrial.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# Inicializar modelo da DeepSeek
llm = ChatDeepSeek(api_key=DEEPSEEK_API_KEY, model="deepseek-chat")

# --- Funções Auxiliares ---
def get_db_schema(connection):
    """Extrai o schema de todas as tabelas do banco de dados SQLite."""
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    schema_str = ""
    for table_name in tables:
        table_name = table_name[0]
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE name = '{table_name}';")
        create_table_stmt = cursor.fetchone()[0]
        schema_str += f"{create_table_stmt};\n\n"
    return schema_str

# Pega o schema uma vez para ser usado nos prompts
db_schema = get_db_schema(conn)

# --- Definição do Estado do Grafo ---
class AgentState(TypedDict):
    question: str
    chat_history: list[HumanMessage | AIMessage]
    sql_query: str
    sql_result: str | List[dict] # Pode ser uma string de erro ou lista de resultados
    final_answer: str
    error_count: int # Para evitar loops infinitos

# --- Nós do Grafo (Funções) ---
def generate_sql(state: AgentState) -> AgentState:
    """Gera uma consulta SQL a partir da pergunta do usuário, usando o histórico."""
    st.write("🤖 Considerando o histórico e pensando em uma consulta SQL...")

    # Formatando o histórico para ser legível no prompt
    history_str = "\n".join([f"{'Humano' if isinstance(m, HumanMessage) else 'Assistente'}: {m.content}" for m in state['chat_history']])
    
    prompt = PromptTemplate.from_template(
        """
        Você é um assistente especialista em bancos de dados SQLite, atuando no contexto de uma planta industrial da SiderTech Solutions, no setor metalmecânico. 

        Sua tarefa é gerar uma consulta SQL precisa com base na pergunta de um usuário (que pode ser um operador, engenheiro ou gestor), usando o schema fornecido e, se necessário, o histórico da conversa para obter contexto.

        Importante:
        - Gere apenas a consulta SQL (sem explicações, comentários ou rodeios).
        - Nunca use aspas para nomes de tabelas ou colunas.
        - Se não for possível responder com os dados disponíveis, retorne exatamente: `SEM_RESPOSTA`
        - Utilize apenas comandos SELECT.
        - Seja cuidadoso com relacionamentos entre tabelas e selecione apenas o que for necessário.
        - Adapte a consulta ao contexto de manutenção industrial (equipamentos, ordens de serviço, técnicos, turnos, histórico etc).

        -- Histórico da Conversa --
        {chat_history}
        -- Fim do Histórico --

        -- Schema do Banco de Dados --
        {schema}
        -- Fim do Schema --

        Pergunta atual do usuário:
        {question}

        Consulta SQL:
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    sql_query = chain.invoke({
        "question": state["question"],
        "schema": db_schema,
        "chat_history": history_str
    })
    
    return {**state, "sql_query": sql_query.strip()}

def execute_sql(state: AgentState) -> AgentState:
    """Executa a consulta SQL e retorna o resultado ou um erro."""
    st.write(f"🔍 Executando SQL: `{state['sql_query']}`")
    sql = state["sql_query"]

    # Medida de segurança simples: permitir apenas SELECT
    if not sql.strip().upper().startswith("SELECT"):
        return {**state, "sql_result": "Erro de Segurança: Apenas consultas SELECT são permitidas."}

    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows]
        if not result:
            result = "A consulta não retornou resultados."
        return {**state, "sql_result": result}
    except Exception as e:
        return {**state, "sql_result": f"Erro SQL: {e}"}

def generate_final_answer(state: AgentState) -> AgentState:
    """Gera uma resposta em linguagem natural com base nos resultados."""
    st.write("💬 Formulando a resposta final...")
    
    prompt = PromptTemplate.from_template(
        """
        Você é um assistente inteligente e prestativo, projetado para apoiar operadores, engenheiros e gestores da SiderTech Solutions no acesso fácil e rápido a dados de manutenção industrial.

        Sua tarefa é interpretar perguntas feitas em linguagem natural e responder com base nos resultados de uma consulta SQL, utilizando uma linguagem clara, objetiva e adequada ao ambiente de fábrica.

        - Se os dados retornarem vazios ou houver erro na consulta, explique isso de forma amigável, sem termos técnicos complexos.
        - Sempre seja direto e evite rodeios.
        - Foque em entregar uma resposta útil e fácil de entender para quem está na operação.

        Pergunta Original:
        {question}

        Resultados da Consulta SQL:
        {sql_result}

        Resposta Final (em português do Brasil):
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    final_answer = chain.invoke({
        "question": state["question"],
        "sql_result": state["sql_result"]
    })
    
    return {**state, "final_answer": final_answer}

# --- Lógica Condicional do Grafo ---
def should_continue(state: AgentState) -> str:
    """Decide o próximo passo: gerar resposta, tentar novamente ou parar."""
    if isinstance(state["sql_result"], str) and "Erro" in state["sql_result"]:
        # Se houve um erro, incrementa o contador e tenta de novo (se não excedeu o limite)
        error_count = state.get("error_count", 0) + 1
        if error_count >= 2: # Tenta corrigir no máximo 1 vez
            return "end_with_error"
        else:
            return "retry_sql_generation"
    else:
        return "generate_answer"

# --- Construção do Grafo com LangGraph ---
builder = StateGraph(AgentState)

builder.add_node("generate_sql", generate_sql)
builder.add_node("execute_sql", execute_sql)
builder.add_node("generate_final_answer", generate_final_answer)

builder.set_entry_point("generate_sql")

# Adiciona a lógica condicional
builder.add_conditional_edges(
    "execute_sql",
    should_continue,
    {
        "retry_sql_generation": "generate_sql",
        "generate_answer": "generate_final_answer",
        "end_with_error": END
    }
)

builder.add_edge("generate_sql", "execute_sql")
builder.add_edge("generate_final_answer", END)

graph = builder.compile()

# --- Interface Streamlit ---
st.set_page_config(page_title="Agente Industrial Inteligente", layout="wide")
st.title("🤖 Agente Industrial Inteligente")
st.caption(f"Conectado ao banco de dados: `{DB_PATH}`")

# with st.expander("Ver Schema do Banco de Dados"):
#     st.code(db_schema, language="sql")

# Inicializa a memória da sessão se ela não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe as mensagens do histórico no início
for message in st.session_state.messages:
    with st.chat_message(message.type): # .type será 'human' ou 'ai'
        st.markdown(message.content)

# Usando st.chat_input para uma interface de chat mais natural
if question := st.chat_input("Faça uma pergunta sobre a manutenção industrial..."):
    
    # Adiciona a mensagem do usuário ao histórico da sessão E a exibe
    st.session_state.messages.append(HumanMessage(content=question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("O agente está trabalhando..."):
        # Prepara o estado inicial para o grafo, incluindo o histórico
        initial_state = {
            "question": question,
            "chat_history": st.session_state.messages[:-1], # Passa o histórico ATÉ a pergunta atual
            "error_count": 0
        }
        
        # Invoca o grafo
        final_state = graph.invoke(initial_state)
        
        final_answer = final_state.get("final_answer", "O agente não conseguiu concluir a tarefa.")

        # Exibe a resposta do agente
        with st.chat_message("assistant"):
            st.markdown(final_answer)
            with st.expander("Detalhes Técnicos"):
                st.markdown(f"**SQL Gerado:**")
                st.code(final_state.get('sql_query', 'N/A'), language="sql")
                st.markdown(f"**Resultado da Consulta:**")
                st.json(final_state.get('sql_result', 'N/A'))

        # Adiciona a resposta do agente ao histórico da sessão para a próxima rodada
        st.session_state.messages.append(AIMessage(content=final_answer))
