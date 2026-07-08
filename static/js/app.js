// Gestor de Gastos Pessoais — lógica do frontend
const API = {
  resumo: "/api/resumo",
  salario: "/api/salario",
  gastos: "/api/gastos",
};

const ROTULOS_TIPO = { credito: "Crédito", debito: "Débito", pix: "Pix" };

function formatarMoeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
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
      <td>${gasto.descricao}</td>
      <td><span class="badge badge-${gasto.tipo}">${ROTULOS_TIPO[gasto.tipo]}</span></td>
      <td>${gasto.banco}</td>
      <td>${formatarMoeda(gasto.valor_total)}</td>
      <td>${formatarMoeda(gasto.valor_parcela)}</td>
      <td>${gasto.tipo === "credito" ? parcelaTexto : "—"}</td>
      <td>${gasto.categoria || "—"}</td>
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

async function carregarResumo() {
  const resp = await fetch(API.resumo);
  const resumo = await resp.json();

  document.getElementById("input-salario").value = resumo.salario;
  document.getElementById("resumo-total-gasto-mes").textContent = formatarMoeda(resumo.total_gasto_mes);
  document.getElementById("resumo-total-a-pagar").textContent = formatarMoeda(resumo.total_a_pagar_parcelas);
  document.getElementById("resumo-parcelas-faltando").textContent = resumo.parcelas_faltando_total;

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

function inicializar() {
  document.getElementById("btn-salvar-salario").addEventListener("click", salvarSalario);

  document.getElementById("tabela-gastos-corpo").addEventListener("click", (evento) => {
    const botao = evento.target.closest("button[data-acao]");
    if (!botao) return;
    if (botao.dataset.acao === "excluir") {
      excluirGasto(botao.dataset.id);
    }
  });

  carregarResumo();
  carregarGastos();
}

document.addEventListener("DOMContentLoaded", inicializar);
