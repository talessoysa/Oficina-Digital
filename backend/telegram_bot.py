import os
import requests
from dotenv import load_dotenv
import backend.database as db

# Carrega o arquivo .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

def enviar_mensagem_telegram(texto: str) -> bool:
    """
    Envia uma mensagem no Telegram. Se nao tiver token configurado,
    apenas imprime no terminal e nao gera erro.
    """
    if not TOKEN or not CHAT_ID:
        print("\n--- [AVISO TELEGRAM (Simulado)] ---")
        try:
            print(texto)
        except UnicodeEncodeError:
            print(texto.encode("ascii", errors="replace").decode("ascii"))
        print("------------------------------------\n")
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }

    try:
        resposta = requests.post(url, json=payload, timeout=5)
        return resposta.status_code == 200
    except Exception as e:
        print(f"[Erro ao conectar com Telegram]: {e}")
        return False

def notificar_novo_chamado(numero: int, equipamento: str, relato: str, prioridade: str, laudo: str):
    """
    Formata e envia a notificacao do novo chamado para o tecnico.
    """
    msg = (
        f"🛠️ *Novo Chamado #{numero} Aberto!*\n"
        f"💻 *Aparelho:* {equipamento}\n"
        f"⚠️ *Prioridade:* {prioridade.upper()}\n"
        f"📝 *Problema:* {relato}\n"
        f"🔍 *Laudo Preliminar:* {laudo}\n"
    )
    enviar_mensagem_telegram(msg)

def processar_comando_telegram(texto_comando: str, sender_chat_id: str) -> str:
    """
    Processa os comandos do tecnico.
    Comandos: /abertos, /ver 1, /andamento 1, /concluir 1
    """
    # Se configurado, so aceita comandos do chat do tecnico
    if CHAT_ID and str(sender_chat_id) != str(CHAT_ID):
        return "Acesso nao autorizado."

    partes = texto_comando.strip().split()
    if not partes:
        return "Comando vazio."

    cmd = partes[0].lower()

    if cmd == "/abertos":
        chamados = db.listar_chamados_abertos()
        if not chamados:
            return "Nenhum chamado aberto na fila no momento."
        linhas = ["📋 *Chamados Abertos:*"]
        for c in chamados:
            linhas.append(f"• #{c['id']} - {c['equipamento']} (Prioridade: {c['prioridade'].upper()})")
        return "\n".join(linhas)

    elif cmd == "/ver":
        if len(partes) < 2 or not partes[1].isdigit():
            return "Uso correto: /ver <numero_do_chamado>"
        numero = int(partes[1])
        c = db.buscar_chamado_por_id(numero)
        if not c:
            return f"Chamado #{numero} nao encontrado."
        return (
            f"🔍 *Detalhes do Chamado #{numero}*\n"
            f"💻 *Aparelho:* {c['equipamento']}\n"
            f"📌 *Status:* {c['status']}\n"
            f"⚠️ *Prioridade:* {c['prioridade'].upper()}\n"
            f"📝 *Relato:* {c['relato']}\n"
            f"📋 *Laudo:* {c['laudo'] or 'Aguardando laudo'}\n"
            f"📅 *Data:* {c['data']}"
        )

    elif cmd == "/andamento":
        if len(partes) < 2 or not partes[1].isdigit():
            return "Uso correto: /andamento <numero_do_chamado>"
        numero = int(partes[1])
        if db.atualizar_status(numero, "em_andamento"):
            return f"✅ Chamado #{numero} marcado como EM ANDAMENTO."
        return f"Chamado #{numero} nao encontrado."

    elif cmd == "/concluir":
        if len(partes) < 2 or not partes[1].isdigit():
            return "Uso correto: /concluir <numero_do_chamado>"
        numero = int(partes[1])
        if db.atualizar_status(numero, "concluido"):
            return f"🎉 Chamado #{numero} CONCLUÍDO com sucesso!"
        return f"Chamado #{numero} nao encontrado."

    else:
        return "Comandos disponiveis:\n/abertos\n/ver <numero>\n/andamento <numero>\n/concluir <numero>"

def rodar_bot_polling():
    """
    Roda um loop simples de escuta de mensagens do Telegram para responder comandos.
    """
    if not TOKEN:
        print("[Telegram Bot] Nenhum token configurado no .env. Bot desativado.")
        return

    print("[Telegram Bot] Iniciando escuta de comandos...")
    offset = 0
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    while True:
        try:
            resp = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25)
            if resp.status_code == 200:
                dados = resp.json()
                for item in dados.get("result", []):
                    offset = item["update_id"] + 1
                    msg = item.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    texto = msg.get("text", "")
                    if texto.startswith("/"):
                        resposta = processar_comando_telegram(texto, chat_id)
                        enviar_mensagem_telegram(resposta)
        except Exception as e:
            print(f"[Telegram Bot Polling Erro]: {e}")
