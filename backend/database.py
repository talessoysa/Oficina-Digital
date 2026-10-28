import sqlite3
from datetime import datetime
from pathlib import Path
import os
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "oficina.db"))

import sqlite3
from datetime import datetime
from pathlib import Path
import os
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "oficina.db"))

def get_connection() -> sqlite3.Connection:
    """
    Retorna uma conexão otimizada com o SQLite.
    timeout=15.0 para evitar conflitos de concorrência com processos paralelos.
    """
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa as tabelas e índices, ativando modo WAL para alta performance.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                contato TEXT NOT NULL,
                equipamento TEXT NOT NULL,
                relato TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'aberto',
                prioridade TEXT DEFAULT 'media',
                laudo TEXT DEFAULT '',
                data TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_laudo ON chamados(laudo);")
        conn.commit()
    finally:
        conn.close()

def criar_chamado(nome: str, contato: str, equipamento: str, relato: str) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        cursor.execute("""
            INSERT INTO chamados (nome, contato, equipamento, relato, status, prioridade, laudo, data)
            VALUES (?, ?, ?, ?, 'aberto', 'media', '', ?)
        """, (nome, contato, equipamento, relato, data_atual))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def buscar_chamado_por_id(numero: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chamados WHERE id = ?", (numero,))
        linha = cursor.fetchone()
        return dict(linha) if linha else None
    finally:
        conn.close()

def atualizar_laudo(numero: int, prioridade: str, laudo: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chamados 
            SET prioridade = ?, laudo = ? 
            WHERE id = ?
        """, (prioridade, laudo, numero))
        conn.commit()
    finally:
        conn.close()

def atualizar_status(numero: int, novo_status: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chamados 
            SET status = ? 
            WHERE id = ?
        """, (novo_status, numero))
        alterado = cursor.rowcount > 0
        conn.commit()
        return alterado
    finally:
        conn.close()

def listar_chamados_abertos() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chamados WHERE status = 'aberto' ORDER BY id ASC")
        linhas = cursor.fetchall()
        return [dict(l) for l in linhas]
    finally:
        conn.close()

def listar_chamados_sem_laudo() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chamados WHERE laudo = '' OR laudo IS NULL OR trim(laudo) = '' ORDER BY id ASC")
        linhas = cursor.fetchall()
        return [dict(l) for l in linhas]
    finally:
        conn.close()
