"""
Testes automatizados com pytest para o módulo de Triagem com Grafo de Conhecimento.
Executa 100% OFFLINE, sem necessidade de internet ou chaves de API.
"""

import pytest
import networkx as nx
from backend.triagem import (
    construir_grafo_conhecimento,
    buscar_no_grafo,
    realizar_triagem,
    normalizar,
    CASOS_CONHECIDOS
)


class TestGrafoConhecimento:
    """Valida a estrutura do Grafo de Conhecimento (NetworkX)."""

    def test_construcao_do_grafo(self):
        g = construir_grafo_conhecimento()
        assert isinstance(g, nx.DiGraph)
        assert len(g.nodes) > 0
        assert len(g.edges) > 0

    def test_todos_os_7_casos_estao_no_grafo(self):
        g = construir_grafo_conhecimento()
        for caso in CASOS_CONHECIDOS:
            aparelho = caso["aparelho"]
            sintoma = caso["sintoma"]
            causa = caso["causa"]
            pecas = caso["pecas"]

            # Verifica presença e tipo dos nós
            assert aparelho in g and g.nodes[aparelho]["tipo"] == "aparelho"
            assert sintoma in g and g.nodes[sintoma]["tipo"] == "sintoma"
            assert causa in g and g.nodes[causa]["tipo"] == "causa"
            assert pecas in g and g.nodes[pecas]["tipo"] == "peca"

            # Verifica as arestas e seus relacionamentos
            assert g.has_edge(aparelho, sintoma)
            assert g.edges[aparelho, sintoma]["relacao"] == "apresenta_sintoma"

            assert g.has_edge(sintoma, causa)
            assert g.edges[sintoma, causa]["relacao"] == "causado_por"

            assert g.has_edge(causa, pecas)
            assert g.edges[causa, pecas]["relacao"] == "requer_peca"


class TestCasosExatosTriagem:
    """Valida os 7 casos de triagem exigidos com prioridades e laudos."""

    def test_caso_1_dell_g15_desliga_sozinho(self):
        """Caso 1: Dell G15 | desliga sozinho -> Prioridade ALTA"""
        prioridade, laudo = realizar_triagem("Dell G15", "O notebook esquenta muito e desliga sozinho após jogar")
        assert prioridade == "alta"
        assert "pasta térmica de fábrica ressecada e aletas obstruídas" in laudo
        assert "Pasta Térmica Alta Condutividade, Thermal Pads" in laudo

    def test_caso_2_dell_g15_nao_liga(self):
        """Caso 2: Dell G15 | não liga -> Prioridade ALTA"""
        prioridade, laudo = realizar_triagem("Dell G15", "Aparelho não liga de jeito nenhum após tempestade")
        assert prioridade == "alta"
        assert "curto no circuito de carga (MOSFET de entrada)" in laudo
        assert "MOSFET Canal N 30V, Carregador 130W" in laudo

    def test_caso_3_acer_nitro_5_tela_azul(self):
        """Caso 3: Acer Nitro 5 | tela azul -> Prioridade MEDIA"""
        prioridade, laudo = realizar_triagem("Acer Nitro 5", "Apresentou tela azul durante o trabalho")
        assert prioridade == "media"
        assert "oxidação nos contatos da memória RAM" in laudo
        assert "Limpa Contato Isopropílico, Memória DDR4" in laudo

    def test_caso_4_acer_nitro_5_tela_preta(self):
        """Caso 4: Acer Nitro 5 | tela preta -> Prioridade MEDIA"""
        prioridade, laudo = realizar_triagem("Acer Nitro 5", "O computador liga os LEDs mas fica com tela preta")
        assert prioridade == "media"
        assert "cabo flat da tela rompido ou solto na dobradiça" in laudo
        assert "Cabo Flat EDP Nitro 5" in laudo

    def test_caso_5_macbook_air_bateria_nao_carrega(self):
        """Caso 5: MacBook Air | bateria não carrega -> Prioridade MEDIA"""
        prioridade, laudo = realizar_triagem("MacBook Air", "Plugado na tomada mas a bateria não carrega")
        assert prioridade == "media"
        assert "ciclos da bateria esgotados ou conector oxidado" in laudo
        assert "Bateria Original A1466" in laudo

    def test_caso_6_desktop_reinicia_em_jogos(self):
        """Caso 6: Desktop | reinicia em jogos -> Prioridade MEDIA"""
        prioridade, laudo = realizar_triagem("Desktop", "PC reinicia em jogos após 15 minutos")
        assert prioridade == "media"
        assert "fonte genérica sem potência suficiente" in laudo
        assert "Fonte ATX 600W 80 Plus" in laudo

    def test_caso_7_notebook_lentidao_extrema(self):
        """Caso 7: Notebook | lentidão extrema -> Prioridade MEDIA"""
        prioridade, laudo = realizar_triagem("Notebook", "Computador com lentidão extrema para abrir pastas e programas")
        assert prioridade == "media"
        assert "HD mecânico antigo com setores ruins" in laudo
        assert "SSD NVMe 500GB ou SATA" in laudo


class TestRegrasPrioridadeERobustez:
    """Valida regras de negócio de prioridade, variações de texto e casos desconhecidos."""

    def test_caso_desconhecido_gera_laudo_de_bancada(self):
        """Casos não encontrados no grafo devem ter prioridade media e laudo específico."""
        prioridade, laudo = realizar_triagem("Impressora Epson", "Papel atolado e luz piscando")
        assert prioridade == "media"
        assert laudo == "necessário teste detalhado na bancada."

    def test_aparelho_conhecido_com_defeito_desconhecido(self):
        """Aparelho catalogado com defeito não listado no grafo."""
        prioridade, laudo = realizar_triagem("MacBook Air", "Caiu suco no teclado e as teclas grudaram")
        assert prioridade == "media"
        assert laudo == "necessário teste detalhado na bancada."

    def test_insensibilidade_a_maiusculas_e_acentos(self):
        """Aceita variações sem acento e em maiúsculas."""
        # 'nao liga' sem acento
        prioridade, laudo = realizar_triagem("DELL g15", "o aparelho nao liga nada")
        assert prioridade == "alta"
        assert "MOSFET" in laudo

        # 'lentidao extrema' sem acento
        prioridade, laudo = realizar_triagem("NOTEBOOK", "muita lentidao extrema ao ligar")
        assert prioridade == "media"
        assert "SSD" in laudo

    def test_sinonimo_computador_desktop(self):
        """Sinônimos como 'PC Gamer' ou 'Computador' são mapeados para Desktop."""
        prioridade, laudo = realizar_triagem("PC Gamer", "computador reinicia em jogos pesados")
        assert prioridade == "media"
        assert "Fonte ATX 600W 80 Plus" in laudo

    def test_aparelho_desconhecido_com_termo_nao_liga_permanece_bancada(self):
        """Aparelho não constante no grafo (ex: TV) não pode casar falsamente com outro aparelho."""
        prioridade, laudo = realizar_triagem("TV Samsung", "Aparelho não liga de jeito nenhum")
        assert prioridade == "media"
        assert laudo == "necessário teste detalhado na bancada."

    def test_aparelho_mencionado_no_relato(self):
        """Se o usuário preencher aparelho genérico mas citar o modelo no relato, deve identificar."""
        prioridade, laudo = realizar_triagem("Notebook", "Meu Dell G15 esquenta e desliga sozinho")
        assert prioridade == "alta"
        assert "pasta térmica de fábrica ressecada e aletas obstruídas" in laudo
