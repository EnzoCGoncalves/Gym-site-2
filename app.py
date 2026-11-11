"""FORJA — montar e avaliar treinos de academia.

Site e API no mesmo processo. Para rodar:  python app.py
"""
import json
import os
import sqlite3
import threading
import webbrowser
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

import engine
from exercises import (ALL_EQUIPMENT, EQUIPMENT_GROUPS, EXERCISES, MUSCLES, PATTERNS,
                       PRESETS)

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "gym.db")
PORT = int(os.environ.get("PORT", 5000))

app = Flask(__name__, static_folder=os.path.join(BASE, "static"), static_url_path="/static")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, dados TEXT NOT NULL,
            nota INTEGER, criado TEXT NOT NULL, atualizado TEXT NOT NULL)""")
        con.execute("CREATE TABLE IF NOT EXISTS config (chave TEXT PRIMARY KEY, valor TEXT NOT NULL)")


def agora():
    return datetime.now().isoformat(timespec="seconds")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/dados")
def dados():
    return jsonify({
        "exercicios": EXERCISES,
        "musculos": MUSCLES,
        "padroes": PATTERNS,
        "equipamentos": [{"grupo": g, "itens": [{"id": k, "nome": n} for k, n in itens]}
                         for g, itens in EQUIPMENT_GROUPS],
        "presets": PRESETS,
    })


@app.get("/api/equipamentos")
def get_equip():
    with db() as con:
        row = con.execute("SELECT valor FROM config WHERE chave='equip'").fetchone()
    return jsonify(json.loads(row["valor"]) if row else ALL_EQUIPMENT)


@app.put("/api/equipamentos")
def put_equip():
    itens = [e for e in (request.get_json(silent=True) or []) if e in ALL_EQUIPMENT]
    with db() as con:
        con.execute("INSERT INTO config (chave, valor) VALUES ('equip', ?) "
                    "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor", (json.dumps(itens),))
    return jsonify(itens)


@app.post("/api/gerar")
def gerar():
    return jsonify(engine.gerar(request.get_json(silent=True) or {}))


@app.post("/api/avaliar")
def avaliar():
    return jsonify(engine.avaliar(request.get_json(silent=True) or {}))


def _resumo(row):
    d = json.loads(row["dados"])
    return {"id": row["id"], "nome": row["nome"], "nota": row["nota"],
            "atualizado": row["atualizado"], "nivel": d["nivel"], "objetivo": d["objetivo"],
            "dias": len(d["dias"]),
            "exercicios": sum(len(x["exercicios"]) for x in d["dias"])}


@app.get("/api/treinos")
def listar():
    with db() as con:
        rows = con.execute("SELECT * FROM treinos ORDER BY atualizado DESC").fetchall()
    return jsonify([_resumo(r) for r in rows])


@app.get("/api/treinos/<int:tid>")
def obter(tid):
    with db() as con:
        row = con.execute("SELECT * FROM treinos WHERE id=?", (tid,)).fetchone()
    if not row:
        return jsonify({"erro": "Treino não encontrado"}), 404
    return jsonify({**json.loads(row["dados"]), "id": row["id"]})


@app.post("/api/treinos")
@app.put("/api/treinos/<int:tid>")
def salvar(tid=None):
    plano = engine.normalizar(request.get_json(silent=True) or {})
    nota = engine.avaliar(plano)["nota"]
    dados_json = json.dumps(plano, ensure_ascii=False)
    with db() as con:
        if tid is None:
            cur = con.execute("INSERT INTO treinos (nome, dados, nota, criado, atualizado) "
                              "VALUES (?,?,?,?,?)", (plano["nome"], dados_json, nota, agora(), agora()))
            tid = cur.lastrowid
        else:
            cur = con.execute("UPDATE treinos SET nome=?, dados=?, nota=?, atualizado=? WHERE id=?",
                              (plano["nome"], dados_json, nota, agora(), tid))
            if cur.rowcount == 0:
                return jsonify({"erro": "Treino não encontrado"}), 404
    return jsonify({**plano, "id": tid})


@app.delete("/api/treinos/<int:tid>")
def excluir(tid):
    with db() as con:
        con.execute("DELETE FROM treinos WHERE id=?", (tid,))
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    url = f"http://127.0.0.1:{PORT}"
    print(f"\n  FORJA rodando em {url}  (Ctrl+C para parar)\n")
    if not os.environ.get("FORJA_SEM_NAVEGADOR"):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)
