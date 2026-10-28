"""
Testes de integração com pytest: abertura de chamado, triagem em segundo plano e persistência no banco SQLite.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
import backend.database as db

client = TestClient(app)


class TestAberturaEConsultaChamado:
    """Testa a criação do chamado, execução da triagem e persistência."""

    def setup_method(self):
        db.init_db()

    def test_abrir_chamado_e_triagem_automatica_em_segundo_plano(self):
        """Ao criar um chamado, a API agenda a triagem, que atualiza prioridade e laudo."""
        payload = {
            "nome": "Cidadão Teste",
            "contato": "11999998888",
            "equipamento": "Dell G15",
            "relato": "Notebook esquenta e desliga sozinho após abrir qualquer programa"
        }

        # 1. Criação do chamado (status code 201)
        response_post = client.post("/chamados", json=payload)
        assert response_post.status_code == 201
        dados_post = response_post.json()
        assert "numero" in dados_post
        numero_chamado = dados_post["numero"]
        assert dados_post["status"] == "aberto"

        # 2. Consulta do chamado recém-criado
        response_get = client.get(f"/chamados/{numero_chamado}")
        assert response_get.status_code == 200
        dados_get = response_get.json()

        assert dados_get["numero"] == numero_chamado
        assert dados_get["equipamento"] == "Dell G15"
        # Prioridade deve ter sido atualizada para 'alta' pelo background task
        assert dados_get["prioridade"] == "alta"
        # Laudo deve conter a causa e peças do grafo
        assert "pasta térmica de fábrica ressecada e aletas obstruídas" in dados_get["laudo"]
        assert "Pasta Térmica Alta Condutividade, Thermal Pads" in dados_get["laudo"]

    def test_chamado_caso_desconhecido(self):
        """Chamado sem caso no grafo recebe prioridade media e teste de bancada."""
        payload = {
            "nome": "Maria Santos",
            "contato": "21988887777",
            "equipamento": "Monitor LG",
            "relato": "Luz indicadora pisca e tela não acende imagem alguma"
        }

        response_post = client.post("/chamados", json=payload)
        assert response_post.status_code == 201
        numero = response_post.json()["numero"]

        response_get = client.get(f"/chamados/{numero}")
        assert response_get.status_code == 200
        dados = response_get.json()
        assert dados["prioridade"] == "media"
        assert dados["laudo"] == "necessário teste detalhado na bancada."

    @pytest.mark.parametrize("equipamento,relato,prioridade_esperada,termo_causa", [
        ("Dell G15", "O aparelho desliga sozinho após aquecer", "alta", "pasta térmica de fábrica ressecada"),
        ("Dell G15", "Depois de um raio o notebook não liga", "alta", "curto no circuito de carga"),
        ("Acer Nitro 5", "O sistema trava com tela azul frequentemente", "media", "oxidação nos contatos da memória RAM"),
        ("Acer Nitro 5", "Acende teclado mas fica em tela preta", "media", "cabo flat da tela rompido"),
        ("MacBook Air", "Conectado ao MagSafe mas a bateria não carrega", "media", "ciclos da bateria esgotados"),
        ("Desktop", "Durante gameplay o computador reinicia em jogos", "media", "fonte genérica sem potência suficiente"),
        ("Notebook", "Sistema com lentidão extrema para abrir arquivos", "media", "HD mecânico antigo com setores ruins"),
    ])
    def test_todos_os_7_casos_via_api(self, equipamento, relato, prioridade_esperada, termo_causa):
        """Valida a persistência e triagem dos 7 casos completos via requisição HTTP à API."""
        payload = {
            "nome": "Usuário Teste",
            "contato": "cliente@email.com",
            "equipamento": equipamento,
            "relato": relato
        }

        res_post = client.post("/chamados", json=payload)
        assert res_post.status_code == 201
        num = res_post.json()["numero"]

        res_get = client.get(f"/chamados/{num}")
        assert res_get.status_code == 200
        dados = res_get.json()

        assert dados["numero"] == num
        assert dados["prioridade"] == prioridade_esperada
        assert termo_causa in dados["laudo"]
