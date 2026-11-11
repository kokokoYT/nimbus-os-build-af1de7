#!/usr/bin/env python3
"""Nimbus app catalog server.

  python3 nimbus_server.py serve [--port 8080] [--dir data]
  python3 nimbus_server.py add-deb --id gimp --name GIMP --package gimp --desc "Image editor" --category Graphics
  python3 nimbus_server.py add-windows setup.exe --id notepadpp --name "Notepad++" --desc "Editor" \
        --category Office --args "/S" --launch 'C:\\Program Files\\Notepad++\\notepad++.exe'
  python3 nimbus_server.py add-windows tool.exe --id tool --name Tool --portable      (single .exe, no installer)
"""
import argparse, hashlib, http.server, json, os, shutil, functools


def load(d):
    p = os.path.join(d, "catalog.json")
    return json.load(open(p)) if os.path.exists(p) else {"name": "Nimbus Apps", "apps": []}


def save(d, cat):
    os.makedirs(d, exist_ok=True)
    json.dump(cat, open(os.path.join(d, "catalog.json"), "w"), indent=2)


def upsert(cat, entry):
    cat["apps"] = [a for a in cat["apps"] if a["id"] != entry["id"]] + [entry]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve"); s.add_argument("--port", type=int, default=8080); s.add_argument("--dir", default="data")
    s.add_argument("--host", default="0.0.0.0")
    for name in ("add-deb", "add-windows"):
        p = sub.add_parser(name)
        if name == "add-windows":
            p.add_argument("file")
        p.add_argument("--dir", default="data")
        p.add_argument("--id", required=True); p.add_argument("--name", required=True)
        p.add_argument("--desc", default=""); p.add_argument("--category", default="Other"); p.add_argument("--version", default="")
        if name == "add-deb":
            p.add_argument("--package", required=True)
        else:
            p.add_argument("--args", default=""); p.add_argument("--launch", default=""); p.add_argument("--portable", action="store_true")
    a = ap.parse_args()

    if a.cmd == "serve":
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=a.dir)
        print("Serving %s on http://%s:%d  (catalog at /catalog.json)" % (a.dir, a.host, a.port))
        http.server.ThreadingHTTPServer((a.host, a.port), h).serve_forever()
    cat = load(a.dir)
    if a.cmd == "add-deb":
        upsert(cat, {"id": a.id, "name": a.name, "type": "deb", "package": a.package,
                     "description": a.desc, "category": a.category, "version": a.version})
    else:
        os.makedirs(os.path.join(a.dir, "files"), exist_ok=True)
        fn = os.path.basename(a.file)
        shutil.copy(a.file, os.path.join(a.dir, "files", fn))
        sha = hashlib.sha256(open(a.file, "rb").read()).hexdigest()
        e = {"id": a.id, "name": a.name, "type": "windows", "url": "/files/" + fn, "sha256": sha,
             "description": a.desc, "category": a.category, "version": a.version}
        if a.portable: e["portable"] = True
        if a.args: e["installer_args"] = a.args
        if a.launch: e["launch"] = a.launch
        upsert(cat, e)
    save(a.dir, cat)
    print("catalog updated:", len(cat["apps"]), "apps")


main()
