## 📌 Projeto: Agente Industrial Inteligente

Este projeto tem como objetivo democratizar o acesso a informações de manutenção industrial por meio de uma aplicação de inteligência artificial capaz de interpretar perguntas em linguagem natural e consultá-las em um banco de dados relacional. A solução visa atender operadores, engenheiros e gestores da planta industrial da empresa SiderTech Solutions.

A aplicação pode ser utilizada de duas formas:

- **Interface Web (Streamlit):** um chatbot acessível por navegador;
- **Notebook Interativo (Jupyter):** versão equivalente com execução célula a célula.

Tecnologias utilizadas:

- **LangGraph** para orquestração e controle do fluxo de agentes;
- **DeepSeek API** para tradução de linguagem natural em comandos SQL;
- **SQLite** como base de dados local (fornecida pela organização);
- **Streamlit** para construção de uma interface web interativa no estilo chatbot.

### ✅ Como Executar

1. Clone o repositório e entre na pasta do projeto:
```bash
git clone https://github.com/raiffhugo/SiderTech.git
cd SiderTech
```

2. Crie o arquivo `.env` com sua chave da DeepSeek:
```env
DEEPSEEK_API_KEY=sk-... (sua chave aqui)
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Coloque o arquivo `manutencao_industrial.db` na raiz do projeto.

5. Execute a aplicação de uma das seguintes formas:

Via Streamlit (interface web):
```bash
streamlit run app.py
```

Via Jupyter Notebook (modo interativo):
- Certifique-se de ter o Jupyter Notebook instalado. Caso não tenha, instale com:
```bash
pip install notebook
```
- Inicie o Jupyter Notebook:
```bash
jupyter notebook
```
- No navegador, navegue até o arquivo `sidertech.ipynb`;
- Execute as células sequencialmente para interagir com a aplicação.

### 💬 Exemplos de Perguntas Suportadas

- "Quais os tipos de equipamentos que tiveram manutenção nos últimos 3 meses?"
- "Qual o nome do técnico que trabalhou em mais ordens de manutenção?"
- "Qual técnico trabalhou na ordem 32?"
- "Qual a especialidade dele?" (feita em sequência)

### 🧠 Funcionalidades

- Interpretação de linguagem natural via modelo LLM;
- Geração e execução dinâmica de consultas SQL;
- Interface web estilo chatbot com histórico de conversas na sessão;
- Suporte a perguntas que envolvem múltiplas tabelas e junções;
- Memória de contexto (para sequências de perguntas).

### 🔒 Limitações

- A qualidade da resposta depende da precisão da geração de SQL pela API da DeepSeek;
- Falta tratamento avançado de exceções em consultas SQL malformadas;
- A memória de contexto ainda não é persistente entre sessões.

### 🚀 Sugestões de Melhoria

- Implementar validação semântica de consultas SQL antes da execução;
- Adicionar fallback com mensagens de erro explicativas e amigáveis;
- Explorar outras LLMs (ex: OpenAI, Mistral) como alternativas;
- Persistência do histórico de interações para análises futuras;
- Implementar um sistema de autenticação e controle de acesso por tipo de usuário (operador, engenheiro, gestor).

### 📎 Arquitetura da Solução

Um diagrama ilustrando a arquitetura do sistema está incluído no repositório em formato .pdf. Ele descreve:

- O fluxo de entrada da pergunta até a resposta final;
- Os principais componentes da aplicação (LLM, executor SQL, interface);
- Interações entre os módulos e o banco de dados.

### 📂 Estrutura do Projeto

.
├── .env                      # Exemplo de arquivo de ambiente
├── app.py                    # Interface principal em Streamlit
├── grafo.png           # Diagrama da solução
├── manutencao_industrial.db  # Banco de dados fornecido
├── README.md
├── requirements.txt
└── sidertech.ipynb           # Interface principal em Jupyter Notebook
