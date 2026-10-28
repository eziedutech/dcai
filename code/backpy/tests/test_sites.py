"""Site lists for the phone and the category signal. Lists are built from a tiny local copy
in UT1's layout; the site's name never reaches the server."""

import json

from sqlalchemy import create_engine, inspect, text

from app.blocklist.build import build
from app.blocklist.lists import contains, decode_count, encode, normalise
from tests.test_devices import paired

SENTINEL = "sentinel-situs-3b9f.example"


def ut1_copy(tmp_path):
    src = tmp_path / "ut1"
    (src / "gambling").mkdir(parents=True)
    (src / "gambling" / "domains").write_text(
        "casino-contoh.test\n.slot-contoh.test\nwww.judi-contoh.test\n10.0.0.1\n", encoding="utf-8"
    )
    (src / "adult").mkdir()
    # Split like UT1's largest category.
    (src / "adult" / "domains.0").write_text("dewasa-satu.test\n", encoding="utf-8")
    (src / "adult" / "domains.1").write_text("dewasa-dua.test\n", encoding="utf-8")
    return src


def with_lists(api, tmp_path):
    out = tmp_path / "lists"
    build(out, ut1_copy(tmp_path))
    api.app.state.settings = api.app.state.settings.model_copy(update={"site_lists_dir": str(out)})
    return out


def test_list_format_and_parent_domain_match():
    blob, count = encode(["casino-contoh.test", ".slot-contoh.test", "1.2.3.4", "bad entry"])
    assert count == 2 and decode_count(blob) == 2
    assert contains(blob, "casino-contoh.test")
    assert contains(blob, "WWW.Casino-Contoh.test.")
    assert contains(blob, "m.cdn.slot-contoh.test")
    assert not contains(blob, "contoh.test")
    assert not contains(blob, "example.com")
    assert normalise("10.0.0.1") is None


def test_build_from_local_copy(tmp_path):
    out = tmp_path / "lists"
    manifest = build(out, ut1_copy(tmp_path))
    counts = {c["name"]: c["count"] for c in manifest["categories"]}
    assert counts["judi"] == 3 and counts["dewasa"] == 2 and counts["kencan"] == 0
    assert manifest["license"] == "CC BY-SA 4.0" and "UT1" in manifest["source"]
    blob = (out / "dewasa.bin").read_bytes()
    assert contains(blob, "dewasa-dua.test")
    # The list holds hashes only.
    assert b"dewasa" not in blob and b"casino" not in (out / "judi.bin").read_bytes()


def test_lists_need_domain_consent(api, tmp_path):
    with_lists(api, tmp_path)
    _t, _c, dev, _b = paired(api, scopes=("percakapan",))
    assert api.get("/v1/device/sites", headers=dev).status_code == 403
    signal = {"category": "judi", "list_version": "202610280000"}
    assert api.post("/v1/device/sites/signals", json=signal, headers=dev).status_code == 403


def test_manifest_and_download_with_etag(api, tmp_path):
    out = with_lists(api, tmp_path)
    _t, _c, dev, _b = paired(api, scopes=("percakapan", "domain"))
    manifest = api.get("/v1/device/sites", headers=dev).json()
    assert manifest == json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    resp = api.get("/v1/device/sites/judi", headers=dev)
    assert resp.status_code == 200 and contains(resp.content, "casino-contoh.test")
    again = api.get("/v1/device/sites/judi", headers={**dev, "If-None-Match": resp.headers["etag"]})
    assert again.status_code == 304
    assert api.get("/v1/device/sites/lainnya", headers=dev).status_code == 404


def test_lists_not_built_is_503(api, tmp_path):
    api.app.state.settings = api.app.state.settings.model_copy(
        update={"site_lists_dir": str(tmp_path / "missing")}
    )
    _t, _c, dev, _b = paired(api, scopes=("percakapan", "domain"))
    assert api.get("/v1/device/sites", headers=dev).status_code == 503


def test_signal_is_one_event_per_burst(api, tmp_path, db_url):
    with_lists(api, tmp_path)
    _t, _c, dev, _b = paired(api, scopes=("percakapan", "domain"))
    body = {"category": "judi", "list_version": "202610280000"}
    first = api.post("/v1/device/sites/signals", json=body, headers=dev)
    second = api.post("/v1/device/sites/signals", json=body, headers=dev)
    other = api.post("/v1/device/sites/signals", json={**body, "category": "dewasa"}, headers=dev)
    assert first.json()["event"] == "situs_judi" and second.json()["event"] is None
    assert other.json()["event"] == "situs_dewasa"
    with create_engine(db_url).connect() as conn:
        rows = conn.execute(text("SELECT kind, level FROM event WHERE kind LIKE 'situs_%'")).all()
    assert sorted(rows) == [("situs_dewasa", "perhatian"), ("situs_judi", "perhatian")]


def test_signal_has_no_place_for_the_site_name(api, tmp_path, db_url):
    with_lists(api, tmp_path)
    _t, _c, dev, _b = paired(api, scopes=("percakapan", "domain"))
    body = {"category": "judi", "list_version": "202610280000", "domain": SENTINEL}
    assert api.post("/v1/device/sites/signals", json=body, headers=dev).status_code == 422
    bad = {"category": "tidak-ada", "list_version": "202610280000"}
    assert api.post("/v1/device/sites/signals", json=bad, headers=dev).status_code == 422
    engine = create_engine(db_url)
    with engine.connect() as conn:
        for table in inspect(engine).get_table_names():
            for row in conn.execute(text(f"SELECT * FROM {table}")):
                assert SENTINEL not in str(row), table
