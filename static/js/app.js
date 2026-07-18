// Gestor de Gastos Pessoais — lógica do frontend
const API = {
  resumo: "/api/resumo",
  salario: "/api/salario",
  metaInvestimento: "/api/meta-investimento",
  gastos: "/api/gastos",
  export: "/api/export",
  import: "/api/import",
};

const ROTULOS_TIPO = { credito: "Crédito", debito: "Débito", pix: "Pix" };

const ROTULOS_CATEGORIA = {
  INVESTIMENTO: "Investimento",
  GASTO_FIXO_CASA: "Gasto fixo da casa",
  MERCADO_ESSENCIAL: "Mercado essencial",
  EMERGENCIA: "Emergência",
  LAZER: "Lazer",
};

function formatarMoeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function escaparHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

function formatarDataBr(dataIso) {
  if (!dataIso) return "—";
  const [ano, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}/${ano}`;
}

function montarQueryFiltros() {
  const banco = document.getElementById("filtro-banco").value;
  const tipo = document.getElementById("filtro-tipo").value;
  const params = new URLSearchParams();
  if (banco) params.set("banco", banco);
  if (tipo) params.set("tipo", tipo);
  return params.toString();
}

async function carregarBancos() {
  const resp = await fetch(API.gastos);
  const gastos = await resp.json();
  const select = document.getElementById("filtro-banco");
  const bancoSelecionado = select.value;
  const bancos = [...new Set(gastos.map((g) => g.banco))].sort();

  select.innerHTML = '<option value="">Todos os bancos</option>';
  for (const banco of bancos) {
    const opcao = document.createElement("option");
    opcao.value = banco;
    opcao.textContent = banco;
    select.appendChild(opcao);
  }
  select.value = bancos.includes(bancoSelecionado) ? bancoSelecionado : "";
}

async function carregarGastos() {
  const query = montarQueryFiltros();
  const resp = await fetch(`${API.gastos}${query ? "?" + query : ""}`);
  const gastos = await resp.json();
  renderizarTabela(gastos);
}

function renderizarTabela(gastos) {
  const corpo = document.getElementById("tabela-gastos-corpo");
  const vazio = document.getElementById("lista-vazia");
  corpo.innerHTML = "";

  vazio.hidden = gastos.length > 0;

  for (const gasto of gastos) {
    const linha = document.createElement("tr");

    const parcelaTexto =
      gasto.tipo === "credito"
        ? `${gasto.parcelas_pagas}/${gasto.parcelas_total}`
        : "à vista";

    linha.innerHTML = `
      <td>${escaparHtml(gasto.descricao)}</td>
      <td><span class="badge badge-${gasto.tipo}">${ROTULOS_TIPO[gasto.tipo]}</span></td>
      <td>${escaparHtml(gasto.banco)}</td>
      <td>${formatarMoeda(gasto.valor_total)}</td>
      <td>${formatarMoeda(gasto.valor_parcela)}</td>
      <td>${gasto.tipo === "credito" ? parcelaTexto : "—"}</td>
      <td>${ROTULOS_CATEGORIA[gasto.categoria] || "—"}</td>
      <td>${formatarDataBr(gasto.data)}</td>
      <td class="acoes-linha">
        <button title="Editar" data-acao="editar" data-id="${gasto.id}">✏️</button>
        <button title="Excluir" data-acao="excluir" data-id="${gasto.id}">🗑️</button>
      </td>
    `;
    corpo.appendChild(linha);
  }
}

async function excluirGasto(id) {
  if (!confirm("Tem certeza que deseja excluir este gasto?")) return;
  await fetch(`${API.gastos}/${id}`, { method: "DELETE" });
  await Promise.all([carregarGastos(), carregarResumo()]);
}

function alternarCamposParcelas() {
  const tipo = document.getElementById("gasto-tipo").value;
  document.getElementById("grupo-parcelas").hidden = tipo !== "credito";
}

function abrirModal(titulo) {
  document.getElementById("modal-titulo").textContent = titulo;
  document.getElementById("form-erro").hidden = true;
  document.getElementById("modal-gasto").hidden = false;
}

function fecharModal() {
  document.getElementById("modal-gasto").hidden = true;
  document.getElementById("form-gasto").reset();
}

function abrirModalParaCriar() {
  document.getElementById("form-gasto").reset();
  document.getElementById("gasto-id").value = "";
  document.getElementById("gasto-data").value = new Date().toISOString().slice(0, 10);
  alternarCamposParcelas();
  abrirModal("Novo gasto");
}

async function abrirModalParaEditar(id) {
  const resp = await fetch(API.gastos);
  const gastos = await resp.json();
  const gasto = gastos.find((g) => g.id === id);
  if (!gasto) return;

  document.getElementById("gasto-id").value = gasto.id;
  document.getElementById("gasto-descricao").value = gasto.descricao;
  document.getElementById("gasto-valor-total").value = gasto.valor_total;
  document.getElementById("gasto-tipo").value = gasto.tipo;
  document.getElementById("gasto-banco").value = gasto.banco;
  document.getElementById("gasto-data").value = gasto.data;
  document.getElementById("gasto-parcelas-total").value = gasto.parcelas_total;
  document.getElementById("gasto-parcelas-pagas").value = gasto.parcelas_pagas;
  document.getElementById("gasto-categoria").value = gasto.categoria || "";

  alternarCamposParcelas();
  abrirModal("Editar gasto");
}

function lerPayloadFormulario() {
  return {
    descricao: document.getElementById("gasto-descricao").value,
    valor_total: parseFloat(document.getElementById("gasto-valor-total").value),
    tipo: document.getElementById("gasto-tipo").value,
    banco: document.getElementById("gasto-banco").value,
    data: document.getElementById("gasto-data").value,
    parcelas_total: parseInt(document.getElementById("gasto-parcelas-total").value || "1", 10),
    parcelas_pagas: parseInt(document.getElementById("gasto-parcelas-pagas").value || "0", 10),
    categoria: document.getElementById("gasto-categoria").value,
  };
}

async function salvarGasto(evento) {
  evento.preventDefault();
  const id = document.getElementById("gasto-id").value;
  const payload = lerPayloadFormulario();
  const erroEl = document.getElementById("form-erro");
  erroEl.hidden = true;

  const url = id ? `${API.gastos}/${id}` : API.gastos;
  const metodo = id ? "PUT" : "POST";

  const resp = await fetch(url, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const erro = await resp.json();
    erroEl.textContent = erro.erro || "Não foi possível salvar o gasto.";
    erroEl.hidden = false;
    return;
  }

  fecharModal();
  await Promise.all([carregarGastos(), carregarResumo(), carregarBancos()]);
}

async function carregarResumo() {
  const resp = await fetch(API.resumo);
  const resumo = await resp.json();

  document.getElementById("input-salario").value = resumo.salario;
  document.getElementById("input-meta-investimento").value = resumo.meta_investimento;
  document.getElementById("resumo-total-gasto-mes").textContent = formatarMoeda(resumo.total_gasto_mes);
  document.getElementById("resumo-total-a-pagar").textContent = formatarMoeda(resumo.total_a_pagar_parcelas);

  const elSobra = document.getElementById("resumo-sobra-salario");
  elSobra.textContent = formatarMoeda(resumo.sobra_salario);
  document.getElementById("card-sobra").classList.toggle("negativo", resumo.sobra_salario < 0);
}

async function salvarSalario() {
  const input = document.getElementById("input-salario");
  const valor = parseFloat(input.value);
  if (Number.isNaN(valor) || valor < 0) {
    alert("Informe um salário válido.");
    return;
  }
  await fetch(API.salario, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ salario: valor }),
  });
  await carregarResumo();
}

async function salvarMetaInvestimento() {
  const input = document.getElementById("input-meta-investimento");
  const valor = parseFloat(input.value);
  if (Number.isNaN(valor) || valor < 0) {
    alert("Informe uma meta de investimento válida.");
    return;
  }
  await fetch(API.metaInvestimento, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ meta_investimento: valor }),
  });
  await carregarResumo();
}

async function exportarDados() {
  const resp = await fetch(API.export);
  const dados = await resp.json();
  const blob = new Blob([JSON.stringify(dados, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `gastos-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

async function importarDados(arquivo) {
  const texto = await arquivo.text();
  let dados;
  try {
    dados = JSON.parse(texto);
  } catch {
    alert("Arquivo inválido: não é um JSON válido.");
    return;
  }

  const resp = await fetch(API.import, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });

  if (!resp.ok) {
    const erro = await resp.json();
    alert(erro.erro || "Não foi possível importar o arquivo.");
    return;
  }

  await Promise.all([carregarGastos(), carregarResumo(), carregarBancos()]);
}

function inicializar() {
  document.getElementById("btn-salvar-salario").addEventListener("click", salvarSalario);
  document.getElementById("btn-salvar-meta-investimento").addEventListener("click", salvarMetaInvestimento);

  document.getElementById("tabela-gastos-corpo").addEventListener("click", (evento) => {
    const botao = evento.target.closest("button[data-acao]");
    if (!botao) return;
    if (botao.dataset.acao === "excluir") {
      excluirGasto(botao.dataset.id);
    } else if (botao.dataset.acao === "editar") {
      abrirModalParaEditar(botao.dataset.id);
    }
  });

  document.getElementById("btn-novo-gasto").addEventListener("click", abrirModalParaCriar);
  document.getElementById("btn-cancelar-modal").addEventListener("click", fecharModal);
  document.getElementById("gasto-tipo").addEventListener("change", alternarCamposParcelas);
  document.getElementById("form-gasto").addEventListener("submit", salvarGasto);

  document.getElementById("filtro-banco").addEventListener("change", carregarGastos);
  document.getElementById("filtro-tipo").addEventListener("change", carregarGastos);

  document.getElementById("btn-exportar").addEventListener("click", exportarDados);
  document.getElementById("btn-importar").addEventListener("click", () => {
    document.getElementById("input-importar").click();
  });
  document.getElementById("input-importar").addEventListener("change", (evento) => {
    const [arquivo] = evento.target.files;
    if (arquivo) importarDados(arquivo);
    evento.target.value = "";
  });

  carregarResumo();
  carregarGastos();
  carregarBancos();
}

document.addEventListener("DOMContentLoaded", inicializar);
