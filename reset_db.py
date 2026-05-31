"""
reset_db.py — Zera todos os dados de teste do bolão.
Mantém a estrutura das tabelas intacta.

Uso:
    python reset_db.py
"""
import sqlite3, os, sys

DB_PATH = os.environ.get("BOLAO_DB_PATH", "bolao.db")

if not os.path.exists(DB_PATH):
    print(f"⚠️  '{DB_PATH}' não encontrado — nada a fazer, banco está limpo.")
    sys.exit(0)

confirm = input(f"⚠️  Isso vai APAGAR TODOS os palpites de '{DB_PATH}'. Confirma? (sim/não): ")
if confirm.strip().lower() != "sim":
    print("Operação cancelada.")
    sys.exit(0)

conn = sqlite3.connect(DB_PATH)
conn.execute("DELETE FROM palpites")
conn.execute("DELETE FROM classificacao_palpites")
conn.execute("DELETE FROM classificacao_real")
conn.execute("DELETE FROM participantes")
conn.execute("UPDATE placares_reais SET gols_brasil=NULL, gols_adversario=NULL, encerrado=0")
conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('participantes','palpites','classificacao_palpites')")
conn.commit()
conn.close()

print("✅ Banco zerado! Estrutura preservada, pronto para o Streamlit Cloud.")
