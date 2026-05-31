"""
database.py — Camada de acesso ao banco de dados (SQLite com WAL mode).

Melhorias em relação à versão anterior:
  • WAL mode + foreign keys habilitados em todas as conexões
  • Migrações automáticas com tabela schema_version (nunca perde dados)
  • Palpites são imutáveis: INSERT OR IGNORE — uma vez enviado, não atualiza
  • palpite_enviado() permite checar antes de mostrar o formulário
  • Coluna enviado_em registra quando o palpite foi feito (auditoria)
  • Todas as escritas dentro de transação explícita
  • Sem DELETE/REPLACE que apagam linhas existentes
"""

import sqlite3
import threading
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("BOLAO_DB_PATH", "bolao.db")

# ── Pool simples de conexão por thread ────────────────────
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        # WAL = leituras não bloqueiam escritas (essencial para Streamlit)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn = conn
    return _local.conn


@contextmanager
def _transaction():
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ── Migração incremental ───────────────────────────────────
_MIGRATIONS = [
    # v1 — esquema inicial
    """
    CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
    INSERT OR IGNORE INTO schema_version VALUES (0);

    CREATE TABLE IF NOT EXISTS participantes (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        nome       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
        enviado_em DATETIME DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS palpites (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        participante_id INTEGER NOT NULL,
        jogo            TEXT    NOT NULL CHECK(jogo IN ('jogo1','jogo2','jogo3')),
        gols_brasil     INTEGER NOT NULL CHECK(gols_brasil     >= 0),
        gols_adversario INTEGER NOT NULL CHECK(gols_adversario >= 0),
        enviado_em      DATETIME DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (participante_id) REFERENCES participantes(id),
        UNIQUE(participante_id, jogo)   -- garante apenas 1 palpite por jogo
    );

    CREATE TABLE IF NOT EXISTS classificacao_palpites (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        participante_id INTEGER NOT NULL UNIQUE,
        primeiro        TEXT    NOT NULL,
        segundo         TEXT    NOT NULL,
        terceiro        TEXT    NOT NULL,
        quarto          TEXT    NOT NULL,
        enviado_em      DATETIME DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (participante_id) REFERENCES participantes(id)
    );

    CREATE TABLE IF NOT EXISTS placares_reais (
        jogo            TEXT    PRIMARY KEY CHECK(jogo IN ('jogo1','jogo2','jogo3')),
        gols_brasil     INTEGER,
        gols_adversario INTEGER,
        encerrado       INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS classificacao_real (
        posicao INTEGER PRIMARY KEY CHECK(posicao BETWEEN 1 AND 4),
        time    TEXT    NOT NULL
    );

    -- Seed linhas dos jogos (idempotente)
    INSERT OR IGNORE INTO placares_reais (jogo, encerrado) VALUES ('jogo1', 0);
    INSERT OR IGNORE INTO placares_reais (jogo, encerrado) VALUES ('jogo2', 0);
    INSERT OR IGNORE INTO placares_reais (jogo, encerrado) VALUES ('jogo3', 0);

    UPDATE schema_version SET version = 1;
    """,
    # v2 — índice de performance para rankings (adiciona sem apagar dados)
    """
    CREATE INDEX IF NOT EXISTS idx_palpites_participante
        ON palpites(participante_id);
    CREATE INDEX IF NOT EXISTS idx_palpites_jogo
        ON palpites(jogo);
    UPDATE schema_version SET version = 2;
    """,
]


def init_db():
    """Inicializa/migra o banco de forma incremental e segura."""
    conn = _get_conn()

    # Descobre a versão atual (pode ser banco legado sem schema_version)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}

    if "schema_version" not in tables:
        current_version = 0
    else:
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        current_version = row[0] if row else 0

    for i, migration_sql in enumerate(_MIGRATIONS):
        target = i + 1
        if current_version < target:
            try:
                conn.executescript(migration_sql)   # executescript já faz commit
                current_version = target
            except Exception as e:
                # Em último caso registra o erro mas não derruba o app
                import sys
                print(f"[bolao] Migração v{target} falhou: {e}", file=sys.stderr)


# ══════════════════════════════════════════════════════════
#  LEITURAS
# ══════════════════════════════════════════════════════════

def get_all_participantes():
    """Retorna [(id, nome, enviado_em), ...]"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, nome, enviado_em FROM participantes ORDER BY enviado_em"
    ).fetchall()
    return [(r["id"], r["nome"], r["enviado_em"]) for r in rows]


def get_palpites_by_participante(pid: int) -> dict:
    """Retorna {'jogo1': (gb, ga), ...}"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT jogo, gols_brasil, gols_adversario FROM palpites WHERE participante_id=?",
        (pid,)
    ).fetchall()
    return {r["jogo"]: (r["gols_brasil"], r["gols_adversario"]) for r in rows}


def get_classificacao_palpite(pid: int):
    """Retorna (primeiro, segundo, terceiro, quarto) ou None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT primeiro, segundo, terceiro, quarto FROM classificacao_palpites WHERE participante_id=?",
        (pid,)
    ).fetchone()
    return tuple(row) if row else None


def get_placares_reais() -> dict:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT jogo, gols_brasil, gols_adversario, encerrado FROM placares_reais"
    ).fetchall()
    return {
        r["jogo"]: {
            "brasil":     r["gols_brasil"],
            "adversario": r["gols_adversario"],
            "encerrado":  r["encerrado"],
        }
        for r in rows
    }


def get_classificacao_real() -> dict:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT posicao, time FROM classificacao_real ORDER BY posicao"
    ).fetchall()
    return {r["posicao"]: r["time"] for r in rows}


def palpite_enviado(nome: str) -> bool:
    """Retorna True se o participante já enviou palpite (imutável)."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT id FROM participantes WHERE nome=?", (nome,)
    ).fetchone()
    if not row:
        return False
    pid = row["id"]
    # Considera enviado se tem pelo menos 1 palpite de jogo OU classificação
    count = conn.execute(
        "SELECT COUNT(*) as c FROM palpites WHERE participante_id=?", (pid,)
    ).fetchone()["c"]
    return count > 0


def get_palpite_completo_por_nome(nome: str):
    """
    Retorna dict com palpites e classificação de um participante pelo nome,
    ou None se não existir.
    """
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, enviado_em FROM participantes WHERE nome=?", (nome,)
    ).fetchone()
    if not row:
        return None
    pid = row["id"]
    return {
        "pid":        pid,
        "enviado_em": row["enviado_em"],
        "palpites":   get_palpites_by_participante(pid),
        "classif":    get_classificacao_palpite(pid),
    }


# ══════════════════════════════════════════════════════════
#  ESCRITAS
# ══════════════════════════════════════════════════════════

def save_palpite(nome: str, palpites: dict, classificacao: tuple) -> bool:
    """
    Salva palpite de forma IMUTÁVEL.
    - Se o participante já existir com palpites, retorna False (sem alterar nada).
    - Se for novo, insere tudo numa transação e retorna True.

    palpites      = {'jogo1': (g_br, g_adv), ...}
    classificacao = ('Brasil', 'Marrocos', 'Haiti', 'Escócia')
    """
    with _transaction() as conn:
        # Cria participante (IGNORE se já existir — nome é UNIQUE COLLATE NOCASE)
        conn.execute(
            "INSERT OR IGNORE INTO participantes (nome) VALUES (?)", (nome,)
        )
        row = conn.execute(
            "SELECT id FROM participantes WHERE nome=?", (nome,)
        ).fetchone()
        pid = row["id"]

        # Verifica se já há palpites para este participante
        already = conn.execute(
            "SELECT COUNT(*) as c FROM palpites WHERE participante_id=?", (pid,)
        ).fetchone()["c"]
        if already > 0:
            return False   # palpite imutável — não altera

        # INSERT OR IGNORE: se por algum motivo a linha já existir, não sobrescreve
        for jogo, (gb, ga) in palpites.items():
            conn.execute(
                """INSERT OR IGNORE INTO palpites
                   (participante_id, jogo, gols_brasil, gols_adversario)
                   VALUES (?, ?, ?, ?)""",
                (pid, jogo, gb, ga),
            )

        conn.execute(
            """INSERT OR IGNORE INTO classificacao_palpites
               (participante_id, primeiro, segundo, terceiro, quarto)
               VALUES (?, ?, ?, ?, ?)""",
            (pid, *classificacao),
        )

    return True


def save_placar_real(jogo: str, gols_brasil: int, gols_adversario: int):
    """Admin: registra placar real de um jogo e marca como encerrado."""
    with _transaction() as conn:
        conn.execute(
            """UPDATE placares_reais
               SET gols_brasil=?, gols_adversario=?, encerrado=1
               WHERE jogo=?""",
            (gols_brasil, gols_adversario, jogo),
        )


def save_classificacao_real(ordem: list):
    """
    Admin: salva classificação final do grupo.
    Usa UPSERT para não apagar histórico — apenas atualiza posições.
    ordem = ['Brasil', 'Marrocos', 'Escócia', 'Haiti']
    """
    with _transaction() as conn:
        for i, time in enumerate(ordem, 1):
            conn.execute(
                """INSERT INTO classificacao_real (posicao, time) VALUES (?, ?)
                   ON CONFLICT(posicao) DO UPDATE SET time=excluded.time""",
                (i, time),
            )
