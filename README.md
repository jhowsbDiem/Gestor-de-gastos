# 💰 Gestor de Gastos Pessoais

[![Licença: uso pessoal](https://img.shields.io/badge/uso-pessoal-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](#-stack-utilizada)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000.svg?logo=flask&logoColor=white)](#-stack-utilizada)

Painel web local para controlar salário, gastos de **crédito parcelado**, **débito** e **Pix**, saber quanto ainda falta pagar de parcelas e quanto sobra do salário no mês. Todos os dados ficam em um arquivo **JSON no seu disco** — nada é enviado para nuvem ou banco de dados externo.

---

## 📌 Principais funcionalidades

- **Dashboard**: data de hoje em destaque, salário editável direto na tela e resumo com total gasto no mês, total ainda a pagar em parcelas, quantas parcelas faltam e quanto sobra do salário.
- **Gastos**: cadastro, edição e exclusão pela própria interface (sem editar JSON na mão), com descrição, valor, tipo (crédito/débito/Pix), banco, data, parcelas e categoria.
- **Parcelas**: cálculo automático de valor da parcela, parcelas faltantes, valor restante e próxima data de vencimento para compras no crédito.
- **Filtros**: por banco e por tipo de gasto.
- **Backup**: exportar e importar todo o histórico em JSON.
- Interface em **português (pt-BR)**, responsiva para uso no celular.

---

## 🛠️ Stack utilizada

- **Backend:** Python 3 + Flask — API REST que lê e escreve o arquivo JSON.
- **Frontend:** HTML + CSS + JavaScript puro (sem framework), consumindo a API via `fetch`.
- **Persistência:** arquivo local `data/gastos.json`. Sem banco de dados.

---

## 🗂️ Estrutura do Repositório

```text
.
├── app.py                     # Rotas Flask (API + página principal)
├── models.py                  # Modelo de dados, regras de negócio e persistência em JSON
├── requirements.txt           # Dependências Python
├── data/
│   ├── gastos.example.json    # Dados fictícios versionados (ponto de partida)
│   └── gastos.json            # Seus dados reais — ignorado pelo Git
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
└── .gitignore
```

---

## ▶️ Como rodar localmente

1. **Pré-requisito:** Python 3.10+ instalado.
2. Crie e ative um ambiente virtual (opcional, mas recomendado):

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Rode o servidor:

   ```bash
   python app.py
   ```

5. Acesse **http://localhost:5000** no navegador.

Na primeira execução, se `data/gastos.json` ainda não existir, ele é criado automaticamente a partir de `data/gastos.example.json`.

---

## 🧾 Estrutura do JSON

```json
{
  "salario": 5000.00,
  "gastos": [
    {
      "id": "uuid",
      "descricao": "Notebook",
      "valor_total": 3000.00,
      "tipo": "credito",
      "banco": "Nubank",
      "data": "2026-07-08",
      "parcelas_total": 10,
      "parcelas_pagas": 3,
      "categoria": "Eletrônicos"
    }
  ]
}
```

- `tipo` aceita `"credito"`, `"debito"` ou `"pix"`. Débito e Pix sempre usam `parcelas_total = 1`.
- Campos **derivados** (calculados pelo backend a cada requisição, nunca salvos no arquivo): `valor_parcela`, `parcelas_faltantes`, `valor_restante` e `proxima_data_vencimento`.
- Valores em Reais (R$); datas armazenadas em `aaaa-mm-dd` e exibidas na interface em `dd/mm/aaaa`.

---

## 🔒 Privacidade dos dados

- `data/gastos.json` (seus dados reais) está no `.gitignore` e **nunca** é versionado.
- Apenas `data/gastos.example.json`, com dados fictícios, é commitado — garantindo que o projeto funcione em qualquer máquina sem expor seus gastos.
- Use os botões **Exportar/Importar** da interface para levar seu histórico entre computadores.

---

## 📸 Screenshots

_Espaço reservado para prints do dashboard e da lista de gastos._

---

Desenvolvido para uso pessoal, seguindo o padrão de documentação e commits de [mastering-github-docs](https://github.com/jhowsbDiem/mastering-github-docs).
