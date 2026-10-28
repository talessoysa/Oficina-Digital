from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

import backend.database as db
from backend.triagem import realizar_triagem
from backend.telegram_bot import notificar_novo_chamado

# Inicializa o banco de dados
db.init_db()

app = FastAPI(
    title="Oficina Digital API",
    description="API para abertura e acompanhamento de chamados da oficina de computadores",
    version="1.0.0"
)

# Libera o CORS para o site local conseguir conversar com a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados
class CriarChamadoInput(BaseModel):
    nome: str = Field(..., min_length=2, description="Nome do cliente (minimo 2 letras)")
    contato: str = Field(..., min_length=5, description="Telefone ou e-mail (minimo 5 letras)")
    equipamento: str = Field(..., min_length=2, description="Aparelho a ser consertado (minimo 2 letras)")
    relato: str = Field(..., min_length=10, max_length=1000, description="Descricao do defeito (10 a 1000 letras)")

class CriarChamadoOutput(BaseModel):
    numero: int
    status: str

class ConsultarChamadoOutput(BaseModel):
    numero: int
    equipamento: str
    status: str
    prioridade: str
    laudo: str
    data: str

def processar_triagem_e_aviso(numero: int, equipamento: str, relato: str):
    """
    Funcao executada em segundo plano:
    Gera o laudo com o grafo de conhecimento e envia notificacao.
    """
    prioridade, laudo = realizar_triagem(equipamento, relato)
    db.atualizar_laudo(numero, prioridade, laudo)
    notificar_novo_chamado(numero, equipamento, relato, prioridade, laudo)

@app.get("/")
def raiz():
    return {"mensagem": "API da Oficina Digital está ativa!"}

@app.post("/chamados", response_model=CriarChamadoOutput, status_code=201)
def rota_criar_chamado(dados: CriarChamadoInput, background_tasks: BackgroundTasks):
    """
    Cria um novo chamado e agenda a triagem automatica.
    """
    numero = db.criar_chamado(
        nome=dados.nome,
        contato=dados.contato,
        equipamento=dados.equipamento,
        relato=dados.relato
    )

    # Executa a triagem e o aviso ao tecnico em segundo plano
    background_tasks.add_task(
        processar_triagem_e_aviso,
        numero=numero,
        equipamento=dados.equipamento,
        relato=dados.relato
    )

    return {
        "numero": numero,
        "status": "aberto"
    }

@app.get("/chamados/{numero}", response_model=ConsultarChamadoOutput)
def rota_consultar_chamado(numero: int):
    """
    Consulta o status e o laudo de um chamado existente.
    Nao devolve nome nem contato por privacidade.
    """
    chamado = db.buscar_chamado_por_id(numero)
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    return {
        "numero": chamado["id"],
        "equipamento": chamado["equipamento"],
        "status": chamado["status"],
        "prioridade": chamado["prioridade"],
        "laudo": chamado["laudo"] or "",
        "data": chamado["data"]
    }
