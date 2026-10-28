// ===================================================
// OFICINA DIGITAL - PORTAL DE SERVIÇOS GOV.BR (script.js)
// Comunicação com a API FastAPI em http://localhost:8000
// ===================================================

const API_BASE = "http://localhost:8000";

// Elementos da página
const statusApi = document.getElementById("statusApi");
const textoStatusApi = document.getElementById("textoStatusApi");
const avisoApiDesligada = document.getElementById("avisoApiDesligada");
const btnAltoContraste = document.getElementById("btnAltoContraste");

const formAbrirChamado = document.getElementById("formAbrirChamado");
const campoNome = document.getElementById("nome");
const campoContato = document.getElementById("contato");
const campoEquipamento = document.getElementById("equipamento");
const campoRelato = document.getElementById("relato");
const btnExemplo = document.getElementById("btnExemplo");

const sucessoChamado = document.getElementById("sucessoChamado");
const valorNumeroChamado = document.getElementById("valorNumeroChamado");
const erroEnvio = document.getElementById("erroEnvio");
const msgErroEnvio = document.getElementById("msgErroEnvio");

const formAcompanhar = document.getElementById("formAcompanhar");
const campoNumeroConsulta = document.getElementById("numeroConsulta");
const dadosChamado = document.getElementById("dadosChamado");
const erroConsulta = document.getElementById("erroConsulta");
const msgErroConsulta = document.getElementById("msgErroConsulta");

const detalheNumero = document.getElementById("detalheNumero");
const detalheEquipamento = document.getElementById("detalheEquipamento");
const detalheData = document.getElementById("detalheData");
const detalheStatus = document.getElementById("detalheStatus");
const detalhePrioridade = document.getElementById("detalhePrioridade");
const detalheLaudo = document.getElementById("detalheLaudo");

// ---------------------------------------------------
// 0. ACESSIBILIDADE GOV.BR: ALTO CONTRASTE
// ---------------------------------------------------
if (btnAltoContraste) {
  btnAltoContraste.addEventListener("click", () => {
    document.body.classList.toggle("alto-contraste");
  });
}

// ---------------------------------------------------
// 1. VERIFICAR SE A API ESTÁ LIGADA OU DESLIGADA
// ---------------------------------------------------
async function verificarConexaoApi() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const resposta = await fetch(`${API_BASE}/`, {
      method: "GET",
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    // Se o servidor respondeu com 200, a API está online!
    definirStatusApi(resposta.ok);
  } catch (erro) {
    // Falha de rede: API desligada
    definirStatusApi(false);
  }
}

function definirStatusApi(ligada) {
  statusApi.className = "status-api " + (ligada ? "online" : "offline");
  
  if (ligada) {
    textoStatusApi.textContent = "API conectada (localhost:8000)";
    avisoApiDesligada.style.display = "none";
  } else {
    textoStatusApi.textContent = "API desconectada";
    avisoApiDesligada.style.display = "flex";
  }
}

// ---------------------------------------------------
// 2. BOTÃO PARA PREENCHER UM EXEMPLO DE TESTE
// ---------------------------------------------------
btnExemplo.addEventListener("click", () => {
  campoNome.value = "Mateus Silva";
  campoContato.value = "11988887777";
  campoEquipamento.value = "Dell G15";
  campoRelato.value = "Dell G15 desliga sozinho depois de 10 minutos jogando";
  campoNome.focus();
});

// ---------------------------------------------------
// 3. ABRIR CHAMADO (POST /chamados)
// Envia exatamente: { "nome", "contato", "equipamento", "relato" }
// Recebe exatamente: { "numero", "status" }
// ---------------------------------------------------
formAbrirChamado.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  sucessoChamado.style.display = "none";
  erroEnvio.style.display = "none";

  const nome = campoNome.value.trim();
  const contato = campoContato.value.trim();
  const equipamento = campoEquipamento.value.trim();
  const relato = campoRelato.value.trim();

  // Validação simples
  if (!nome || !contato || !equipamento || !relato) {
    mostrarErroEnvio("Por favor, preencha todos os quatro campos obrigatórios.");
    return;
  }

  const dadosParaEnviar = {
    nome: nome,
    contato: contato,
    equipamento: equipamento,
    relato: relato
  };

  try {
    const resposta = await fetch(`${API_BASE}/chamados`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(dadosParaEnviar)
    });

    if (!resposta.ok) {
      throw new Error(`A API respondeu com código de erro (${resposta.status}).`);
    }

    const resultado = await resposta.json();
    definirStatusApi(true);

    // Sucesso: exibe o número do protocolo/chamado
    valorNumeroChamado.textContent = `#${resultado.numero}`;
    sucessoChamado.style.display = "block";

    // Preenche automaticamente o campo de consulta para facilitar o cidadão
    campoNumeroConsulta.value = resultado.numero;

    // Limpa os campos do formulário
    formAbrirChamado.reset();

  } catch (erro) {
    definirStatusApi(false);
    mostrarErroEnvio(
      "Aviso: A API está desligada ou inacessível. Inicie o servidor FastAPI em http://localhost:8000 para protocolar chamados."
    );
  }
});

function mostrarErroEnvio(mensagem) {
  msgErroEnvio.textContent = mensagem;
  erroEnvio.style.display = "flex";
}

// ---------------------------------------------------
// 4. ACOMPANHAR CHAMADO (GET /chamados/{numero})
// Recebe: { "numero", "equipamento", "status", "prioridade", "laudo", "data" }
// Se "laudo" vier vazio: mostra "A triagem ainda está trabalhando"
// ---------------------------------------------------
formAcompanhar.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  dadosChamado.style.display = "none";
  erroConsulta.style.display = "none";

  const numero = campoNumeroConsulta.value.trim();

  if (!numero) {
    mostrarErroConsulta("Por favor, informe o número do chamado a ser consultado.");
    return;
  }

  try {
    const resposta = await fetch(`${API_BASE}/chamados/${numero}`);

    if (resposta.status === 404) {
      definirStatusApi(true);
      mostrarErroConsulta(`Chamado número #${numero} não foi encontrado na base de dados.`);
      return;
    }

    if (!resposta.ok) {
      throw new Error(`Erro na consulta (código ${resposta.status}).`);
    }

    const chamado = await resposta.json();
    definirStatusApi(true);

    // Atualiza os dados na tela
    detalheNumero.textContent = `#${chamado.numero}`;
    detalheEquipamento.textContent = chamado.equipamento || "Não informado";
    detalheData.textContent = chamado.data || "Data não registrada";
    detalheStatus.textContent = formatarStatus(chamado.status);
    detalhePrioridade.textContent = formatarPrioridade(chamado.prioridade);

    // Regra do laudo:
    // Se "laudo" vier vazio, mostre "A triagem ainda está trabalhando"
    if (!chamado.laudo || chamado.laudo.trim() === "") {
      detalheLaudo.textContent = "A triagem ainda está trabalhando";
    } else {
      detalheLaudo.textContent = chamado.laudo;
    }

    dadosChamado.style.display = "block";

  } catch (erro) {
    definirStatusApi(false);
    mostrarErroConsulta(
      "Aviso: A API está desligada. Ligue o servidor FastAPI em http://localhost:8000 para consultar o chamado."
    );
  }
});

function mostrarErroConsulta(mensagem) {
  msgErroConsulta.textContent = mensagem;
  erroConsulta.style.display = "flex";
}

// Funções para formatar rótulos oficiais
function formatarStatus(status) {
  if (!status) return "Pendente";
  if (status === "aberto") return "Aberto";
  if (status === "em_andamento") return "Em andamento";
  if (status === "concluido") return "Concluído";
  return status;
}

function formatarPrioridade(prioridade) {
  if (!prioridade) return "Em análise";
  if (prioridade.toLowerCase() === "alta") {
    detalhePrioridade.className = "selo-oficial selo-prioridade alta";
    return "Prioridade Alta";
  }
  detalhePrioridade.className = "selo-oficial selo-prioridade";
  return `Prioridade ${prioridade}`;
}

// Verificação periódica de conexão
verificarConexaoApi();
setInterval(verificarConexaoApi, 10000);
