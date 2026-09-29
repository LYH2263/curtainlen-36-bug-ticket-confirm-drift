from app.db import connect


def get_by_no(c, ticket_no):
    r = c.execute("SELECT * FROM tickets WHERE ticket_no=?", (ticket_no,)).fetchone()
    return dict(r) if r else None


def get(ticket_no):
    c = connect()
    try:
        return get_by_no(c, ticket_no)
    finally:
        c.close()


def count():
    c = connect()
    try:
        return c.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"]
    finally:
        c.close()
