"""
Testes automatizados para o script de automação de reserva (automacao_reserva.py).
"""

import pytest
import io
import sys
from automacao_reserva import processar_chamados_pendentes, executar_loop
import backend.database as db


class TestAutomacaoReserva:
    """Valida o funcionamento do processo autônomo de triagem de reserva."""

    def setup_method(self):
        db.init_db()

    def test_nenhum_chamado_pendente_exibe_mensagem_esperada(self, monkeypatch, capsys):
        """Quando não há chamados sem laudo, deve imprimir 'Nenhum chamado pendente no momento'."""
        # Garante que nenhum chamado esteja sem laudo no momento do teste
        monkeypatch.setattr(db, "listar_chamados_sem_laudo", lambda: [])

        processados = processar_chamados_pendentes()
        captured = capsys.readouterr()

        assert processados == 0
        assert "Nenhum chamado pendente no momento" in captured.out

    def test_processamento_de_chamados_sem_laudo_com_grafo(self, capsys):
        """Cria chamado sem laudo e valida se a automação preenche com a triagem de grafo."""
        # Cria um chamado pendente (sem laudo inicial)
        num_chamado = db.criar_chamado(
            nome="Cliente Reserva",
            contato="11999990000",
            equipamento="Dell G15",
            relato="Notebook esquenta e desliga sozinho após abrir qualquer jogo pesado"
        )
        
        # Garante que o laudo esteja vazio inicialmente
        db.atualizar_laudo(num_chamado, "media", "")
        chamado_antes = db.buscar_chamado_por_id(num_chamado)
        assert chamado_antes["laudo"] == ""

        # Executa uma rodada da automação
        processados = processar_chamados_pendentes()
        captured = capsys.readouterr()

        assert processados >= 1
        chamado_depois = db.buscar_chamado_por_id(num_chamado)

        # Deve ter sido atualizado com o grafo
        assert chamado_depois["prioridade"] == "alta"
        assert "pasta térmica de fábrica ressecada e aletas obstruídas" in chamado_depois["laudo"]
        assert "Pasta Térmica Alta Condutividade, Thermal Pads" in chamado_depois["laudo"]

    def test_chamado_desconhecido_recebe_laudo_bancada(self):
        """Chamado sem padrão exato no grafo recebe 'necessário teste detalhado na bancada.'."""
        num_chamado = db.criar_chamado(
            nome="Cliente Desconhecido",
            contato="11888887777",
            equipamento="Teclado Mecânico RGB",
            relato="Algumas teclas param de funcionar aleatoriamente durante o dia"
        )
        db.atualizar_laudo(num_chamado, "media", "")

        processar_chamados_pendentes()

        chamado_depois = db.buscar_chamado_por_id(num_chamado)
        assert chamado_depois["prioridade"] == "media"
        assert "necessário teste detalhado na bancada." in chamado_depois["laudo"]

    def test_executar_loop_com_limite_de_iteracoes(self, capsys):
        """Valida que o loop executa e termina com parâmetro de iterações máximas."""
        executar_loop(intervalo=0.01, iteracoes_max=2)
        captured = capsys.readouterr()
        assert "AUTOMAÇÃO DE RESERVA" in captured.out

    def test_interrupcao_por_ctrl_c(self, monkeypatch, capsys):
        """Valida que KeyboardInterrupt é capturado e encerra com mensagem limpa."""
        def simular_ctrl_c(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(db, "listar_chamados_sem_laudo", simular_ctrl_c)

        with pytest.raises(SystemExit) as exc_info:
            executar_loop(intervalo=0.01)

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Automação finalizada com sucesso pelo usuário (Ctrl + C)" in captured.out

