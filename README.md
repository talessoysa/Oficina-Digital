# 🛠️ Oficina Digital

Sistema unificado para abertura, acompanhamento e triagem técnica automática de chamados de assistência de computadores, desenvolvido com **FastAPI**, **NetworkX (Grafo de Conhecimento)**, **SQLite** e interface web moderna no padrão Gov.br.

---

## 🚀 Funcionalidades Principais

1. **Portal Web do Cidadão (Gov.br):** Interface limpa, responsiva e com suporte a acessibilidade (alto contraste) para abertura e consulta de chamados.
2. **API REST (FastAPI):** Endpoints assíncronos e documentados via Swagger/OpenAPI para cadastro e consulta de ordens de serviço.
3. **Triagem Automática por Grafo de Conhecimento (Offline):** Modelagem ontológica com NetworkX conectando `(Aparelho) -> (Sintoma) -> (Causa) -> (Peça Sugerida)`, determinando prioridade técnica e laudo preliminar em milissegundos sem custos de API ou dependência de internet.
4. **Automação de Reserva (Daemon):** Processo separado de contingência que verifica a cada 5 segundos qualquer chamado pendente sem laudo no banco SQLite e processa a triagem com segurança.
5. **Integração com Telegram Bot:** Notificações automáticas ao técnico para cada chamado aberto e consulta de chamados em tempo real via comandos `/abertos`, `/ver`, `/andamento` e `/concluir`.

---

## 🏗️ Estrutura do Projeto

```text
├── automacao_reserva.py       # Script da automação de reserva periódica
├── iniciar_automacao.bat      # Atalho Windows para execução da automação
├── requirements.txt           # Dependências do projeto Python
├── .env.example               # Exemplo de variáveis de ambiente
├── .gitignore                 # Filtro de segurança para arquivos sensíveis
├── backend/
│   ├── main.py                # Servidor FastAPI e rotas REST
│   ├── database.py            # Camada de banco de dados SQLite com WAL mode
│   ├── triagem.py             # Grafo de conhecimento ontológico (NetworkX)
│   └── telegram_bot.py        # Integração e polling do bot Telegram
├── site/
│   ├── index.html             # Interface Web do portal
│   ├── style.css              # Estilos visuais e acessibilidade
│   └── script.js              # Integração Frontend com a API REST
└── tests/
    ├── test_api_triagem.py    # Testes de integração da API
    ├── test_triagem.py        # Testes unitários do grafo de conhecimento
    └── test_automacao_reserva.py # Testes do processo de contingência
```

---

## 💻 Como Executar

### 1. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar a API Principal
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Acesse a API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Documentação Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Acessar o Portal Web
Abra o arquivo `site/index.html` em seu navegador preferido (Brave, Chrome, Firefox, Edge).

### 4. Executar a Automação de Reserva
Em um terminal separado:
```bash
python automacao_reserva.py
```
*(No Windows, você também pode dar dois cliques em `iniciar_automacao.bat`)*

---

## 🧪 Testes Automatizados

O projeto conta com suíte de testes completa utilizando **pytest**:
```bash
pytest
```

