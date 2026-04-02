from disposable_exec.usage import get_period_key


def test_health_returns_expected_shape(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert {"ok", "api", "db", "worker_recent_heartbeat", "timestamp", "polar_env"} <= set(data.keys())


def test_me_rejects_missing_api_key(client):
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header"


def test_me_rejects_invalid_api_key(client):
    response = client.get("/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API Key"


def test_valid_api_key_can_access_me(client, seeded_api_key):
    response = client.get("/me", headers=seeded_api_key["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == seeded_api_key["user_id"]
    assert data["is_active"] is True
    assert "effective_plan" in data


def test_run_rejects_when_quota_is_exhausted(client, seeded_api_key, app_modules):
    conn = app_modules.db.get_conn()
    conn.execute(
        "INSERT INTO usage_counters (user_id, period_key, execution_count, credit_used) VALUES (?, ?, ?, ?)",
        (seeded_api_key["user_id"], get_period_key(), 50, 50.0),
    )
    conn.commit()
    conn.close()

    response = client.post("/run", headers=seeded_api_key["headers"], json={"script": "print('hi')"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Monthly credit quota exceeded"


def test_diagnose_rejects_when_credit_quota_is_exhausted(client, seeded_api_key, app_modules):
    conn = app_modules.db.get_conn()
    conn.execute(
        "INSERT INTO usage_counters (user_id, period_key, execution_count, credit_used) VALUES (?, ?, ?, ?)",
        (seeded_api_key["user_id"], get_period_key(), 10, 49.9),
    )
    conn.commit()
    conn.close()

    response = client.post("/diagnose", headers=seeded_api_key["headers"], json={"script": "print('hi')"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Monthly credit quota exceeded"


def test_diagnostics_credit_thresholds(app_modules):
    usage = app_modules.usage
    assert usage.compute_diagnostics_credits(0) == 0.25
    assert usage.compute_diagnostics_credits(128 * 1024) == 0.25
    assert usage.compute_diagnostics_credits((128 * 1024) + 1) == 0.5
    assert usage.compute_diagnostics_credits(512 * 1024) == 0.5
    assert usage.compute_diagnostics_credits((512 * 1024) + 1) == 1.0


def test_execution_credit_thresholds(app_modules):
    usage = app_modules.usage
    assert usage.compute_execution_credits(0) == 1.0
    assert usage.compute_execution_credits(64 * 1024) == 1.0
    assert usage.compute_execution_credits((64 * 1024) + 1) == 1.5
    assert usage.compute_execution_credits(256 * 1024) == 1.5
    assert usage.compute_execution_credits((256 * 1024) + 1) == 2.0


def test_diagnose_rejects_missing_auth(client):
    response = client.post("/diagnose", json={"script": "print('hi')"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header"


def test_run_rejects_missing_auth(client):
    response = client.post("/run", json={"script": "print('hi')"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header"


def test_run_rejects_invalid_api_key(client):
    response = client.post(
        "/run",
        headers={"Authorization": "Bearer invalid"},
        json={"script": "print('hi')"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API Key"


def test_run_rejects_missing_script_input(client, seeded_api_key):
    response = client.post("/run", headers=seeded_api_key["headers"], json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing script"


def test_run_rejects_empty_script_input(client, seeded_api_key):
    response = client.post("/run", headers=seeded_api_key["headers"], json={"script": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing script"


def test_run_rejects_script_and_files_mode_together(client, seeded_api_key):
    response = client.post(
        "/run",
        headers=seeded_api_key["headers"],
        json={
            "script": "print('hi')",
            "entrypoint": "main.py",
            "files": [{"path": "main.py", "content": "print('hi')"}],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Provide either script or entrypoint plus files, not both"


def test_run_accepts_valid_files_mode_request(client, seeded_api_key):
    response = client.post(
        "/run",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [
                {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
                {"path": "utils.py", "content": "def add(a, b):\n    return a + b"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data
    assert data["plan"] == "Free"
    assert data["quota"] == 50


def test_run_records_usage_event_with_payload_metadata(client, seeded_api_key, app_modules):
    response = client.post("/run", headers=seeded_api_key["headers"], json={"script": "print('ok')"})
    assert response.status_code == 200
    execution_id = response.json()["execution_id"]

    conn = app_modules.db.get_business_conn()
    row = conn.execute(
        """
        SELECT route_category, credit_amount, input_mode, file_count, total_content_bytes,
               max_single_file_bytes, entrypoint, key_id, execution_id
        FROM usage_events
        ORDER BY created_at DESC
        LIMIT 1
        """
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["route_category"] == "run"
    assert row["credit_amount"] == 1.0
    assert row["input_mode"] == "script"
    assert row["file_count"] == 1
    assert row["total_content_bytes"] > 0
    assert row["max_single_file_bytes"] == row["total_content_bytes"]
    assert row["entrypoint"] is None
    assert row["key_id"] == seeded_api_key["record"]["id"]
    assert row["execution_id"] == execution_id

    conn = app_modules.db.get_business_conn()
    usage_counter_row = conn.execute(
        "SELECT execution_count, credit_used FROM usage_counters WHERE user_id = ? AND period_key = ?",
        (seeded_api_key["user_id"], get_period_key()),
    ).fetchone()
    conn.close()
    assert usage_counter_row["execution_count"] == 1
    assert usage_counter_row["credit_used"] == 1.0


def test_run_rejects_files_mode_path_traversal(client, seeded_api_key):
    response = client.post(
        "/run",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "../main.py",
            "files": [{"path": "../main.py", "content": "print('hi')"}],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Path traversal is not allowed"


def test_run_rejects_files_mode_when_total_content_is_too_large(client, seeded_api_key):
    large_content = "a" * (1024 * 1024)
    response = client.post(
        "/run",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [
                {"path": "main.py", "content": large_content},
                {"path": "utils.py", "content": "print('small')"},
            ],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Total file content is too large"


def test_run_rejects_malformed_json_body(client, seeded_api_key):
    response = client.post(
        "/run",
        headers={**seeded_api_key["headers"], "Content-Type": "application/json"},
        content="{",
    )
    assert response.status_code == 422


def test_run_accepts_safe_execution_request_when_allowed(client, seeded_api_key):
    response = client.post("/run", headers=seeded_api_key["headers"], json={"script": "print('ok')"})
    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data
    assert data["plan"] == "Free"
    assert data["quota"] == 50


def test_diagnose_script_returns_ok_for_valid_python(client, seeded_api_key):
    response = client.post("/diagnose", headers=seeded_api_key["headers"], json={"script": "print(2 + 2)"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["mode"] == "diagnostics"
    assert data["language"] == "python"
    assert data["input_mode"] == "script"
    assert data["file_count"] == 1
    assert data["total_content_bytes"] > 0
    assert data["max_single_file_bytes"] == data["total_content_bytes"]
    assert data["entrypoint"] is None
    assert data["metadata"] == {
        "input_mode": "script",
        "file_count": 1,
        "total_content_bytes": data["total_content_bytes"],
        "max_single_file_bytes": data["max_single_file_bytes"],
        "entrypoint": None,
    }
    assert data["issues"] == []


def test_diagnose_records_usage_event_with_payload_metadata(client, seeded_api_key, app_modules):
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [
                {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
                {"path": "utils.py", "content": "def add(a, b):\n    return a + b"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"] == {
        "input_mode": "files",
        "file_count": 2,
        "total_content_bytes": data["total_content_bytes"],
        "max_single_file_bytes": data["max_single_file_bytes"],
        "entrypoint": "main.py",
    }

    conn = app_modules.db.get_business_conn()
    row = conn.execute(
        """
        SELECT route_category, credit_amount, input_mode, file_count, total_content_bytes,
               max_single_file_bytes, entrypoint, key_id, execution_id
        FROM usage_events
        ORDER BY created_at DESC
        LIMIT 1
        """
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["route_category"] == "diagnose"
    assert row["credit_amount"] == 0.25
    assert row["input_mode"] == "files"
    assert row["file_count"] == 2
    assert row["total_content_bytes"] == data["total_content_bytes"]
    assert row["max_single_file_bytes"] == data["max_single_file_bytes"]
    assert row["entrypoint"] == "main.py"
    assert row["key_id"] == seeded_api_key["record"]["id"]
    assert row["execution_id"] is None

    conn = app_modules.db.get_business_conn()
    usage_counter_row = conn.execute(
        "SELECT execution_count, credit_used FROM usage_counters WHERE user_id = ? AND period_key = ?",
        (seeded_api_key["user_id"], get_period_key()),
    ).fetchone()
    conn.close()
    assert usage_counter_row["execution_count"] == 0
    assert usage_counter_row["credit_used"] == 0.25


def test_usage_event_metadata_is_persisted_for_diagnose_and_run_paths(client, seeded_api_key, app_modules):
    diagnose_script_response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={"script": "print(2 + 2)"},
    )
    assert diagnose_script_response.status_code == 200

    diagnose_files_response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [
                {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
                {"path": "utils.py", "content": "def add(a, b):\n    return a + b"},
            ],
        },
    )
    assert diagnose_files_response.status_code == 200

    run_response = client.post(
        "/run",
        headers=seeded_api_key["headers"],
        json={"script": "print('ok')"},
    )
    assert run_response.status_code == 200
    execution_id = run_response.json()["execution_id"]

    conn = app_modules.db.get_business_conn()
    rows = conn.execute(
        """
        SELECT route_category, input_mode, file_count, total_content_bytes,
               max_single_file_bytes, entrypoint, execution_id
        FROM usage_events
        ORDER BY created_at DESC
        LIMIT 3
        """
    ).fetchall()
    conn.close()

    assert len(rows) == 3
    latest_rows = [dict(row) for row in rows]

    assert latest_rows[0]["route_category"] == "run"
    assert latest_rows[0]["input_mode"] == "script"
    assert latest_rows[0]["file_count"] == 1
    assert latest_rows[0]["total_content_bytes"] > 0
    assert latest_rows[0]["max_single_file_bytes"] == latest_rows[0]["total_content_bytes"]
    assert latest_rows[0]["entrypoint"] is None
    assert latest_rows[0]["execution_id"] == execution_id

    assert latest_rows[1]["route_category"] == "diagnose"
    assert latest_rows[1]["input_mode"] == "files"
    assert latest_rows[1]["file_count"] == 2
    assert latest_rows[1]["total_content_bytes"] > 0
    assert latest_rows[1]["max_single_file_bytes"] > 0
    assert latest_rows[1]["entrypoint"] == "main.py"
    assert latest_rows[1]["execution_id"] is None

    assert latest_rows[2]["route_category"] == "diagnose"
    assert latest_rows[2]["input_mode"] == "script"
    assert latest_rows[2]["file_count"] == 1
    assert latest_rows[2]["total_content_bytes"] > 0
    assert latest_rows[2]["max_single_file_bytes"] == latest_rows[2]["total_content_bytes"]
    assert latest_rows[2]["entrypoint"] is None
    assert latest_rows[2]["execution_id"] is None


def test_me_exposes_credit_usage_fields(client, seeded_api_key, app_modules):
    conn = app_modules.db.get_conn()
    conn.execute(
        "INSERT INTO usage_counters (user_id, period_key, execution_count, credit_used) VALUES (?, ?, ?, ?)",
        (seeded_api_key["user_id"], get_period_key(), 3, 12.5),
    )
    conn.commit()
    conn.close()

    response = client.get("/me", headers=seeded_api_key["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["effective_quota_monthly"] == 50
    assert data["execution_count_this_period"] == 3
    assert data["credit_used_this_period"] == 12.5
    assert data["credit_remaining_this_period"] == 37.5
    assert data["usage_this_period"] == 12.5


def test_diagnose_script_returns_syntax_issue_for_invalid_python(client, seeded_api_key):
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={"script": "def broken(:\n    pass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["input_mode"] == "script"
    assert any(issue["code"] == "python_syntax_error" for issue in data["issues"])


def test_diagnose_accepts_valid_files_mode_payload(client, seeded_api_key):
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [
                {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
                {"path": "utils.py", "content": "def add(a, b):\n    return a + b"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["input_mode"] == "files"
    assert data["entrypoint"] == "main.py"
    assert data["file_count"] == 2
    assert data["issues"] == []


def test_diagnose_files_returns_missing_local_module_issue(client, seeded_api_key):
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [{"path": "main.py", "content": "from utils_missing import add\nprint(add(2, 2))"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["input_mode"] == "files"
    assert any(issue["code"] == "missing_local_module" for issue in data["issues"])


def test_diagnose_files_allows_obvious_stdlib_import_without_missing_local_module(client, seeded_api_key):
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [{"path": "main.py", "content": "import os\nprint(os.getcwd())"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert not any(issue["code"] == "missing_local_module" for issue in data["issues"])


def test_diagnose_files_returns_syntax_issue_for_invalid_python(client, seeded_api_key):
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [{"path": "main.py", "content": "def broken(:\n    pass"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["input_mode"] == "files"
    assert any(issue["code"] == "python_syntax_error" for issue in data["issues"])


def test_diagnose_enforces_total_content_limit(client, seeded_api_key):
    large_content = "a" * (1024 * 1024)
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "main.py",
            "files": [
                {"path": "main.py", "content": large_content},
                {"path": "utils.py", "content": "print('small')"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert any(
        issue["code"] == "payload_validation_failed"
        and issue["message"] == "Total file content is too large"
        for issue in data["issues"]
    )


def test_diagnose_enforces_path_traversal_rejection(client, seeded_api_key):
    response = client.post(
        "/diagnose",
        headers=seeded_api_key["headers"],
        json={
            "entrypoint": "../main.py",
            "files": [{"path": "../main.py", "content": "print('hi')"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert any(
        issue["code"] == "payload_validation_failed"
        and issue["message"] == "Path traversal is not allowed"
        for issue in data["issues"]
    )


def test_status_route_returns_valid_structure(client, seeded_api_key):
    run_response = client.post("/run", headers=seeded_api_key["headers"], json={"script": "print('queued')"})
    execution_id = run_response.json()["execution_id"]

    response = client.get(f"/status/{execution_id}", headers=seeded_api_key["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["execution_id"] == execution_id
    assert data["status"] in {"queued", "running", "finished", "completed", "failed"}
    assert "has_result" in data


def test_result_route_returns_valid_structure_for_finished_execution(client, seeded_api_key, app_modules):
    execution_id = "exec_finished_001"
    app_modules.status.set_status(
        execution_id,
        "finished",
        key_id=seeded_api_key["record"]["id"],
        user_id=seeded_api_key["user_id"],
    )
    app_modules.results.save_result(
        execution_id,
        {
            "stdout": "done\n",
            "stderr": "",
            "exit_code": 0,
            "duration": 0.01,
        },
        key_id=seeded_api_key["record"]["id"],
        user_id=seeded_api_key["user_id"],
    )

    response = client.get(f"/result/{execution_id}", headers=seeded_api_key["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["execution_id"] == execution_id
    assert data["status"] == "completed"
    assert data["result"]["exit_code"] == 0
