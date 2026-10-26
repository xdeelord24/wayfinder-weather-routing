"""Create a minimal source/built-frontend ZIP for manual WSGI hosting.

Only explicitly allowed runtime files are packed. Credentials, virtualenvs,
assessment source, tests, Git data and local evidence are excluded.
No account access, network request, install, upload or deployment is performed.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]

WSGI_TEMPLATE = '''# Paste into the WSGI configuration file linked from PythonAnywhere's Web tab.
# Replace YOUR_USERNAME; choose the same Python version as the virtualenv.
import os
import sys

project_home = "/home/YOUR_USERNAME/wayfinder"
backend = project_home + "/backend"
if backend not in sys.path:
    sys.path.insert(0, backend)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
# config.settings loads /home/YOUR_USERNAME/wayfinder/.env privately.
# Do not put actual secrets in this template or a public repository.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
'''


def main():
    required = [ROOT / "requirements.txt", ROOT / "frontend/dist/index.html", ROOT / "backend/config/settings.py"]
    if not all(path.is_file() for path in required):
        raise SystemExit("Required runtime/build files are missing; build the frontend before packaging.")
    files = [ROOT / "requirements.txt"]
    files.extend(path for path in (ROOT / "backend").rglob("*.py")
                 if "__pycache__" not in path.parts and "staticfiles" not in path.parts
                 and path.name not in {"tests.py", "conftest.py"} and not path.name.startswith("test_"))
    files.append(ROOT / "backend/routing/data/demo_routes.json")
    files.extend(path for path in (ROOT / "frontend/dist").rglob("*")
                 if path.is_file() and path.suffix in {".html", ".js", ".css", ".svg", ".woff", ".woff2"})
    files = sorted(set(files))
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise SystemExit("Refusing a symlink or file outside the project.")
    now = datetime.now(timezone.utc)
    output = ROOT / "output/deployment"
    output.mkdir(parents=True, exist_ok=True)
    stem = "wayfinder-pythonanywhere-" + now.strftime("%Y%m%dT%H%M%SZ")
    archive = output / (stem + ".zip")
    manifest_path = output / (stem + "-manifest.json")
    entries = []
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            name = "wayfinder/" + path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            bundle.writestr(name, data)
            entries.append({"path": name, "bytes": len(data), "sha256": sha256(data).hexdigest()})
        name = "wayfinder/pythonanywhere_wsgi.py.example"
        data = WSGI_TEMPLATE.encode()
        bundle.writestr(name, data)
        entries.append({"path": name, "bytes": len(data), "sha256": sha256(data).hexdigest()})
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None, "ZIP integrity check failed"
        names = bundle.namelist()
        assert len(names) == len(set(names)) == len(entries)
        assert not any(".." in Path(name).parts or any(part.startswith(".env") for part in Path(name).parts) for name in names)
        assert not any(name.endswith((".pdf", ".pyc", ".map")) or "__pycache__" in name or "tests.py" in name for name in names)
        assert all(name.startswith(("wayfinder/backend/", "wayfinder/frontend/dist/")) or name in {
            "wayfinder/requirements.txt", "wayfinder/pythonanywhere_wsgi.py.example"} for name in names)
    manifest = {"created_at_utc": now.isoformat(), "archive": str(archive), "archive_bytes": archive.stat().st_size,
                "archive_sha256": sha256(archive.read_bytes()).hexdigest(), "uncompressed_bytes": sum(item["bytes"] for item in entries),
                "file_count": len(entries), "verification": "ZIP integrity, explicit runtime allowlist, names and SHA-256 checks passed",
                "hosting_status": "Prepared locally only; not uploaded, installed or hosted", "files": entries}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "pythonanywhere_wsgi.py.example").write_text(WSGI_TEMPLATE, encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("archive", "archive_bytes", "uncompressed_bytes", "file_count", "verification", "hosting_status")}, indent=2))
    print("Manifest: " + str(manifest_path))


if __name__ == "__main__":
    main()
