"""
Módulo de Triagem com Grafo de Conhecimento (Oficina Digital)
Funciona 100% OFFLINE (sem internet e sem chaves de API).

O Grafo de Conhecimento modela as relações:
(Aparelho) -[apresenta_sintoma]-> (Sintoma) -[causado_por]-> (Causa) -[requer_peca]-> (Peça)
"""

import functools
import unicodedata
from typing import Optional, Dict, Tuple, Any
import networkx as nx

# Os 7 casos exatos catalogados da oficina
CASOS_CONHECIDOS = [
    {
        "aparelho": "Dell G15",
        "sintoma": "desliga sozinho",
        "causa": "pasta térmica de fábrica ressecada e aletas obstruídas",
        "pecas": "Pasta Térmica Alta Condutividade, Thermal Pads"
    },
    {
        "aparelho": "Dell G15",
        "sintoma": "não liga",
        "causa": "curto no circuito de carga (MOSFET de entrada)",
        "pecas": "MOSFET Canal N 30V, Carregador 130W"
    },
    {
        "aparelho": "Acer Nitro 5",
        "sintoma": "tela azul",
        "causa": "oxidação nos contatos da memória RAM",
        "pecas": "Limpa Contato Isopropílico, Memória DDR4"
    },
    {
        "aparelho": "Acer Nitro 5",
        "sintoma": "tela preta",
        "causa": "cabo flat da tela rompido ou solto na dobradiça",
        "pecas": "Cabo Flat EDP Nitro 5"
    },
    {
        "aparelho": "MacBook Air",
        "sintoma": "bateria não carrega",
        "causa": "ciclos da bateria esgotados ou conector oxidado",
        "pecas": "Bateria Original A1466"
    },
    {
        "aparelho": "Desktop",
        "sintoma": "reinicia em jogos",
        "causa": "fonte genérica sem potência suficiente",
        "pecas": "Fonte ATX 600W 80 Plus"
    },
    {
        "aparelho": "Notebook",
        "sintoma": "lentidão extrema",
        "causa": "HD mecânico antigo com setores ruins",
        "pecas": "SSD NVMe 500GB ou SATA"
    }
]


@functools.lru_cache(maxsize=1024)
def normalizar(texto: str) -> str:
    """
    Remove acentos, converte para minúsculas e remove espaços extras.
    Ex: 'Não Liga' -> 'nao liga'
    """
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.lower().strip()


def construir_grafo_conhecimento() -> nx.DiGraph:
    """
    Constrói um Grafo Direcionado (DiGraph) do NetworkX contendo as
    entidades e relações ontológicas da oficina técnica:
      (Aparelho) ---> (Sintoma) ---> (Causa) ---> (Peça)
    """
    g = nx.DiGraph()

    for caso in CASOS_CONHECIDOS:
        aparelho = caso["aparelho"]
        sintoma = caso["sintoma"]
        causa = caso["causa"]
        pecas = caso["pecas"]

        # Adiciona os nós identificados com seus respectivos tipos
        g.add_node(aparelho, tipo="aparelho")
        g.add_node(sintoma, tipo="sintoma")
        g.add_node(causa, tipo="causa")
        g.add_node(pecas, tipo="peca")

        # Conecta as entidades com arestas tipadas
        g.add_edge(aparelho, sintoma, relacao="apresenta_sintoma")
        g.add_edge(sintoma, causa, relacao="causado_por")
        g.add_edge(causa, pecas, relacao="requer_peca")

    return g


# Instância global do grafo em memória (acesso rápido)
grafo = construir_grafo_conhecimento()


def buscar_no_grafo(
    equipamento: str,
    relato: str,
    grafo_conhecimento: Optional[nx.DiGraph] = None
) -> Optional[Dict[str, str]]:
    """
    Pesquisa o aparelho e o sintoma no Grafo de Conhecimento.
    Se encontrar um caminho válido (Aparelho -> Sintoma -> Causa -> Peça),
    retorna um dicionário com os elementos correspondentes.
    """
    g = grafo_conhecimento if grafo_conhecimento is not None else grafo

    equip_norm = normalizar(equipamento)
    relato_norm = normalizar(relato)

    # 1. Recupera todos os nós de aparelho no grafo
    aparelhos_grafo = [n for n, d in g.nodes(data=True) if d.get("tipo") == "aparelho"]
    # Ordena por tamanho para casar nomes mais específicos primeiro (ex: 'Dell G15' antes de 'Notebook')
    aparelhos_grafo.sort(key=len, reverse=True)

    texto_busca = f"{equip_norm} {relato_norm}"

    aparelhos_candidatos = []
    for ap in aparelhos_grafo:
        ap_norm = normalizar(ap)
        # Verifica se o nome completo do aparelho está no equipamento ou relato
        if ap_norm in equip_norm or ap_norm in relato_norm:
            aparelhos_candidatos.append(ap)
        # Verifica se o texto do equipamento é um subtítulo do aparelho (mínimo 3 caracteres, ex: 'g15', 'nitro', 'macbook')
        elif len(equip_norm) >= 3 and equip_norm in ap_norm:
            aparelhos_candidatos.append(ap)

    # Se ainda não identificou pelo nome do aparelho, faz inferência por sinônimos
    if not aparelhos_candidatos:
        if any(termo in texto_busca for termo in ["pc gamer", "pc", "computador", "desktop", "gabinete"]):
            if "Desktop" in g:
                aparelhos_candidatos.append("Desktop")
        if any(termo in texto_busca for termo in ["notebook", "laptop"]):
            if "Notebook" in g:
                aparelhos_candidatos.append("Notebook")

    # 2. Navega pelas arestas de sintomas associadas ao aparelho
    for ap in aparelhos_candidatos:
        sintomas_conectados = [
            viz for viz in g.successors(ap)
            if g.nodes[viz].get("tipo") == "sintoma"
        ]

        for sintoma in sintomas_conectados:
            sintoma_norm = normalizar(sintoma)

            # Verifica se o sintoma coincide com o relato do usuário
            match_sintoma = False
            if sintoma_norm in relato_norm:
                match_sintoma = True
            else:
                # Comparações semânticas para termos chave
                if "desliga" in sintoma_norm and "desliga" in relato_norm:
                    match_sintoma = True
                elif "nao liga" in sintoma_norm and ("nao liga" in relato_norm or "não liga" in relato.lower()):
                    match_sintoma = True
                elif "tela azul" in sintoma_norm and "tela azul" in relato_norm:
                    match_sintoma = True
                elif "tela preta" in sintoma_norm and "tela preta" in relato_norm:
                    match_sintoma = True
                elif "bateria" in sintoma_norm and ("bateria" in relato_norm and "carrega" in relato_norm):
                    match_sintoma = True
                elif "reinicia" in sintoma_norm and ("reinicia" in relato_norm and "jog" in relato_norm):
                    match_sintoma = True
                elif "lentid" in sintoma_norm and ("lentid" in relato_norm or "lento" in relato_norm):
                    match_sintoma = True

            if match_sintoma:
                # Percorre o grafo para encontrar a Causa
                causas = [
                    c for c in g.successors(sintoma)
                    if g.nodes[c].get("tipo") == "causa"
                ]
                if not causas:
                    continue
                causa = causas[0]

                # Percorre o grafo para encontrar a Peça sugerida
                pecas = [
                    p for p in g.successors(causa)
                    if g.nodes[p].get("tipo") == "peca"
                ]
                peca = pecas[0] if pecas else ""

                return {
                    "aparelho": ap,
                    "sintoma": sintoma,
                    "causa": causa,
                    "pecas": peca
                }

    return None


def realizar_triagem(
    equipamento: str,
    relato: str,
    grafo_conhecimento: Optional[nx.DiGraph] = None
) -> Tuple[str, str]:
    """
    Realiza a triagem técnica automática usando o Grafo de Conhecimento.

    Regras de negócio:
    - Se achar um caso:
        * prioridade 'alta' quando o relato tiver 'não liga' ou 'desliga', senão 'media'.
        * laudo com a causa e as peças do caso.
    - Se não achar:
        * prioridade 'media'.
        * laudo: 'necessário teste detalhado na bancada.'

    Retorna:
        tuple[str, str]: (prioridade, laudo)
    """
    caso = buscar_no_grafo(equipamento, relato, grafo_conhecimento)
    relato_norm = normalizar(relato)

    if caso:
        # Verifica se o relato possui os termos críticos de alta prioridade
        if "nao liga" in relato_norm or "desliga" in relato_norm:
            prioridade = "alta"
        else:
            prioridade = "media"

        causa = caso["causa"]
        pecas = caso["pecas"]
        laudo = f"{causa}. Peças sugeridas: {pecas}."
        return prioridade, laudo
    else:
        prioridade = "media"
        laudo = "necessário teste detalhado na bancada."
        return prioridade, laudo
