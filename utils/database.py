"""
database.py — Suporte dual: PostgreSQL (Supabase/produção) + SQLite (local).

Em produção no Streamlit Cloud:
  - Define DATABASE_URL nos Secrets do Streamlit com a connection string do Supabase
  - Os dados persistem para sempre no PostgreSQL gratuito do Supabase

Localmente:
  - Sem DATABASE_URL → usa SQLite (bolao.db)
  - Tudo funciona igual, sem nenhuma configuração extra
"""

import os
import threading
from contextlib import contextmanager

# ── Detecta qual banco usar ───────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Supabase entrega URLs com prefixo "postgres://", psycopg2 precisa "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)

# ── Conexão SQLite (local) ────────────────────────────────
if not USE_POSTGRES:
    import sqlite3
    DB_PATH = os.environ.get("BOLAO_DB_PATH", "bolao.db")
    _local  = threading.local()

    def _get_conn():
        if not hasattr(_local, "conn") or _local.conn is None:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
            conn.row_factory = sqlite3.Row
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

# ── Conexão PostgreSQL (produção) ─────────────────────────
else:
    import psycopg2
    import psycopg2.extras
    from psycopg2.pool import ThreadedConnectionPool

    _pg_pool = None

    def _get_pool():
        global _pg_pool
        if _pg_pool is None:
            _pg_pool = ThreadedConnectionPool(1, 10, DATABASE_URL)
        return _pg_pool

    @contextmanager
    def _transaction():
        pool = _get_pool()
        conn = pool.getconn()
        try:
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)

    def _get_conn():
        """Para leituras simples fora de transação."""
        pool = _get_pool()
        return pool.getconn()

    def _put_conn(conn):
        _get_pool().putconn(conn)


# ── Helpers para normalizar resultados ───────────────────
def _fetchall(cursor):
    """Retorna lista de dicts independente do banco."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def _fetchone(cursor):
    cols = [d[0] for d in cursor.description]
    row  = cursor.fetchone()
    return dict(zip(cols, row)) if row else None


# ── SQL adaptado (SQLite ↔ PostgreSQL) ───────────────────
def _sql(sqlite_sql: str) -> str:
    """Converte SQL SQLite para PostgreSQL quando necessário."""
    if not USE_POSTGRES:
        return sqlite_sql
    # %s placeholder (psycopg2) vs ? (sqlite3)
    return sqlite_sql.replace("?", "%s")


# ═══════════════════════════════════════════════════════════
#  INIT / MIGRATIONS
# ═══════════════════════════════════════════════════════════

def init_db():
    if USE_POSTGRES:
        _init_postgres()
    else:
        _init_sqlite()


def _init_sqlite():
    import sqlite3
    conn = _get_conn()
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}

    if "schema_version" not in tables:
        current = 0
    else:
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        current = row[0] if row else 0

    migrations = _get_migrations_sqlite()
    for i, sql in enumerate(migrations):
        if current < i + 1:
            try:
                conn.executescript(sql)
                current = i + 1
            except Exception as e:
                import sys
                print(f"[bolao] Migração SQLite v{i+1} falhou: {e}", file=sys.stderr)


def _init_postgres():
    with _transaction() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cur.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = cur.fetchone()
        current = row[0] if row else 0

        migrations = _get_migrations_postgres()
        for i, sql in enumerate(migrations):
            if current < i + 1:
                try:
                    cur.execute(sql)
                    if current == 0:
                        cur.execute("INSERT INTO schema_version VALUES (%s)", (i+1,))
                    else:
                        cur.execute("UPDATE schema_version SET version = %s", (i+1,))
                    current = i + 1
                except Exception as e:
                    import sys
                    print(f"[bolao] Migração PG v{i+1} falhou: {e}", file=sys.stderr)
                    conn.rollback()


def _get_migrations_sqlite():
    return [
        # v1
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
            gols_brasil     INTEGER NOT NULL CHECK(gols_brasil >= 0),
            gols_adversario INTEGER NOT NULL CHECK(gols_adversario >= 0),
            enviado_em      DATETIME DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (participante_id) REFERENCES participantes(id),
            UNIQUE(participante_id, jogo)
        );

        CREATE TABLE IF NOT EXISTS classificacao_palpites (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL UNIQUE,
            primeiro TEXT NOT NULL, segundo TEXT NOT NULL,
            terceiro TEXT NOT NULL, quarto   TEXT NOT NULL,
            enviado_em DATETIME DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (participante_id) REFERENCES participantes(id)
        );

        CREATE TABLE IF NOT EXISTS placares_reais (
            jogo        TEXT PRIMARY KEY CHECK(jogo IN ('jogo1','jogo2','jogo3')),
            gols_brasil INTEGER, gols_adversario INTEGER,
            encerrado   INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS classificacao_real (
            posicao INTEGER PRIMARY KEY CHECK(posicao BETWEEN 1 AND 4),
            time    TEXT NOT NULL
        );

        INSERT OR IGNORE INTO placares_reais (jogo, encerrado) VALUES ('jogo1', 0);
        INSERT OR IGNORE INTO placares_reais (jogo, encerrado) VALUES ('jogo2', 0);
        INSERT OR IGNORE INTO placares_reais (jogo, encerrado) VALUES ('jogo3', 0);

        UPDATE schema_version SET version = 1;
        """,
        # v2 — índices
        """
        CREATE INDEX IF NOT EXISTS idx_pal_part ON palpites(participante_id);
        CREATE INDEX IF NOT EXISTS idx_pal_jogo ON palpites(jogo);
        UPDATE schema_version SET version = 2;
        """,
    ]


def _get_migrations_postgres():
    return [
        # v1
        """
        CREATE TABLE IF NOT EXISTS participantes (
            id         SERIAL PRIMARY KEY,
            nome       TEXT   NOT NULL,
            enviado_em TIMESTAMP DEFAULT NOW(),
            UNIQUE(nome)
        );

        CREATE TABLE IF NOT EXISTS palpites (
            id              SERIAL PRIMARY KEY,
            participante_id INTEGER NOT NULL REFERENCES participantes(id),
            jogo            TEXT    NOT NULL CHECK(jogo IN ('jogo1','jogo2','jogo3')),
            gols_brasil     INTEGER NOT NULL CHECK(gols_brasil >= 0),
            gols_adversario INTEGER NOT NULL CHECK(gols_adversario >= 0),
            enviado_em      TIMESTAMP DEFAULT NOW(),
            UNIQUE(participante_id, jogo)
        );

        CREATE TABLE IF NOT EXISTS classificacao_palpites (
            id              SERIAL PRIMARY KEY,
            participante_id INTEGER NOT NULL UNIQUE REFERENCES participantes(id),
            primeiro TEXT NOT NULL, segundo TEXT NOT NULL,
            terceiro TEXT NOT NULL, quarto  TEXT NOT NULL,
            enviado_em TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS placares_reais (
            jogo        TEXT PRIMARY KEY CHECK(jogo IN ('jogo1','jogo2','jogo3')),
            gols_brasil INTEGER, gols_adversario INTEGER,
            encerrado   INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS classificacao_real (
            posicao INTEGER PRIMARY KEY CHECK(posicao BETWEEN 1 AND 4),
            time    TEXT NOT NULL
        );

        INSERT INTO placares_reais (jogo, encerrado) VALUES ('jogo1',0),('jogo2',0),('jogo3',0)
        ON CONFLICT (jogo) DO NOTHING;
        """,
        # v2 — índices
        """
        CREATE INDEX IF NOT EXISTS idx_pal_part ON palpites(participante_id);
        CREATE INDEX IF NOT EXISTS idx_pal_jogo ON palpites(jogo);
        """,
    ]


# ═══════════════════════════════════════════════════════════
#  LEITURAS  (SQLite e PostgreSQL idênticos externamente)
# ═══════════════════════════════════════════════════════════

def get_all_participantes():
    if USE_POSTGRES:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT id, nome, enviado_em FROM participantes ORDER BY enviado_em")
        rows = _fetchall(cur)
        _put_conn(conn)
        return [(r["id"], r["nome"], str(r["enviado_em"])) for r in rows]
    else:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT id, nome, enviado_em FROM participantes ORDER BY enviado_em"
        ).fetchall()
        return [(r["id"], r["nome"], r["enviado_em"]) for r in rows]


def get_palpites_by_participante(pid: int) -> dict:
    if USE_POSTGRES:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "SELECT jogo, gols_brasil, gols_adversario FROM palpites WHERE participante_id=%s",
            (pid,)
        )
        rows = _fetchall(cur)
        _put_conn(conn)
    else:
        rows = _get_conn().execute(
            "SELECT jogo, gols_brasil, gols_adversario FROM palpites WHERE participante_id=?",
            (pid,)
        ).fetchall()
        rows = [dict(r) for r in rows]
    return {r["jogo"]: (r["gols_brasil"], r["gols_adversario"]) for r in rows}


def get_classificacao_palpite(pid: int):
    if USE_POSTGRES:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute(
            "SELECT primeiro, segundo, terceiro, quarto FROM classificacao_palpites WHERE participante_id=%s",
            (pid,)
        )
        row = _fetchone(cur)
        _put_conn(conn)
        return (row["primeiro"], row["segundo"], row["terceiro"], row["quarto"]) if row else None
    else:
        row = _get_conn().execute(
            "SELECT primeiro, segundo, terceiro, quarto FROM classificacao_palpites WHERE participante_id=?",
            (pid,)
        ).fetchone()
        return tuple(row) if row else None


def get_placares_reais() -> dict:
    if USE_POSTGRES:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT jogo, gols_brasil, gols_adversario, encerrado FROM placares_reais")
        rows = _fetchall(cur)
        _put_conn(conn)
    else:
        rows = [dict(r) for r in _get_conn().execute(
            "SELECT jogo, gols_brasil, gols_adversario, encerrado FROM placares_reais"
        ).fetchall()]
    return {
        r["jogo"]: {
            "brasil":     r["gols_brasil"],
            "adversario": r["gols_adversario"],
            "encerrado":  r["encerrado"],
        }
        for r in rows
    }


def get_classificacao_real() -> dict:
    if USE_POSTGRES:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT posicao, time FROM classificacao_real ORDER BY posicao")
        rows = _fetchall(cur)
        _put_conn(conn)
    else:
        rows = [dict(r) for r in _get_conn().execute(
            "SELECT posicao, time FROM classificacao_real ORDER BY posicao"
        ).fetchall()]
    return {r["posicao"]: r["time"] for r in rows}


def palpite_enviado(nome: str) -> bool:
    if USE_POSTGRES:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM participantes WHERE LOWER(nome)=LOWER(%s)", (nome,))
        row = _fetchone(cur)
        if not row:
            _put_conn(conn)
            return False
        pid = row["id"]
        cur.execute("SELECT COUNT(*) as c FROM palpites WHERE participante_id=%s", (pid,))
        count = cur.fetchone()[0]
        _put_conn(conn)
        return count > 0
    else:
        conn = _get_conn()
        row  = conn.execute("SELECT id FROM participantes WHERE nome=?", (nome,)).fetchone()
        if not row:
            return False
        count = conn.execute(
            "SELECT COUNT(*) as c FROM palpites WHERE participante_id=?", (row["id"],)
        ).fetchone()["c"]
        return count > 0


def get_palpite_completo_por_nome(nome: str):
    if USE_POSTGRES:
        conn = _get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT id, enviado_em FROM participantes WHERE LOWER(nome)=LOWER(%s)", (nome,))
        row = _fetchone(cur)
        _put_conn(conn)
        if not row:
            return None
        pid = row["id"]
    else:
        conn = _get_conn()
        row  = conn.execute("SELECT id, enviado_em FROM participantes WHERE nome=?", (nome,)).fetchone()
        if not row:
            return None
        pid = row["id"]
        row = dict(row)
    return {
        "pid":        pid,
        "enviado_em": str(row["enviado_em"]),
        "palpites":   get_palpites_by_participante(pid),
        "classif":    get_classificacao_palpite(pid),
    }


# ═══════════════════════════════════════════════════════════
#  ESCRITAS
# ═══════════════════════════════════════════════════════════

def save_palpite(nome: str, palpites: dict, classificacao: tuple) -> bool:
    with _transaction() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            # Upsert participante (ignora se já existe)
            cur.execute(
                "INSERT INTO participantes (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING",
                (nome,)
            )
            cur.execute("SELECT id FROM participantes WHERE LOWER(nome)=LOWER(%s)", (nome,))
            row = cur.fetchone()
            pid = row[0]

            cur.execute("SELECT COUNT(*) FROM palpites WHERE participante_id=%s", (pid,))
            if cur.fetchone()[0] > 0:
                return False

            for jogo, (gb, ga) in palpites.items():
                cur.execute(
                    """INSERT INTO palpites (participante_id, jogo, gols_brasil, gols_adversario)
                       VALUES (%s, %s, %s, %s) ON CONFLICT (participante_id, jogo) DO NOTHING""",
                    (pid, jogo, gb, ga)
                )
            cur.execute(
                """INSERT INTO classificacao_palpites
                   (participante_id, primeiro, segundo, terceiro, quarto)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (participante_id) DO NOTHING""",
                (pid, *classificacao)
            )
        else:
            conn.execute("INSERT OR IGNORE INTO participantes (nome) VALUES (?)", (nome,))
            row = conn.execute("SELECT id FROM participantes WHERE nome=?", (nome,)).fetchone()
            pid = row["id"]

            already = conn.execute(
                "SELECT COUNT(*) as c FROM palpites WHERE participante_id=?", (pid,)
            ).fetchone()["c"]
            if already > 0:
                return False

            for jogo, (gb, ga) in palpites.items():
                conn.execute(
                    """INSERT OR IGNORE INTO palpites
                       (participante_id, jogo, gols_brasil, gols_adversario)
                       VALUES (?, ?, ?, ?)""",
                    (pid, jogo, gb, ga)
                )
            conn.execute(
                """INSERT OR IGNORE INTO classificacao_palpites
                   (participante_id, primeiro, segundo, terceiro, quarto)
                   VALUES (?, ?, ?, ?, ?)""",
                (pid, *classificacao)
            )
    return True


def save_placar_real(jogo: str, gols_brasil: int, gols_adversario: int):
    with _transaction() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(
                "UPDATE placares_reais SET gols_brasil=%s, gols_adversario=%s, encerrado=1 WHERE jogo=%s",
                (gols_brasil, gols_adversario, jogo)
            )
        else:
            conn.execute(
                "UPDATE placares_reais SET gols_brasil=?, gols_adversario=?, encerrado=1 WHERE jogo=?",
                (gols_brasil, gols_adversario, jogo)
            )


def save_classificacao_real(ordem: list):
    with _transaction() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            for i, time in enumerate(ordem, 1):
                cur.execute(
                    """INSERT INTO classificacao_real (posicao, time) VALUES (%s, %s)
                       ON CONFLICT (posicao) DO UPDATE SET time=EXCLUDED.time""",
                    (i, time)
                )
        else:
            for i, time in enumerate(ordem, 1):
                conn.execute(
                    """INSERT INTO classificacao_real (posicao, time) VALUES (?, ?)
                       ON CONFLICT(posicao) DO UPDATE SET time=excluded.time""",
                    (i, time)
                )
