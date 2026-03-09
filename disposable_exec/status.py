from .db import get_conn


def set_status(execution_id, status):
    conn = get_conn()
    existing = conn.execute(
        "SELECT execution_id FROM execution_status WHERE execution_id = ?",
        (execution_id,),
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE execution_status SET status = ? WHERE execution_id = ?",
            (status, execution_id),
        )
    else:
        conn.execute(
            "INSERT INTO execution_status (execution_id, status) VALUES (?, ?)",
            (execution_id, status),
        )

    conn.commit()
    conn.close()


def get_status(execution_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT status FROM execution_status WHERE execution_id = ?",
        (execution_id,),
    ).fetchone()
    conn.close()

    return row["status"] if row else None