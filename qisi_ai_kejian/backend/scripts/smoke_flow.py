"""End-to-end mock flow against a running server (or in-process TestClient)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Isolated SQLite so repeated smokes don't inherit paid membership state
_os_db = tempfile.NamedTemporaryFile(prefix="qisi-smoke-", suffix=".db", delete=False)
os.environ["DATABASE_PATH"] = _os_db.name
_os_db.close()
# Force mock DeepSeek in CI unless explicitly enabled (never requires real key)
if os.environ.get("DEEPSEEK_SMOKE") != "1":
    os.environ["DEEPSEEK_API_KEY"] = ""

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)
    h = client.get("/api/health")
    assert h.status_code == 200 and h.json()["ok"], h.text

    login = client.post("/api/auth/login", json={"code": "smoke"})
    assert login.status_code == 200, login.text

    sess = client.post("/api/sessions", json={"content_type": "courseware", "title": "smoke"})
    assert sess.status_code == 200, sess.text
    sid = sess.json()["id"]

    replies = []
    for text in [
        "高一物理，45 分钟，人教版必修一力学",
        "强调牛顿定律辨析与例题，避开超纲微积分",
        "确认，可以整理大纲了",
    ]:
        r = client.post(f"/api/sessions/{sid}/messages", json={"content": text})
        assert r.status_code == 200, r.text
        replies.append(r.json())

    last = replies[-1]
    assert last["teacher"]["clarifying_done"] is True
    assert last["outline"] is not None
    assert last["outline"]["key_points"]

    styles = client.get("/api/catalog/styles").json()
    models = client.get("/api/catalog/models").json()
    assert len(styles) >= 1 and len(models) >= 1

    preview = client.post(
        f"/api/sessions/{sid}/preview",
        params={"style_id": styles[0]["id"], "model_id": models[0]["id"]},
    )
    assert preview.status_code == 200, preview.text
    pages = preview.json()["pages"]
    assert len(pages) == 6, pages

    # DeepSeek ppt-think (mock fallback when key cleared above)
    think = client.post(
        f"/api/sessions/{sid}/ppt-think",
        json={"style_id": styles[0]["id"], "model_id": models[0]["id"], "auto_generate": False},
    )
    assert think.status_code == 200, think.text
    think_body = think.json()
    assert think_body["thinking"]
    assert think_body["thinking_steps"]
    assert think_body["outline"]["key_points"]
    assert think_body["provider"] in ("mock", "deepseek")
    assert think_body["deepseek_configured"] is False or think_body["provider"] == "deepseek"

    health = client.get("/api/health").json()
    assert "deepseek_configured" in health

    # exam sessions must not use ppt-think
    sess_exam_gate = client.post(
        "/api/sessions", json={"content_type": "exam", "title": "smoke-exam-gate"}
    )
    bad_think = client.post(
        f"/api/sessions/{sess_exam_gate.json()['id']}/ppt-think",
        json={},
    )
    assert bad_think.status_code == 400, bad_think.text

    gen = client.post(
        f"/api/sessions/{sid}/generate",
        json={"style_id": styles[0]["id"], "model_id": models[0]["id"]},
    )
    assert gen.status_code == 200, gen.text
    art = gen.json()
    assert art["artifact_type"] == "ppt"
    assert art["content"]["slide_count"] >= 6
    got = client.get(f"/api/artifacts/{art['id']}")
    assert got.status_code == 200 and got.json()["id"] == art["id"]

    # exam path
    sess2 = client.post("/api/sessions", json={"content_type": "exam", "title": "smoke-exam"})
    sid2 = sess2.json()["id"]
    for text in ["初三化学，人教版", "覆盖酸碱盐，难度中等", "整理试卷大纲"]:
        client.post(f"/api/sessions/{sid2}/messages", json={"content": text})
    exam = client.post(
        f"/api/sessions/{sid2}/generate",
        json={"style_id": "exam_focus", "model_id": models[0]["id"]},
    )
    assert exam.status_code == 200, exam.text
    assert exam.json()["artifact_type"] == "exam"
    assert len(exam.json()["content"]["questions"]) >= 5

    from app.db import get_conn

    # ensure session owner is free so premium model is gated
    with get_conn() as conn:
        conn.execute(
            "UPDATE members SET plan='free', expires_at=NULL WHERE user_id=(SELECT user_id FROM sessions WHERE id=?)",
            (sid,),
        )
    gated = client.post(
        f"/api/sessions/{sid}/generate",
        json={"style_id": styles[0]["id"], "model_id": "mock-hunyuan"},
    )
    assert gated.status_code == 402, gated.text

    login2 = client.post("/api/auth/login", json={"code": "payer"})
    uid = login2.json()["user_id"]
    plans = client.get("/api/membership/plans").json()
    assert any(p["id"] == "pro_month" for p in plans)
    order = client.post("/api/pay/orders", json={"user_id": uid, "plan_id": "pro_month"})
    assert order.status_code == 200, order.text
    paid = client.post("/api/pay/notify/mock", json={"order_id": order.json()["id"]})
    assert paid.status_code == 200 and paid.json()["status"] == "paid"
    me = client.get("/api/membership/me", params={"user_id": uid}).json()
    assert me["is_premium_active"] is True

    with get_conn() as conn:
        conn.execute(
            "UPDATE members SET plan=?, expires_at=? WHERE user_id=(SELECT user_id FROM sessions WHERE id=?)",
            (me["plan"], me["expires_at"], sid),
        )
    ungated = client.post(
        f"/api/sessions/{sid}/generate",
        json={"style_id": styles[0]["id"], "model_id": "mock-hunyuan"},
    )
    assert ungated.status_code == 200, ungated.text

    admin = client.get("/admin/members", auth=("admin", "admin_mock_change_me"))
    assert admin.status_code == 200 and "会员" in admin.text
    denied = client.get("/admin/orders", auth=("nope", "nope"))
    assert denied.status_code == 401

    print(
        "SMOKE OK — session",
        sid,
        "ppt_slides",
        art["content"]["slide_count"],
        "exam_q",
        len(exam.json()["content"]["questions"]),
        "membership",
        me["plan"],
        "admin_ok",
    )


if __name__ == "__main__":
    main()
