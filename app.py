"""Gestor de Gastos Pessoais — servidor Flask."""
from datetime import date

from flask import Flask, jsonify, render_template, request, send_file

import models

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", hoje=date.today().strftime("%d/%m/%Y"))


@app.route("/api/resumo", methods=["GET"])
def api_resumo():
    return jsonify(models.calcular_resumo())


@app.route("/api/salario", methods=["GET", "PUT"])
def api_salario():
    if request.method == "GET":
        return jsonify({"salario": models.obter_salario()})

    payload = request.get_json(silent=True) or {}
    try:
        valor = float(payload.get("salario"))
        novo_salario = models.definir_salario(valor)
    except (TypeError, ValueError) as erro:
        return jsonify({"erro": str(erro) or "Valor de salário inválido."}), 400
    return jsonify({"salario": novo_salario})


@app.route("/api/meta-investimento", methods=["GET", "PUT"])
def api_meta_investimento():
    if request.method == "GET":
        return jsonify({"meta_investimento": models.obter_meta_investimento()})

    payload = request.get_json(silent=True) or {}
    try:
        valor = float(payload.get("meta_investimento"))
        nova_meta = models.definir_meta_investimento(valor)
    except (TypeError, ValueError) as erro:
        return jsonify({"erro": str(erro) or "Valor de meta de investimento inválido."}), 400
    return jsonify({"meta_investimento": nova_meta})


@app.route("/api/gastos", methods=["GET", "POST"])
def api_gastos():
    if request.method == "GET":
        banco = request.args.get("banco") or None
        tipo = request.args.get("tipo") or None
        return jsonify(models.listar_gastos(banco=banco, tipo=tipo))

    payload = request.get_json(silent=True) or {}
    try:
        gasto = models.criar_gasto(payload)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(gasto), 201


@app.route("/api/gastos/<gasto_id>", methods=["PUT", "DELETE"])
def api_gasto_detalhe(gasto_id):
    if request.method == "DELETE":
        try:
            models.excluir_gasto(gasto_id)
        except KeyError:
            return jsonify({"erro": "Gasto não encontrado."}), 404
        return "", 204

    payload = request.get_json(silent=True) or {}
    try:
        gasto = models.atualizar_gasto(gasto_id, payload)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except KeyError:
        return jsonify({"erro": "Gasto não encontrado."}), 404
    return jsonify(gasto)


@app.route("/api/export", methods=["GET"])
def api_export():
    return jsonify(models.exportar_dados())


@app.route("/api/import", methods=["POST"])
def api_import():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"erro": "Envie um JSON válido no corpo da requisição."}), 400
    try:
        models.importar_dados(payload)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
