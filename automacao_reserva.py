"""
Automação de Reserva da Oficina Digital.

Executa em segundo plano ou em terminal separado:
1. A cada 5 segundos, busca no banco de dados chamados SEM laudo.
2. Realiza a triagem técnica automática com o Grafo de Conhecimento (NetworkX).
3. Preenche a prioridade e o laudo de cada chamado pendente.
4. Se não houver chamados pendentes, escreve: "Nenhum chamado pendente no momento".
5. Encerra de forma limpa e graciosa ao pressionar Ctrl + C.
"""

import sys
import time
import functools
from pathlib import Path

# Força flush imediato nos prints para exibição em tempo real
print = functools.partial(print, flush=True)

# Configura o stdout para UTF-8 compatível com terminais Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Garante que a raiz do projeto esteja no caminho de importação do Python
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import backend.database as db
from backend.triagem import realizar_triagem

INTERVALO_SEGUNDOS = 5


def processar_chamados_pendentes() -> int:
    """
    Busca chamados sem laudo, realiza a triagem com o grafo de conhecimento
    e atualiza a prioridade e o laudo no banco SQLite.
    
    Retorna a quantidade de chamados processados.
    """
    chamados_pendentes = db.listar_chamados_sem_laudo()

    if not chamados_pendentes:
        print("Nenhum chamado pendente no momento")
        return 0

    print(f"[{time.strftime('%H:%M:%S')}] {len(chamados_pendentes)} chamado(s) pendente(s) encontrado(s):")
    for chamado in chamados_pendentes:
        num = chamado["id"]
        equip = chamado["equipamento"]
        relato = chamado["relato"]

        # Executa a triagem usando o mesmo grafo de conhecimento
        prioridade, laudo = realizar_triagem(equip, relato)

        # Salva o resultado no banco
        db.atualizar_laudo(num, prioridade, laudo)

        print(f"  -> Chamado #{num} [{equip}]: Prioridade '{prioridade.upper()}' | Laudo: {laudo}")

    return len(chamados_pendentes)


def executar_loop(intervalo: float = INTERVALO_SEGUNDOS, iteracoes_max: int = None):
    """
    Loop principal da automação de reserva.
    Executa a cada `intervalo` segundos até ser interrompido por Ctrl + C.
    """
    print("=" * 65)
    print(">>> [AUTOMAÇÃO DE RESERVA] Triagem Automática com Grafo <<<")
    print(f"[*] Intervalo de verificação: {intervalo} segundos")
    print("[*] Pressione Ctrl + C para encerrar a qualquer momento")
    print("=" * 65)

    contador = 0
    try:
        while True:
            processar_chamados_pendentes()
            contador += 1
            if iteracoes_max is not None and contador >= iteracoes_max:
                break
            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("\n[Encerrado] Automação finalizada com sucesso pelo usuário (Ctrl + C).")
        sys.exit(0)


if __name__ == "__main__":
    db.init_db()
    executar_loop()
