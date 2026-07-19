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

# Categorias fixas do gasto — base do motor de peso/limite/cascata do orçamento.
# Todo gasto pertence a exatamente uma delas; nenhum outro valor é aceito.
CATEGORIAS_VALIDAS = (
    "INVESTIMENTO",       # Aportes e reservas (poupança, investimentos, previdência).
    "GASTO_FIXO_CASA",    # Despesas fixas de moradia: aluguel, financiamento, contas da casa.
    "MERCADO_ESSENCIAL",  # Compras essenciais de mercado e alimentação do dia a dia.
    "EMERGENCIA",         # Gastos emergenciais e imprevistos.
    "LAZER",              # Gastos não essenciais: lazer, entretenimento, compras discricionárias.
)

# Percentual fixo do salário destinado a cada categoria — não editável pelo
# usuário nesta fase. Soma sempre 100% do salário.
PERCENTUAIS_LIMITE_CATEGORIA = {
    "INVESTIMENTO": 0.20,
    "GASTO_FIXO_CASA": 0.30,
    "MERCADO_ESSENCIAL": 0.25,
    "EMERGENCIA": 0.10,
    "LAZER": 0.15,
}


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


def _mes_seguinte(ano, mes):
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def _parcela_vence_no_mes(gasto, ano, mes):
    """Verifica se alguma parcela do gasto estava agendada pra vencer no mês
    informado. Usa a data de compra + índice da parcela, não `parcelas_pagas`
    — assim funciona pra meses passados independente do estado atual de
    pagamento, necessário pro rollover histórico da Emergência."""
    if gasto["tipo"] != "credito":
        return False
    for indice in range(gasto["parcelas_total"]):
        vencimento = _somar_meses(gasto["data"], indice)
        if vencimento.year == ano and vencimento.month == mes:
            return True
    return False


def _usado_categoria_mes(gastos, categoria, ano, mes):
    """Soma o valor de uma categoria que efetivamente vence/ocorre no mês informado."""
    total = 0.0
    for g in gastos:
        if g["categoria"] != categoria:
            continue
        if g["tipo"] == "credito":
            if _parcela_vence_no_mes(g, ano, mes):
                total += g["valor_parcela"]
        else:
            ano_g, mes_g, _ = (int(p) for p in g["data"].split("-"))
            if ano_g == ano and mes_g == mes:
                total += g["valor_total"]
    return round(total, 2)


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
    if payload.get("categoria") not in CATEGORIAS_VALIDAS:
        erros.append("Categoria deve ser uma das opções válidas: " + ", ".join(CATEGORIAS_VALIDAS) + ".")
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
        "categoria": payload["categoria"],
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
                    "categoria": payload["categoria"],
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


def calcular_limites_categoria(salario):
    """Limite de gasto de cada categoria, na proporção fixa do salário informado."""
    return {
        categoria: round(salario * percentual, 2)
        for categoria, percentual in PERCENTUAIS_LIMITE_CATEGORIA.items()
    }


# Ordem em que categorias com déficit disputam as fontes de cascata dentro do
# mesmo mês — a issue não define prioridade entre elas, então a ordem é fixa
# e determinística (não a ordem de fallback dentro de uma categoria, que é
# sempre Lazer -> Emergência mês -> Emergência acumulado).
ORDEM_GATILHO_CASCATA = ("GASTO_FIXO_CASA", "MERCADO_ESSENCIAL", "EMERGENCIA")


def _valor_no_mes(gasto):
    return gasto["valor_parcela"] if gasto["tipo"] == "credito" else gasto["valor_total"]


def _gastos_da_categoria_no_mes_ordenados(gastos, categoria, ano, mes):
    """Gastos de uma categoria com valor no mês informado, em ordem
    cronológica de compra — define a ordem de atribuição da cascata quando
    vários gastos disputam a mesma fonte no mesmo mês."""
    relevantes = [
        g for g in gastos
        if g["categoria"] == categoria and (
            _parcela_vence_no_mes(g, ano, mes) if g["tipo"] == "credito"
            else g["data"][:7] == f"{ano:04d}-{mes:02d}"
        )
    ]
    return sorted(relevantes, key=lambda g: g["data"])


def _calcular_cascata_mes(gastos, ano, mes, limites, saldo_acumulado_emergencia):
    """Calcula, sem persistir nada, como a cascata cobriria os déficits de
    Gasto Fixo Casa, Mercado Essencial e Emergência num mês. Investimento
    nunca participa (nem gatilho nem fonte); Emergência, quando é o gatilho,
    só pode puxar de Lazer, nunca de si mesma.

    Retorna as alocações por gasto (pra registrar rastreabilidade), o resumo
    de déficit/cobertura por categoria, e quanto foi consumido de cada nível
    da Emergência (pra quem for fechar o mês decidir o que persistir).
    """
    usado = {cat: _usado_categoria_mes(gastos, cat, ano, mes) for cat in CATEGORIAS_VALIDAS}

    pool_lazer = max(0.0, limites["LAZER"] - usado["LAZER"])
    pool_emergencia_mes = max(0.0, limites["EMERGENCIA"] - usado["EMERGENCIA"])
    pool_emergencia_acumulado = max(0.0, saldo_acumulado_emergencia)

    consumo_emergencia_mes_por_outras = 0.0
    consumo_emergencia_acumulado = 0.0
    alocacoes = {}
    resumo = {}
    mes_rotulo = f"{ano:04d}-{mes:02d}"

    for categoria in ORDEM_GATILHO_CASCATA:
        deficit_total = round(usado[categoria] - limites[categoria], 2)
        resumo[categoria] = {"deficit": max(0.0, deficit_total), "coberto": 0.0, "nao_coberto": 0.0}
        if deficit_total <= 0:
            continue

        pode_usar_emergencia = categoria != "EMERGENCIA"
        usado_acumulado = 0.0
        coberto_total = 0.0

        for gasto in _gastos_da_categoria_no_mes_ordenados(gastos, categoria, ano, mes):
            deficit_antes = max(0.0, usado_acumulado - limites[categoria])
            usado_acumulado += _valor_no_mes(gasto)
            deficit_depois = max(0.0, usado_acumulado - limites[categoria])
            fatia = round(deficit_depois - deficit_antes, 2)
            if fatia <= 0:
                continue

            restante = fatia
            eventos = []

            usar = round(min(restante, pool_lazer), 2)
            if usar > 0:
                pool_lazer -= usar
                restante -= usar
                eventos.append({"mes": mes_rotulo, "origem": "LAZER", "nivel": "mes", "valor": usar})

            if restante > 0 and pode_usar_emergencia:
                usar = round(min(restante, pool_emergencia_mes), 2)
                if usar > 0:
                    pool_emergencia_mes -= usar
                    consumo_emergencia_mes_por_outras += usar
                    restante -= usar
                    eventos.append({"mes": mes_rotulo, "origem": "EMERGENCIA", "nivel": "mes", "valor": usar})

            if restante > 0 and pode_usar_emergencia:
                usar = round(min(restante, pool_emergencia_acumulado), 2)
                if usar > 0:
                    pool_emergencia_acumulado -= usar
                    consumo_emergencia_acumulado += usar
                    restante -= usar
                    eventos.append({"mes": mes_rotulo, "origem": "EMERGENCIA", "nivel": "acumulado", "valor": usar})

            if eventos:
                alocacoes.setdefault(gasto["id"], []).extend(eventos)
            coberto_total += fatia - restante

        resumo[categoria]["coberto"] = round(coberto_total, 2)
        resumo[categoria]["nao_coberto"] = round(deficit_total - coberto_total, 2)

    return {
        "alocacoes": alocacoes,
        "resumo_por_categoria": resumo,
        "consumo_emergencia_mes_por_outras": round(consumo_emergencia_mes_por_outras, 2),
        "consumo_emergencia_acumulado": round(consumo_emergencia_acumulado, 2),
        "pool_emergencia_mes_inicial": round(max(0.0, limites["EMERGENCIA"] - usado["EMERGENCIA"]), 2),
    }


def _fechar_mes(dados, gastos, ano, mes):
    """Fecha um mês definitivamente: aplica a cascata calculada nos gastos
    daquele mês (persistindo a origem em `cascata`) e ajusta o acumulado de
    Emergência. A contribuição própria da Emergência pro acumulado nunca é
    negativa — se ela mesma estourou, o rombo foi coberto por Lazer (ou ficou
    descoberto), nunca pelo próprio acumulado."""
    limites = calcular_limites_categoria(dados["salario"])
    saldo_acumulado_antes = dados.get("saldo_acumulado_emergencia", 0.0)
    resultado = _calcular_cascata_mes(gastos, ano, mes, limites, saldo_acumulado_antes)

    for gasto in dados["gastos"]:
        eventos = resultado["alocacoes"].get(gasto["id"])
        if eventos:
            gasto.setdefault("cascata", []).extend(eventos)

    contribuicao_propria = resultado["pool_emergencia_mes_inicial"] - resultado["consumo_emergencia_mes_por_outras"]
    novo_acumulado = saldo_acumulado_antes + contribuicao_propria - resultado["consumo_emergencia_acumulado"]
    dados["saldo_acumulado_emergencia"] = round(novo_acumulado, 2)


def _avancar_fechamento_mensal(dados, gastos, ano_atual, mes_atual):
    """Fecha, um mês de cada vez, todo mês pendente até alcançar o mês atual
    (cascata + acumulado de Emergência). Retorna True se `dados` foi alterado
    (precisa persistir).

    Usa o salário atual pra estimar limites de meses passados, já que não
    existe histórico de salário por mês — simplificação aceitável pra um app
    pessoal de um usuário só.
    """
    ultimo = dados.get("ultimo_mes_fechado")
    if ultimo is None:
        dados["ultimo_mes_fechado"] = f"{ano_atual:04d}-{mes_atual:02d}"
        dados.setdefault("saldo_acumulado_emergencia", 0.0)
        return True

    ano_r, mes_r = (int(p) for p in ultimo.split("-"))
    if (ano_r, mes_r) >= (ano_atual, mes_atual):
        return False

    while (ano_r, mes_r) < (ano_atual, mes_atual):
        _fechar_mes(dados, gastos, ano_r, mes_r)
        ano_r, mes_r = _mes_seguinte(ano_r, mes_r)

    dados["ultimo_mes_fechado"] = f"{ano_r:04d}-{mes_r:02d}"
    return True


def calcular_saldos_categoria():
    """Motor central de orçamento: limite, usado e disponível de cada
    categoria no mês atual. Emergência também carrega `saldo_acumulado`, a
    reserva que fecha mês a mês. Gasto Fixo Casa, Mercado Essencial e
    Emergência carregam `cascata_previa`: como a cascata cobriria o déficit
    se o mês fechasse agora — cálculo ao vivo, não persistido (só vira
    definitivo, com rastreabilidade por gasto, quando o mês realmente fecha).
    """
    dados = _carregar()
    gastos = [calcular_derivados(g) for g in dados["gastos"]]
    ano_atual, mes_atual = _mes_atual()

    if _avancar_fechamento_mensal(dados, gastos, ano_atual, mes_atual):
        _salvar(dados)
        gastos = [calcular_derivados(g) for g in dados["gastos"]]

    limites = calcular_limites_categoria(dados["salario"])
    saldos = {}
    for categoria in CATEGORIAS_VALIDAS:
        usado = _usado_categoria_mes(gastos, categoria, ano_atual, mes_atual)
        limite = limites[categoria]
        saldos[categoria] = {
            "limite": limite,
            "usado": usado,
            "disponivel": round(limite - usado, 2),
        }

    saldo_acumulado = dados.get("saldo_acumulado_emergencia", 0.0)
    saldos["EMERGENCIA"]["saldo_acumulado"] = saldo_acumulado

    previa = _calcular_cascata_mes(gastos, ano_atual, mes_atual, limites, saldo_acumulado)
    for categoria in ORDEM_GATILHO_CASCATA:
        saldos[categoria]["cascata_previa"] = previa["resumo_por_categoria"][categoria]

    return saldos


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
        "saldos_categoria": calcular_saldos_categoria(),
    }


def exportar_dados():
    return _carregar()


def importar_dados(dados):
    if not isinstance(dados, dict) or "salario" not in dados or "gastos" not in dados:
        raise ValueError("Arquivo JSON inválido: esperado objeto com 'salario' e 'gastos'.")
    _salvar(dados)
