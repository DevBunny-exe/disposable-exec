from datetime import datetime

from .db import get_conn


def save_result(
    execution_id: str,
    result: dict,
    key_id: str | None = None,
    user_id: str | None = None,
):
    conn = get_conn()
    existing = conn.execute(
        "SELECT execution_id, key_id, user_id, created_at FROM execution_results WHERE execution_id = ?",
        (execution_id,),
    ).fetchone()

    now = datetime.utcnow().isoformat() + "Z"
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code")
    duration = result.get("duration")

    if existing:
        current_key_id = key_id if key_id is not None else existing["key_id"]
        current_user_id = user_id if user_id is not None else existing["user_id"]
        current_created_at = existing["created_at"] or now

        conn.execute(
            """
            UPDATE execution_results
            SET key_id = ?, user_id = ?, stdout = ?, stderr = ?, exit_code = ?, duration = ?, created_at = ?
            WHERE execution_id = ?
            """,
            (
                current_key_id,
                current_user_id,
                stdout,
                stderr,
                exit_code,
                duration,
                current_created_at,
                execution_id,
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO execution_results
            (execution_id, key_id, user_id, stdout, stderr, exit_code, duration, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                key_id,
                user_id,
                stdout,
                stderr,
                exit_code,
                duration,
                now,
            ),
        )

    conn.commit()
    conn.close()


def get_result(
    execution_id: str,
    key_id: str | None = None,
    user_id: str | None = None,
):
    conn = get_conn()

    query = """
        SELECT execution_id, key_id, user_id, stdout, stderr, exit_code, duration, created_at
        FROM execution_results
        WHERE execution_id = ?
    """
    params = [execution_id]

    if key_id is not None:
        query += " AND key_id = ?"
        params.append(key_id)

    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)

    row = conn.execute(query, tuple(params)).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "execution_id": row["execution_id"],
        "stdout": row["stdout"],
        "stderr": row["stderr"],
        "exit_code": row["exit_code"],
        "duration": row["duration"],
        "created_at": row["created_at"],
    }