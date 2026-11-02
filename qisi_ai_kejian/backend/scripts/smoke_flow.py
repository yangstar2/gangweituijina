"""End-to-end mock flow against a running server (or in-process TestClient)."""

from __future__ import annotations

import sys
from pathlib import Path

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
    print("SMOKE OK — session", sid, "pages", [p["title"] for p in pages])


if __name__ == "__main__":
    main()
