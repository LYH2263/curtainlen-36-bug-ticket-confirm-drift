from app.db import connect

def get_all():
    c = connect()
    try:
        return {r["key"]: r["value"] for r in c.execute("SELECT key,value FROM settings").fetchall()}
    finally:
        c.close()
