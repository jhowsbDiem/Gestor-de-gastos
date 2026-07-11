"""Modelo de dados e persistência em JSON para o Gestor de Gastos."""
import json
import os
import shutil
import uuid
from datetime import date

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "gastos.json")
EXAMPLE_FILE = os.path.join(DATA_DIR, "gastos.example.json")

TIPOS_VALIDOS = ("credito", "debito", "pix")


def _garantir_arquivo_dados():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        origem = EXAMPLE_FILE if os.path.exists(EXAMPLE_FILE) else None
        if origem:
            shutil.copyfile(origem, DATA_FILE)
        else:
            _salvar({"salario": 0.0, "meta_investimento": 0.0, "gastos": []})


def _carregar():
    _garantir_arquivo_dados()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar(dados):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def _mes_atual():
    hoje = date.today()
    return hoje.year, hoje.month


def _somar_meses(data_iso, meses):
    ano, mes, dia = (int(p) for p in data_iso.split("-"))
    total_meses = mes - 1 + meses
    novo_ano = ano + total_meses // 12
    novo_mes = total_meses % 12 + 1
    return date(novo_ano, novo_mes, 1)


def calcular_derivados(gasto):
    """Calcula os campos derivados de um gasto sem persisti-los."""
    valor_total = gasto["valor_total"]
    parcelas_total = gasto["parcelas_total"]
    parcelas_pagas = gasto["parcelas_pagas"]

    valor_parcela = round(valor_total / parcelas_total, 2) if parcelas_total else valor_total

    if gasto["tipo"] == "credito":
        parcelas_faltantes = max(parcelas_total - parcelas_pagas, 0)
        valor_restante = round(valor_parcela * parcelas_faltantes, 2)
        proxima_data_vencimento = (
            _somar_meses(gasto["data"], parcelas_pagas).isoformat()
            if parcelas_faltantes > 0
            else None
        )
    else:
        parcelas_faltantes = 0
        valor_restante = 0.0
        proxima_data_vencimento = None

    derivado = dict(gasto)
    derivado["valor_parcela"] = valor_parcela
    derivado["parcelas_faltantes"] = parcelas_faltantes
    derivado["valor_restante"] = valor_restante
    derivado["proxima_data_vencimento"] = proxima_data_vencimento
    return derivado


def listar_gastos(banco=None, tipo=None):
    dados = _carregar()
    gastos = [calcular_derivados(g) for g in dados["gastos"]]
    if banco:
        gastos = [g for g in gastos if g["banco"].lower() == banco.lower()]
    if tipo:
        gastos = [g for g in gastos if g["tipo"] == tipo]
    return gastos


def obter_salario():
    return _carregar()["salario"]


def definir_salario(valor):
    if valor < 0:
        raise ValueError("Salário não pode ser negativo.")
    dados = _carregar()
    dados["salario"] = valor
    _salvar(dados)
    return dados["salario"]


def obter_meta_investimento():
    return _carregar().get("meta_investimento", 0.0)


def definir_meta_investimento(valor):
    if valor < 0:
        raise ValueError("Meta de investimento não pode ser negativa.")
    dados = _carregar()
    dados["meta_investimento"] = valor
    _salvar(dados)
    return dados["meta_investimento"]


def _validar_gasto(payload):
    erros = []
    if not payload.get("descricao", "").strip():
        erros.append("Descrição é obrigatória.")
    if payload.get("tipo") not in TIPOS_VALIDOS:
        erros.append("Tipo deve ser credito, debito ou pix.")
    if not payload.get("banco", "").strip():
        erros.append("Banco é obrigatório.")
    if not payload.get("data"):
        erros.append("Data é obrigatória.")
    try:
        if float(payload.get("valor_total", -1)) <= 0:
            erros.append("Valor total deve ser positivo.")
    except (TypeError, ValueError):
        erros.append("Valor total inválido.")

    tipo = payload.get("tipo")
    parcelas_total = payload.get("parcelas_total", 1)
    parcelas_pagas = payload.get("parcelas_pagas", 0)
    try:
        parcelas_total = int(parcelas_total)
        parcelas_pagas = int(parcelas_pagas)
    except (TypeError, ValueError):
        erros.append("Número de parcelas inválido.")
        parcelas_total, parcelas_pagas = 1, 0

    if tipo in ("debito", "pix"):
        parcelas_total, parcelas_pagas = 1, 1
    else:
        if parcelas_total < 1:
            erros.append("Parcelas totais deve ser ao menos 1.")
        if parcelas_pagas < 0 or parcelas_pagas > parcelas_total:
            erros.append("Parcelas pagas deve estar entre 0 e o total de parcelas.")

    return erros, parcelas_total, parcelas_pagas


def criar_gasto(payload):
    erros, parcelas_total, parcelas_pagas = _validar_gasto(payload)
    if erros:
        raise ValueError(" ".join(erros))

    gasto = {
        "id": str(uuid.uuid4()),
        "descricao": payload["descricao"].strip(),
        "valor_total": float(payload["valor_total"]),
        "tipo": payload["tipo"],
        "banco": payload["banco"].strip(),
        "data": payload["data"],
        "parcelas_total": parcelas_total,
        "parcelas_pagas": parcelas_pagas,
        "categoria": payload.get("categoria", "").strip(),
    }
    dados = _carregar()
    dados["gastos"].append(gasto)
    _salvar(dados)
    return calcular_derivados(gasto)


def atualizar_gasto(gasto_id, payload):
    erros, parcelas_total, parcelas_pagas = _validar_gasto(payload)
    if erros:
        raise ValueError(" ".join(erros))

    dados = _carregar()
    for gasto in dados["gastos"]:
        if gasto["id"] == gasto_id:
            gasto.update(
                {
                    "descricao": payload["descricao"].strip(),
                    "valor_total": float(payload["valor_total"]),
                    "tipo": payload["tipo"],
                    "banco": payload["banco"].strip(),
                    "data": payload["data"],
                    "parcelas_total": parcelas_total,
                    "parcelas_pagas": parcelas_pagas,
                    "categoria": payload.get("categoria", "").strip(),
                }
            )
            _salvar(dados)
            return calcular_derivados(gasto)
    raise KeyError(gasto_id)


def excluir_gasto(gasto_id):
    dados = _carregar()
    tamanho_antes = len(dados["gastos"])
    dados["gastos"] = [g for g in dados["gastos"] if g["id"] != gasto_id]
    if len(dados["gastos"]) == tamanho_antes:
        raise KeyError(gasto_id)
    _salvar(dados)


def calcular_resumo():
    dados = _carregar()
    salario = dados["salario"]
    gastos = [calcular_derivados(g) for g in dados["gastos"]]
    ano_atual, mes_atual = _mes_atual()

    total_gasto_mes = 0.0
    total_a_pagar_parcelas = 0.0
    compromisso_mes_atual = 0.0

    for g in gastos:
        if g["tipo"] == "credito":
            total_a_pagar_parcelas += g["valor_restante"]
            vencimento = g["proxima_data_vencimento"]
            if vencimento:
                ano_v, mes_v, _ = (int(p) for p in vencimento.split("-"))
                if ano_v == ano_atual and mes_v == mes_atual:
                    total_gasto_mes += g["valor_parcela"]
                    compromisso_mes_atual += g["valor_parcela"]
        else:
            ano_g, mes_g, _ = (int(p) for p in g["data"].split("-"))
            if ano_g == ano_atual and mes_g == mes_atual:
                total_gasto_mes += g["valor_total"]
                compromisso_mes_atual += g["valor_total"]

    sobra_salario = round(salario - compromisso_mes_atual, 2)

    return {
        "salario": salario,
        "total_gasto_mes": round(total_gasto_mes, 2),
        "total_a_pagar_parcelas": round(total_a_pagar_parcelas, 2),
        "meta_investimento": dados.get("meta_investimento", 0.0),
        "sobra_salario": sobra_salario,
    }


def exportar_dados():
    return _carregar()


def importar_dados(dados):
    if not isinstance(dados, dict) or "salario" not in dados or "gastos" not in dados:
        raise ValueError("Arquivo JSON inválido: esperado objeto com 'salario' e 'gastos'.")
    _salvar(dados)
