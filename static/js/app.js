// Gestor de Gastos Pessoais — lógica do frontend
const API = {
  resumo: "/api/resumo",
  salario: "/api/salario",
  gastos: "/api/gastos",
};

function formatarMoeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
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
  carregarResumo();
}

document.addEventListener("DOMContentLoaded", inicializar);
