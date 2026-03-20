"""
generate_data.py — Gerador de dados de teste consistentes.

Gera CSVs prontos para upload no front-end ou chamada direta na API.
Re-executar NUNCA apaga dados existentes — só adiciona e atualiza.
Estado persistido em sample_data/state.json.

Saída em sample_data/:
  channels.csv       → POST /api/v1/channels/batch
  stores.csv         → POST /api/v1/stores/batch
  channel_stores.csv → referência dos vínculos canal × loja
  products.csv       → POST /api/v1/products/batch
  customers.csv      → POST /api/v1/customers/batch
  prices.csv         → POST /api/v1/prices/batch
  stock.csv          → POST /api/v1/stock/batch

Para expandir os dados, aumente TOTAL_PRODUCTS / TOTAL_CUSTOMERS
ou adicione itens nas seções MASTER_CHANNELS / MASTER_STORES.
"""
import os
import json
import random
import pandas as pd
from datetime import datetime, timedelta

# ================================================================== #
# CONFIGURAÇÃO — ajuste aqui
# ================================================================== #
TOTAL_PRODUCTS = 150
TOTAL_CUSTOMERS = 80
OUTPUT_DIR = "sample_data"
STATE_FILE = os.path.join(OUTPUT_DIR, "state.json")

# ================================================================== #
# MASTER DATA — edite aqui para adicionar canais, lojas, etc.
# O script detecta itens novos/alterados e atualiza o state.
# ================================================================== #

MASTER_CHANNELS = [
    {
        "channel_id": "CH-WEB",
        "name": "E-commerce",
        "type": "web",
        "store_mode": "single",
        "is_active": True,
        "stores": ["LOJA-WEB"],
    },
    {
        "channel_id": "CH-APP",
        "name": "App Mobile",
        "type": "app",
        "store_mode": "multi",
        "is_active": True,
        "stores": ["LOJA-01", "LOJA-02", "LOJA-03"],
    },
    {
        "channel_id": "CH-FISICO",
        "name": "Lojas Físicas",
        "type": "loja_fisica",
        "store_mode": "multi",
        "is_active": True,
        "stores": ["LOJA-01", "LOJA-02", "LOJA-03", "LOJA-04", "LOJA-05"],
    },
    {
        "channel_id": "CH-TELEVENDAS",
        "name": "Televendas",
        "type": "televendas",
        "store_mode": "single",
        "is_active": True,
        "stores": ["LOJA-TELEVENDAS"],
    },
]

MASTER_STORES = [
    {"store_id": "LOJA-WEB",        "name": "Loja Virtual Web",   "is_active": True},
    {"store_id": "LOJA-TELEVENDAS", "name": "Central Televendas", "is_active": True},
    {"store_id": "LOJA-01",         "name": "Loja Centro",        "is_active": True},
    {"store_id": "LOJA-02",         "name": "Loja Norte",         "is_active": True},
    {"store_id": "LOJA-03",         "name": "Loja Sul",           "is_active": True},
    {"store_id": "LOJA-04",         "name": "Loja Leste",         "is_active": True},
    {"store_id": "LOJA-05",         "name": "Loja Shopping",      "is_active": True},
]

CUSTOMER_TYPES = [
    "restaurante", "padaria", "lanchonete", "mercado",
    "cafeteria", "bar", "pizzaria", "sorveteria", "confeitaria",
]

# ================================================================== #
# GERAÇÃO DE PRODUTOS — determinístico por seed do SKU
# Catálogo estilo varejo generalista (Target/Renner/Extra):
#   30% Roupas Adulto | 10% Roupas Infantil | 20% Alimentos
#   10% TVs | 10% Smartphones | 10% Áudio | 10% Casa & Cozinha
# ================================================================== #

def _seeded(sku_index: int) -> random.Random:
    """Random isolado por SKU — mesmo índice sempre produz os mesmos dados."""
    r = random.Random()
    r.seed(sku_index * 31337)
    return r


# ------------------------------------------------------------------ #
# Roupas Adulto
# ------------------------------------------------------------------ #
_ra_marcas    = ["Hering", "Zara", "Farm", "Colcci", "Forum", "Renner", "C&A", "Riachuelo", "Animale", "Osklen"]
_ra_tipos     = ["Camiseta", "Calça Jeans", "Jaqueta", "Vestido", "Shorts", "Moletom", "Casaco", "Blusa", "Camisa Social", "Calça de Moletom", "Regata", "Macacão", "Pijama"]
_ra_generos   = ["Masculino", "Feminino"]
_ra_cores     = ["Preto", "Branco", "Azul Marinho", "Cinza Mescla", "Verde Militar", "Bege", "Rosa Claro", "Vermelho", "Azul Claro", "Off White", "Caramelo", "Lilás"]
_ra_tamanhos  = ["PP", "P", "M", "G", "GG", "XGG"]
_ra_materiais = ["Algodão 100%", "Algodão + Elastano", "Poliéster Reciclado", "Linho", "Malha Premium", "Jeans Stretch", "Moletom Fleece", "Lã Merino", "Viscose", "Seda Acetinada"]
_ra_temporada = ["Verão", "Inverno", "Meia Estação", "Outlet"]
_ra_fit       = ["Regular Fit", "Slim Fit", "Oversized", "Relaxed Fit", "Cropped", "Straight"]

def _gen_roupa_adulto(idx: int) -> dict:
    r = _seeded(idx)
    marca    = r.choice(_ra_marcas)
    tipo     = r.choice(_ra_tipos)
    genero   = r.choice(_ra_generos)
    cor      = r.choice(_ra_cores)
    tamanho  = r.choice(_ra_tamanhos)
    material = r.choice(_ra_materiais)
    temp     = r.choice(_ra_temporada)
    fit      = r.choice(_ra_fit)
    price    = round(r.uniform(39.90, 699.90), 2)

    name = f"{tipo} {marca} {fit} {cor}"
    cats = [
        f"Roupas > {genero} > {tipo}s",
        f"Roupas > {genero} > {temp}",
        f"{marca} > {genero}",
    ]
    if temp == "Outlet":
        cats.append("Ofertas > Outlet de Moda")

    desc = (
        f"{tipo} {marca} no estilo {fit} para o {temp}. "
        f"Confeccionada em {material}, proporciona conforto e leveza durante todo o dia. "
        f"Cor {cor}, disponível no tamanho {tamanho}. "
        f"Ideal para uso casual, passeios e encontros casuais."
    )
    attrs = {
        "marca": marca, "tipo": tipo, "genero": genero, "cor": cor,
        "tamanho": tamanho, "material": material, "temporada": temp, "fit": fit,
    }
    return {"name": name, "price": price, "category": cats, "attributes": attrs, "description": desc}


# ------------------------------------------------------------------ #
# Roupas Infantil
# ------------------------------------------------------------------ #
_ri_marcas    = ["Carinhoso", "Tip Top", "Lilica Ripilica", "Alphabeto", "Pampili", "Tigor T. Tigre", "Kyly", "Brandili"]
_ri_tipos     = ["Body", "Macacão", "Conjunto Calça + Camiseta", "Vestido Infantil", "Pijama Infantil", "Camiseta Infantil", "Calça Legging", "Shorts Infantil"]
_ri_faixas    = ["0-3 meses", "3-6 meses", "6-12 meses", "1-2 anos", "2-4 anos", "4-6 anos", "6-8 anos", "8-10 anos", "10-12 anos"]
_ri_cores     = ["Rosa", "Azul", "Amarelo", "Verde Água", "Lilás", "Branco", "Estampado Divertido", "Xadrez Colorido"]
_ri_materiais = ["Suedine Macio", "Cotton Penteado", "Ribana Stretch", "Moletom Quentinho", "Malha 100% Algodão"]

def _gen_roupa_infantil(idx: int) -> dict:
    r = _seeded(idx)
    marca    = r.choice(_ri_marcas)
    tipo     = r.choice(_ri_tipos)
    faixa    = r.choice(_ri_faixas)
    cor      = r.choice(_ri_cores)
    material = r.choice(_ri_materiais)
    price    = round(r.uniform(29.90, 199.90), 2)

    name = f"{tipo} {marca} {cor} {faixa}"
    cats = [
        f"Roupas > Infantil > {tipo}s",
        f"Roupas > Infantil > {faixa}",
        f"{marca} > Infantil",
    ]
    desc = (
        f"{tipo} infantil {marca} na cor {cor} para crianças de {faixa}. "
        f"Fabricado em {material}, garantindo maciez e segurança para a pele sensível dos pequenos. "
        f"Fechamento prático com botões de pressão. Lavar à máquina até 40°C."
    )
    attrs = {
        "marca": marca, "tipo": tipo, "faixa_etaria": faixa, "cor": cor, "material": material,
        "fechamento": "Botão de Pressão" if "Body" in tipo or "Macacão" in tipo else "Elástico",
        "lavagem": "Máquina até 40°C",
    }
    return {"name": name, "price": price, "category": cats, "attributes": attrs, "description": desc}


# ------------------------------------------------------------------ #
# Alimentos
# ------------------------------------------------------------------ #
_al_subcats = {
    "Cereais Matinais": {
        "marcas": ["Kellogg's", "Nestlé", "Quaker", "Mãe Terra", "Granola Foods"],
        "produtos": ["Granola com Mel e Castanhas", "Flocos de Milho", "Aveia em Flocos", "Muesli Integral", "Flocos de Arroz"],
        "pesos": ["200g", "300g", "500g", "1kg"],
        "preco": (8.90, 39.90),
        "attrs_extra": {"integral": True, "fonte_de_fibras": True},
    },
    "Biscoitos": {
        "marcas": ["Bauducco", "Nestlé", "Oreo", "Piraquê", "Marilan"],
        "produtos": ["Biscoito Recheado Chocolate", "Biscoito Cream Cracker", "Wafer Baunilha", "Cookies Integral", "Rosquinha de Coco"],
        "pesos": ["100g", "130g", "200g", "350g", "400g"],
        "preco": (3.90, 18.90),
        "attrs_extra": {},
    },
    "Café e Chá": {
        "marcas": ["Nescafé", "Pilão", "3 Corações", "Melitta", "Leão"],
        "produtos": ["Café Torrado Moído", "Café Solúvel", "Café em Cápsulas", "Chá Verde", "Chá de Camomila"],
        "pesos": ["100g", "250g", "500g", "10 cápsulas", "20 saquinhos"],
        "preco": (9.90, 59.90),
        "attrs_extra": {"intensidade": None},
    },
    "Arroz e Feijão": {
        "marcas": ["Camil", "Tio João", "Kicaldo", "Urbano", "Namorado"],
        "produtos": ["Arroz Branco Tipo 1", "Arroz Integral", "Feijão Carioca", "Feijão Preto", "Arroz Parboilizado"],
        "pesos": ["1kg", "2kg", "5kg"],
        "preco": (5.90, 34.90),
        "attrs_extra": {"tipo": None},
    },
    "Massas": {
        "marcas": ["Barilla", "Renata", "Nissin", "La Molisana", "Adria"],
        "produtos": ["Espaguete", "Penne", "Fusilli", "Lasanha", "Farfalle", "Macarrão Parafuso"],
        "pesos": ["500g", "1kg"],
        "preco": (4.90, 19.90),
        "attrs_extra": {"cozimento": "8 minutos", "ovos": None},
    },
    "Bebidas": {
        "marcas": ["Coca-Cola", "PepsiCo", "Del Valle", "Natural One", "Suco Bom"],
        "produtos": ["Refrigerante Cola", "Suco de Laranja Integral", "Água de Coco", "Isotônico", "Chá Gelado Pêssego"],
        "pesos": ["350ml", "600ml", "1L", "1.5L", "2L"],
        "preco": (3.90, 18.90),
        "attrs_extra": {"acucar_reduzido": None},
    },
    "Chocolates e Doces": {
        "marcas": ["Nestlé", "Lacta", "Ferrero", "Lindt", "Hershey's"],
        "produtos": ["Chocolate ao Leite", "Chocolate Amargo 70%", "Bombom Sortido", "Trufa de Chocolate", "Chocolate Branco"],
        "pesos": ["80g", "100g", "200g", "250g", "400g"],
        "preco": (6.90, 49.90),
        "attrs_extra": {"cacau_percentual": None, "vegano": None},
    },
    "Snacks e Petiscos": {
        "marcas": ["Elma Chips", "Ruffles", "Pringles", "Forno de Minas", "Tostitos"],
        "produtos": ["Batata Chips Ondulada", "Amendoim Japonês", "Pipoca de Microondas", "Palito de Queijo", "Tortilha Chips"],
        "pesos": ["50g", "80g", "100g", "150g", "200g"],
        "preco": (4.90, 22.90),
        "attrs_extra": {},
    },
}

_al_desc_templates = {
    "Cereais Matinais": (
        "{produto} {marca}, embalagem de {peso}. "
        "Cereal {flags}rico em fibras e carboidratos complexos para energia prolongada. "
        "Fonte de vitaminas e minerais, ideal no café da manhã com leite ou iogurte. "
        "Textura crocante, sabor adocicado, fornece saciedade e disposição para o dia."
    ),
    "Biscoitos": (
        "{produto} {marca}, embalagem de {peso}. "
        "Biscoito {flags}crocante, sabor marcante, ótimo para lanches rápidos. "
        "Textura levinha que derrete na boca, combina com café, chá ou sozinho. "
        "Praticidade para o lanche da tarde, merenda escolar ou snack entre refeições."
    ),
    "Café e Chá": (
        "{produto} {marca}, embalagem de {peso}. "
        "{especifico} "
        "Produto {flags}para quem busca sabor e qualidade na xícara. "
        "Armazenar em local seco e fresco, longe da umidade."
    ),
    "Arroz e Feijão": (
        "{produto} {marca}, embalagem de {peso}. "
        "Grão {flags}selecionado, cozimento uniforme e sabor neutro que combina com qualquer prato. "
        "Base da alimentação brasileira, fonte de carboidratos, proteínas vegetais e fibras. "
        "Rendimento superior, grãos soltos após o cozimento."
    ),
    "Massas": (
        "{produto} {marca}, embalagem de {peso}. "
        "Massa {flags}de trigo selecionado, textura firme al dente após cozimento em torno de 8 minutos. "
        "Versátil para molhos vermelhos, brancos, pesto e receitas ao forno. "
        "Fonte de carboidratos, praticidade e rendimento para refeições completas da família."
    ),
    "Bebidas": (
        "{produto} {marca}, embalagem de {peso}. "
        "{especifico} "
        "Bebida {flags}gelada ou na temperatura ambiente, para hidratação e prazer no dia a dia."
    ),
    "Chocolates e Doces": (
        "{produto} {marca}, embalagem de {peso}. "
        "Chocolate {flags}com sabor intenso e textura cremosa que derrete na boca. "
        "Rico em cacau, fonte de antioxidantes flavonoides e feniletilamina que melhora o humor. "
        "Perfeito para presentear, sobremesas, fondue ou consumo puro como indulgência."
    ),
    "Snacks e Petiscos": (
        "{produto} {marca}, embalagem de {peso}. "
        "Snack {flags}crocante e saboroso para beliscar entre refeições ou em momentos de lazer. "
        "Textura irresistível, tempero característico, difícil de parar de comer. "
        "Ideal para festas, cinema, happy hour ou lanche rápido."
    ),
}

_al_cafe_cha_especifico = {
    "Café Torrado Moído":  "Café torrado e moído com aroma intenso, teor de cafeína elevado para disposição e foco. Sabor encorpado com notas de amêndoa e caramelo, acidez equilibrada.",
    "Café Solúvel":        "Café solúvel de dissolução instantânea, praticidade para preparar sem coador. Cafeína para energia imediata, aroma característico de café fresco.",
    "Café em Cápsulas":    "Café em cápsulas compatíveis com máquinas espresso, extração pressurizada que preserva os óleos aromáticos. Crema densa, cafeína concentrada e sabor intenso.",
    "Chá Verde":           "Chá verde rico em antioxidantes catequinas e EGCG, auxilia no emagrecimento e acelera o metabolismo. Cafeína suave para energia sem ansiedade, propriedades anti-inflamatórias e termogênicas. Sabor levemente herbáceo e adstringente.",
    "Chá de Camomila":     "Chá de camomila com propriedades calmantes e ansiolíticas, auxilia no sono e no relaxamento. Sem cafeína, indicado para à noite ou em momentos de estresse. Sabor suave e floral, anti-inflamatório natural.",
}

_al_bebida_especifico = {
    "Refrigerante Cola":          "Bebida gaseificada com sabor adocicado de cola, cafeína para energia e frescor. Gás intenso e sabor característico que agrada adultos e crianças.",
    "Suco de Laranja Integral":   "Suco de laranja integral 100% fruta, rico em vitamina C, antioxidantes e flavonoides. Sem adição de açúcar, conservantes ou corantes artificiais. Acidez natural e sabor cítrico refrescante.",
    "Água de Coco":               "Água de coco natural rica em eletrólitos — potássio, sódio e magnésio — para reidratação pós-exercício. Baixa caloria, refrescante, sabor suave e levemente adocicado.",
    "Isotônico":                  "Bebida isotônica com sais minerais e eletrólitos para repor o que se perde no suor durante exercícios. Hidratação esportiva, energia rápida, reduz cãibras e fadiga muscular.",
    "Chá Gelado Pêssego":         "Chá gelado sabor pêssego, refrescante e levemente adocicado. Combinação de chá com fruta, opção menos calórica que refrigerante, servido bem gelado.",
}


def _gen_alimento(idx: int) -> dict:
    r = _seeded(idx)
    subcat_name = r.choice(list(_al_subcats.keys()))
    sub         = _al_subcats[subcat_name]
    marca       = r.choice(sub["marcas"])
    produto     = r.choice(sub["produtos"])
    peso        = r.choice(sub["pesos"])
    price       = round(r.uniform(*sub["preco"]), 2)
    vegano      = r.choice([True, False])
    sem_gluten  = r.choice([True, False])
    organico    = r.choice([True, False, False, False])

    name = f"{produto} {marca} {peso}"
    cats = [
        f"Alimentos > {subcat_name}",
        f"Alimentos > {marca}",
    ]
    if organico:
        cats.append("Alimentos > Orgânicos e Naturais")
    if vegano:
        cats.append("Alimentos > Vegano")

    flags_parts = []
    if organico:   flags_parts.append("orgânico")
    if vegano:     flags_parts.append("vegano")
    if sem_gluten: flags_parts.append("sem glúten")
    flags_str = ", ".join(flags_parts) + " — " if flags_parts else ""

    template = _al_desc_templates.get(subcat_name, "{produto} {marca}, embalagem de {peso}. Produto {flags}de qualidade para o dia a dia.")
    especifico = (
        _al_cafe_cha_especifico.get(produto, "Bebida quente aromática com propriedades únicas para o bem-estar.")
        if subcat_name == "Café e Chá"
        else _al_bebida_especifico.get(produto, "Bebida refrescante para hidratação e prazer no dia a dia.")
    )
    desc = template.format(produto=produto, marca=marca, peso=peso, flags=flags_str, especifico=especifico)

    attrs = {
        "marca": marca, "subcategoria": subcat_name, "peso_volume": peso,
        "vegano": vegano, "sem_gluten": sem_gluten, "organico": organico,
        **{k: v for k, v in sub["attrs_extra"].items() if v is not None},
    }
    return {"name": name, "price": price, "category": cats, "attributes": attrs, "description": desc}


# ------------------------------------------------------------------ #
# TVs
# ------------------------------------------------------------------ #
_tv_marcas    = ["Samsung", "LG", "Sony", "Philips", "TCL", "Hisense"]
_tv_polegadas = ["32", "43", "50", "55", "65", "75", "85"]
_tv_resolucao = ["HD", "Full HD", "4K Ultra HD", "8K"]
_tv_tecnologia= ["LED", "OLED", "QLED", "NanoCell", "Mini LED", "AMOLED"]
_tv_sistema   = ["Android TV", "Tizen", "WebOS", "Google TV", "Roku TV"]
_tv_hdr       = ["HDR10", "Dolby Vision", "HDR10+", "HLG", "Sem HDR"]

def _gen_tv(idx: int) -> dict:
    r = _seeded(idx)
    marca     = r.choice(_tv_marcas)
    polegadas = r.choice(_tv_polegadas)
    resolucao = r.choice(_tv_resolucao)
    tecnologia= r.choice(_tv_tecnologia)
    sistema   = r.choice(_tv_sistema)
    hdr       = r.choice(_tv_hdr)
    hdmi      = r.choice([2, 3, 4])
    price     = round(r.uniform(999.90, 9999.90), 2)

    name = f"Smart TV {marca} {polegadas}\" {resolucao} {tecnologia}"
    cats = [
        f"Eletrônicos > TVs > {resolucao}",
        f"Eletrônicos > TVs > {tecnologia}",
        f"{marca} > TVs",
    ]
    desc = (
        f"Smart TV {marca} de {polegadas} polegadas com resolução {resolucao} e tecnologia de painel {tecnologia}. "
        f"Sistema operacional {sistema} com acesso a Netflix, Prime Video, YouTube e mais. "
        f"Suporte a {hdr} para imagens com maior contraste e cores vivas. "
        f"{hdmi} entradas HDMI e conectividade Wi-Fi e Bluetooth integrados. Voltagem Bivolt."
    )
    attrs = {
        "marca": marca, "polegadas": polegadas, "resolucao": resolucao,
        "tecnologia_painel": tecnologia, "sistema_operacional": sistema,
        "hdr": hdr, "portas_hdmi": hdmi, "smart_tv": True, "voltagem": "Bivolt",
        "wi_fi": True, "bluetooth": True,
    }
    return {"name": name, "price": price, "category": cats, "attributes": attrs, "description": desc}


# ------------------------------------------------------------------ #
# Smartphones
# ------------------------------------------------------------------ #
_sp_marcas  = ["Samsung", "Apple", "Motorola", "Xiaomi", "Realme", "TCL"]
_sp_modelos = {
    "Samsung":  ["Galaxy A14", "Galaxy A34", "Galaxy A54", "Galaxy S23", "Galaxy S24 Ultra"],
    "Apple":    ["iPhone 13", "iPhone 14", "iPhone 15", "iPhone 15 Pro", "iPhone 15 Pro Max"],
    "Motorola": ["Moto G34", "Moto G54", "Moto G84", "Edge 40", "Edge 40 Pro"],
    "Xiaomi":   ["Redmi 13C", "Redmi Note 13", "Xiaomi 13T", "POCO X6", "Redmi Note 13 Pro"],
    "Realme":   ["Realme C53", "Realme 11", "Narzo 60", "Realme GT 5"],
    "TCL":      ["TCL 40 SE", "TCL 40 XL", "TCL 50 XL"],
}
_sp_rams    = ["4GB", "6GB", "8GB", "12GB", "16GB"]
_sp_storages= ["64GB", "128GB", "256GB", "512GB"]
_sp_cameras = ["12MP", "48MP", "50MP", "64MP", "108MP", "200MP"]
_sp_baterias= ["3500mAh", "4000mAh", "5000mAh", "5500mAh", "6000mAh"]
_sp_telas   = ['5.0"', '6.1"', '6.4"', '6.67"', '6.8"', '7.0"']
_sp_cores   = ["Preto", "Branco", "Azul", "Verde", "Roxo", "Dourado", "Grafite", "Prata"]

def _gen_smartphone(idx: int) -> dict:
    r = _seeded(idx)
    marca     = r.choice(_sp_marcas)
    modelo    = r.choice(_sp_modelos[marca])
    ram       = r.choice(_sp_rams)
    storage   = r.choice(_sp_storages)
    camera    = r.choice(_sp_cameras)
    bateria   = r.choice(_sp_baterias)
    tela      = r.choice(_sp_telas)
    cor       = r.choice(_sp_cores)
    has_5g    = r.choice([True, False])
    price     = round(r.uniform(699.90, 7999.90), 2)

    name = f"Smartphone {marca} {modelo} {ram}/{storage} {cor}"
    cats = [
        "Eletrônicos > Smartphones",
        f"Eletrônicos > Smartphones > {marca}",
        f"{marca} > Smartphones",
    ]
    if has_5g:
        cats.append("Eletrônicos > Smartphones > 5G")

    desc = (
        f"Smartphone {marca} {modelo} com {ram} de RAM e {storage} de armazenamento interno. "
        f"Câmera principal de {camera} para fotos e vídeos com alta definição. "
        f"Bateria de {bateria} com carregamento rápido, tela de {tela}. "
        f"{'Conectividade 5G para velocidades ultrarrápidas. ' if has_5g else ''}"
        f"Disponível na cor {cor}."
    )
    attrs = {
        "marca": marca, "modelo": modelo, "ram": ram, "armazenamento": storage,
        "camera_principal": camera, "bateria": bateria, "tela": tela,
        "cor": cor, "5g": has_5g, "sistema": "Android" if marca != "Apple" else "iOS",
    }
    return {"name": name, "price": price, "category": cats, "attributes": attrs, "description": desc}


# ------------------------------------------------------------------ #
# Áudio
# ------------------------------------------------------------------ #
_au_marcas   = ["JBL", "Sony", "Bose", "Philips", "Multilaser", "Beats", "Edifier", "Anker"]
_au_tipos    = ["Fone In-Ear", "Fone Over-Ear", "Fone On-Ear", "Caixa de Som Portátil", "Soundbar", "Fone Gamer"]
_au_conect   = ["Bluetooth 5.0", "Bluetooth 5.3", "Com fio P2", "Com fio USB-C", "Bluetooth 5.0 + P2"]
_au_autonomia= ["6 horas", "10 horas", "12 horas", "20 horas", "30 horas", "40 horas"]
_au_ipx      = ["IPX4", "IPX5", "IPX7", "Sem resistência à água"]
_au_cores    = ["Preto", "Branco", "Azul", "Vermelho", "Verde", "Cinza"]

def _gen_audio(idx: int) -> dict:
    r = _seeded(idx)
    marca      = r.choice(_au_marcas)
    tipo       = r.choice(_au_tipos)
    conect     = r.choice(_au_conect)
    autonomia  = r.choice(_au_autonomia)
    ipx        = r.choice(_au_ipx)
    cor        = r.choice(_au_cores)
    anc        = r.choice([True, False])
    price      = round(r.uniform(49.90, 1999.90), 2)

    name = f"{tipo} {marca} {cor} {'ANC' if anc else ''} {conect.split()[0]}".strip()
    cats = [
        f"Eletrônicos > Áudio > {tipo}s",
        f"{marca} > Áudio",
    ]
    if anc:
        cats.append("Eletrônicos > Áudio > Cancelamento de Ruído")

    desc = (
        f"{tipo} {marca} com conectividade {conect}. "
        f"{'Cancelamento ativo de ruído (ANC) para isolamento sonoro superior. ' if anc else ''}"
        f"Autonomia de bateria de {autonomia} com uma única carga. "
        f"Resistência à água {ipx}. "
        f"Design confortável na cor {cor}, ideal para uso diário, academia e viagens."
    )
    attrs = {
        "marca": marca, "tipo": tipo, "conectividade": conect,
        "autonomia_bateria": autonomia, "resistencia_agua": ipx,
        "cancelamento_ruido_anc": anc, "cor": cor,
        "microfone_integrado": True,
    }
    return {"name": name, "price": price, "category": cats, "attributes": attrs, "description": desc}


# ------------------------------------------------------------------ #
# Casa & Cozinha
# ------------------------------------------------------------------ #
_cc_subcats = {
    "Panelas e Frigideiras": {
        "marcas":   ["Tramontina", "Brinox", "Cuisinart", "Panelux", "Rochedo"],
        "produtos": ["Jogo de Panelas 5 peças", "Frigideira Antiaderente", "Panela de Pressão", "Wok Antiaderente", "Caçarola Tampa de Vidro"],
        "materiais":["Alumínio com Antiaderente", "Aço Inox Triplo Fundo", "Cerâmica Antiaderente", "Titânio Reforçado"],
        "caps":     ["16cm", "20cm", "24cm", "26cm", "4,5L", "6L", "7L"],
        "preco":    (89.90, 699.90),
    },
    "Eletrodomésticos Pequenos": {
        "marcas":   ["Arno", "Mondial", "Philco", "Britânia", "Oster"],
        "produtos": ["Liquidificador", "Batedeira Planetária", "Cafeteira Elétrica", "Torradeira", "Sanduicheira Grill"],
        "materiais":["Plástico ABS + Aço Inox", "Plástico Resistente", "Aço Inox Escovado"],
        "caps":     ["1.5L", "2L", "12 xícaras", "750W", "1200W", "1500W"],
        "preco":    (99.90, 499.90),
    },
    "Organização e Armazenamento": {
        "marcas":   ["Ordene", "Coza", "Paramount", "Tramontina", "Hercules"],
        "produtos": ["Conjunto de Potes Herméticos", "Caixa Organizadora com Tampa", "Porta-Temperos Giratório", "Tábua de Corte Bambu", "Conjunto de Tigelas Inox"],
        "materiais":["Plástico BPA Free", "Bambu Natural", "Aço Inox 304", "Vidro Borossilicato"],
        "caps":     ["500ml", "1L", "2L", "5L", "10L", "30x20cm", "40x30cm"],
        "preco":    (29.90, 199.90),
    },
}

def _gen_casa_cozinha(idx: int) -> dict:
    r = _seeded(idx)
    subcat_name = r.choice(list(_cc_subcats.keys()))
    sub         = _cc_subcats[subcat_name]
    marca       = r.choice(sub["marcas"])
    produto     = r.choice(sub["produtos"])
    material    = r.choice(sub["materiais"])
    capacidade  = r.choice(sub["caps"])
    cor         = r.choice(["Preto", "Prata", "Branco", "Vermelho", "Grafite"])
    inducao     = r.choice([True, False])
    voltagem    = r.choice(["110v", "220v", "Bivolt"])
    price       = round(r.uniform(*sub["preco"]), 2)

    name = f"{produto} {marca} {material.split()[0]} {capacidade}"
    cats = [
        f"Casa e Cozinha > {subcat_name}",
        f"{marca} > Casa e Cozinha",
    ]
    if inducao:
        cats.append("Casa e Cozinha > Compatível com Indução")

    desc = (
        f"{produto} {marca} fabricado em {material}. "
        f"Capacidade de {capacidade}, cor {cor}. "
        f"{'Compatível com fogão de indução. ' if inducao else ''}"
        f"Resistente e fácil de limpar, ideal para cozinhas modernas. "
        f"Voltagem: {voltagem}."
    )
    attrs = {
        "marca": marca, "subcategoria": subcat_name, "produto": produto,
        "material": material, "capacidade": capacidade, "cor": cor,
        "compativel_inducao": inducao, "voltagem": voltagem,
    }
    return {"name": name, "price": price, "category": cats, "attributes": attrs, "description": desc}


# ------------------------------------------------------------------ #
# Dispatcher — distribui os 150 produtos pelas categorias
# ------------------------------------------------------------------ #
# idx % 10: 0,1,2 → roupa adulto | 3 → roupa infantil | 4,5 → alimento
#           6 → tv | 7 → smartphone | 8 → áudio | 9 → casa & cozinha

def _product_category(idx: int) -> str:
    bucket = idx % 10
    if bucket in (0, 1, 2): return "roupa_adulto"
    if bucket == 3:          return "roupa_infantil"
    if bucket in (4, 5):     return "alimento"
    if bucket == 6:          return "tv"
    if bucket == 7:          return "smartphone"
    if bucket == 8:          return "audio"
    return "casa_cozinha"


def generate_product(idx: int) -> dict:
    cat = _product_category(idx)
    generators = {
        "roupa_adulto":   _gen_roupa_adulto,
        "roupa_infantil": _gen_roupa_infantil,
        "alimento":       _gen_alimento,
        "tv":             _gen_tv,
        "smartphone":     _gen_smartphone,
        "audio":          _gen_audio,
        "casa_cozinha":   _gen_casa_cozinha,
    }
    data = generators[cat](idx)
    return {
        "external_id": f"SKU-{2000 + idx}",
        "name":        data["name"],
        "price":       data["price"],
        "description": data["description"],
        "image_url":   f"https://fake-cdn.com/images/produto_{2000 + idx}.jpg",
        "category":    json.dumps(data["category"], ensure_ascii=False),
        "attributes":  json.dumps(data["attributes"], ensure_ascii=False),
        "is_active":   True,
    }


# ================================================================== #
# GERAÇÃO DE CLIENTES — determinístico por seed do índice
# ================================================================== #

_first_names = ["João", "Maria", "Carlos", "Ana", "Pedro", "Lucia", "Roberto",
                "Sandra", "Marcos", "Patricia", "Felipe", "Fernanda", "Bruno", "Juliana"]
_last_names  = ["Silva", "Souza", "Oliveira", "Santos", "Costa", "Ferreira",
                "Rodrigues", "Almeida", "Nascimento", "Lima", "Pereira", "Carvalho"]
_city_suffix = ["Centro", "Norte", "Sul", "Leste", "Oeste", "Matriz", "Filial"]


def generate_customer(idx: int) -> dict:
    r = _seeded(idx + 90000)   # seed diferente da dos produtos
    first     = r.choice(_first_names)
    last      = r.choice(_last_names)
    ctype     = r.choice(CUSTOMER_TYPES)
    suffix    = r.choice(_city_suffix)
    doc_num   = r.randint(10_000_000, 99_999_999)
    crm_num   = r.randint(1000, 9999)

    # Data de cadastro entre 1 e 5 anos atrás
    days_ago  = r.randint(30, 365 * 5)
    src_date  = (datetime(2026, 3, 16) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "customer_id":     f"CLI-{10000 + idx}",
        "customer_add_id": f"CRM-{crm_num}",
        "name":            f"{ctype.capitalize()} {last} {suffix}",
        "document":        f"{doc_num:02d}.{r.randint(100,999)}.{r.randint(100,999)}/0001-{r.randint(10,99)}",
        "customer_type":   ctype,
        "source_created_at": src_date,
    }


# ================================================================== #
# GERAÇÃO DE PREÇOS — por produto × canal (e × loja quando multi)
# ================================================================== #

# Fator de preço por tipo de canal
_CHANNEL_PRICE_FACTOR = {
    "web":         1.00,
    "app":         0.97,   # 3% de desconto no app
    "loja_fisica": 1.02,   # ligeiramente mais caro na loja
    "televendas":  0.99,
}
# Variação adicional por loja (±%)
_STORE_VARIATION = {
    "LOJA-01": 0.00,
    "LOJA-02": 0.01,
    "LOJA-03": -0.01,
    "LOJA-04": 0.02,
    "LOJA-05": -0.02,
}


def generate_prices(products: list[dict], channels: list[dict]) -> list[dict]:
    rows = []
    for prod in products:
        base = prod["price"]
        for ch in channels:
            factor = _CHANNEL_PRICE_FACTOR.get(ch["type"], 1.0)
            for store_id in ch["stores"]:
                store_var = _STORE_VARIATION.get(store_id, 0.0)
                rows.append({
                    "product_external_id": prod["external_id"],
                    "channel_id": ch["channel_id"],
                    "store_id": store_id,
                    "price": round(base * factor * (1 + store_var), 2),
                })
    return rows


# ================================================================== #
# GERAÇÃO DE ESTOQUE
# ================================================================== #

def generate_stock(products: list[dict], channels: list[dict]) -> list[dict]:
    rows = []
    for prod in products:
        r = _seeded(hash(prod["external_id"]) % 99999)
        for ch in channels:
            for store_id in ch["stores"]:
                qty = r.randint(0, 200)
                rows.append({
                    "product_external_id": prod["external_id"],
                    "channel_id": ch["channel_id"],
                    "store_id": store_id,
                    "quantity": qty,
                    "available": qty > 0,
                })
    return rows


# ================================================================== #
# STATE — carrega, mescla e salva
# ================================================================== #

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "channels":      {},   # channel_id → dict
        "stores":        {},   # store_id   → dict
        "channel_stores": {},  # "CH-X|LOJA-Y" → dict
        "products":      {},   # external_id → dict
        "customers":     {},   # customer_id → dict
        "prices":        {},   # "sku|ch|store" → dict
        "stock":         {},   # "sku|ch|store" → dict
        "meta": {"last_run": "", "total_products": 0, "total_customers": 0},
    }


def save_state(state: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def merge_master(state: dict):
    """Aplica master data de canais/lojas ao state (upsert)."""
    for ch in MASTER_CHANNELS:
        state["channels"][ch["channel_id"]] = {k: v for k, v in ch.items() if k != "stores"}

    store_set = set()
    for ch in MASTER_CHANNELS:
        for sid in ch["stores"]:
            key = f"{ch['channel_id']}|{sid}"
            state["channel_stores"][key] = {"channel_id": ch["channel_id"], "store_id": sid}
            store_set.add(sid)

    for s in MASTER_STORES:
        state["stores"][s["store_id"]] = s


def merge_products(state: dict):
    """Gera produtos até TOTAL_PRODUCTS. Produtos existentes não são alterados."""
    for idx in range(TOTAL_PRODUCTS):
        prod = generate_product(idx)
        eid = prod["external_id"]
        if eid not in state["products"]:
            state["products"][eid] = prod
            print(f"  + produto novo: {eid} — {prod['name']}")


def merge_customers(state: dict):
    """Gera clientes até TOTAL_CUSTOMERS. Clientes existentes não são alterados."""
    for idx in range(TOTAL_CUSTOMERS):
        cust = generate_customer(idx)
        cid = cust["customer_id"]
        if cid not in state["customers"]:
            state["customers"][cid] = cust
            print(f"  + cliente novo: {cid} — {cust['name']}")


def merge_prices(state: dict):
    """Recalcula preços para todos os produtos × canais × lojas."""
    state["prices"] = {}
    products = list(state["products"].values())
    for p in generate_prices(products, MASTER_CHANNELS):
        key = f"{p['product_external_id']}|{p['channel_id']}|{p['store_id']}"
        state["prices"][key] = p


def merge_stock(state: dict):
    """Recalcula estoque para todos os produtos × canais × lojas."""
    state["stock"] = {}
    products = list(state["products"].values())
    for s in generate_stock(products, MASTER_CHANNELS):
        key = f"{s['product_external_id']}|{s['channel_id']}|{s['store_id']}"
        state["stock"][key] = s


# ================================================================== #
# OFERTAS — geradas dinamicamente a cada run (full replace)
# ================================================================== #

def _write_orders_csv(state: dict):
    """
    Gera orders.csv com histórico de 24 meses adequado para BG/NBD.

    Cada cliente recebe um "perfil de compra" com:
    - lambda: taxa de compra (compras/mês)
    - p_death: probabilidade de churn após cada compra

    Compras são geradas sequencialmente com intervalos exponenciais,
    o que replica o processo Pareto/NBD que o BG/NBD modela.

    Perfis (distribuição entre os clientes):
    - LoyalStar   (15%): lambda alto, churn baixíssimo
    - LoyalRunner (20%): lambda médio-alto, churn baixo
    - Regular     (25%): lambda médio, churn moderado
    - Occasional  (25%): lambda baixo, churn moderado-alto
    - OneTime     (15%): lambda baixo, churn muito alto (quase sempre param após 1-2 compras)
    """
    import math

    customers = list(state["customers"].values())
    products  = list(state["products"].values())
    channels  = list(state["channels"].values())
    if not customers or not products:
        return

    ch_stores_map: dict = {}
    for cs in state["channel_stores"].values():
        ch_stores_map.setdefault(cs["channel_id"], []).append(cs["store_id"])

    rng = random.Random(42)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    history_start = today - timedelta(days=730)  # 24 meses de histórico

    rows = []
    order_seq = 1

    # Perfis de compra para BG/NBD
    # (lambda_min, lambda_max, p_death_min, p_death_max, promo_rate)
    profiles = [
        # (nome, peso, lambda_min, lambda_max, p_death_min, p_death_max, promo_rate)
        ("LoyalStar",   0.15, 2.5, 5.0,  0.01, 0.03, 0.10),
        ("LoyalRunner", 0.20, 1.0, 2.5,  0.03, 0.08, 0.12),
        ("Regular",     0.25, 0.4, 1.0,  0.08, 0.18, 0.15),
        ("Occasional",  0.25, 0.1, 0.4,  0.18, 0.40, 0.20),
        ("OneTime",     0.15, 0.1, 0.3,  0.60, 0.95, 0.25),
    ]

    # Sorteia perfil para cada cliente de forma determinística
    def pick_profile(idx: int):
        thresholds = []
        acc = 0
        for p in profiles:
            acc += p[1]
            thresholds.append(acc)
        r_val = rng.random()
        for i, t in enumerate(thresholds):
            if r_val <= t:
                return profiles[i]
        return profiles[-1]

    for i, cust in enumerate(customers):
        profile = pick_profile(i)
        _, _, lam_min, lam_max, p_death_min, p_death_max, promo_rate = profile

        # Parâmetros individuais do cliente
        lam = rng.uniform(lam_min, lam_max)         # compras/mês
        p_death = rng.uniform(p_death_min, p_death_max)

        # Canal preferido do cliente (fixo)
        preferred_ch = rng.choice(channels)
        channel_id = preferred_ch["channel_id"]
        store_options = ch_stores_map.get(channel_id, [])
        store_id = rng.choice(store_options) if store_options else ""

        # Gera compras sequencialmente via processo de Poisson truncado
        # Intervalo entre compras ~ Exponential(1/lambda) em dias
        avg_days_between = 30.0 / lam  # converte meses para dias
        current_date = history_start + timedelta(days=rng.randint(0, 30))

        while current_date <= today:
            # Intervalo até próxima compra
            interval_days = rng.expovariate(1.0 / avg_days_between)
            current_date += timedelta(days=interval_days)

            if current_date > today:
                break

            order_id = f"PED-{order_seq:05d}"
            order_seq += 1
            ordered_at = current_date.strftime("%Y-%m-%dT%H:%M:%S")

            # Ocasionalmente muda de canal
            if rng.random() < 0.15:
                ch = rng.choice(channels)
                ch_id = ch["channel_id"]
                st_opts = ch_stores_map.get(ch_id, [])
                ch_order = ch_id
                st_order = rng.choice(st_opts) if st_opts else ""
            else:
                ch_order = channel_id
                st_order = store_id

            status = rng.choices(
                ["delivered", "confirmed", "cancelled", "returned"],
                weights=[75, 15, 7, 3]
            )[0]

            n_items = rng.randint(1, 4)
            order_products = rng.sample(products, min(n_items, len(products)))

            gross_total = 0.0
            discount_total = 0.0
            tax_total = 0.0
            item_rows = []

            for prod in order_products:
                qty = rng.randint(1, 3)
                unit_price = round(float(prod["price"]), 2)
                is_promo = rng.random() < promo_rate
                discount_amount = round(unit_price * rng.uniform(0.05, 0.25), 2) if is_promo else 0.0
                tax_pct = rng.uniform(0.05, 0.12)
                tax_amount = round((unit_price - discount_amount) * tax_pct, 2)
                net_price = round(unit_price - discount_amount + tax_amount, 2)

                gross_total    += unit_price * qty
                discount_total += discount_amount * qty
                tax_total      += tax_amount * qty

                item_rows.append({
                    "order_id":            order_id,
                    "customer_ref":        cust["customer_id"],
                    "channel_id":          ch_order,
                    "store_id":            st_order,
                    "status":              status,
                    "ordered_at":          ordered_at,
                    "gross_value":         round(gross_total, 2),
                    "discount_value":      round(discount_total, 2),
                    "tax_value":           round(tax_total, 2),
                    "net_value":           round(gross_total - discount_total + tax_total, 2),
                    "product_external_id": prod["external_id"],
                    "quantity":            qty,
                    "unit_price":          unit_price,
                    "discount_amount":     discount_amount,
                    "tax_amount":          tax_amount,
                    "net_price":           net_price,
                    "is_promo":            is_promo,
                })

            rows.extend(item_rows)

            # Churn após esta compra?
            if rng.random() < p_death:
                break

    pd.DataFrame(rows).to_csv(f"{OUTPUT_DIR}/orders.csv", index=False)
    n_orders = len({r["order_id"] for r in rows})

    # Estatísticas úteis para validar a distribuição
    from collections import Counter
    orders_per_customer = Counter(r["customer_ref"] for r in rows)
    multi_buyers = sum(1 for v in orders_per_customer.values() if v > 1)
    print(f"  Pedidos:  {n_orders} pedidos | {len(rows)} linhas (itens)")
    print(f"  Clientes: {len(orders_per_customer)} com pedidos | {multi_buyers} com >1 pedido (BG/NBD)")
    print(f"  Média:    {n_orders / max(len(orders_per_customer), 1):.1f} pedidos/cliente")


def _write_offers_csv(state: dict):
    """
    Gera offers.csv com amostras de todos os tipos de promoção.
    Ofertas são full-replace — não precisam de state persistente.
    """
    today = datetime.now()
    start = today.strftime("%Y-%m-%dT00:00:00")
    end_30 = (today + timedelta(days=30)).strftime("%Y-%m-%dT23:59:59")
    end_7  = (today + timedelta(days=7)).strftime("%Y-%m-%dT23:59:59")

    # Pega até 20 SKUs do state para usar nas ofertas
    skus = [p["external_id"] for p in list(state["products"].values())[:20]]
    if not skus:
        return

    # Pega alguns customer_ids para oferta segmentada
    cust_ids = [c["customer_id"] for c in list(state["customers"].values())[:5]]
    cust_refs = "|".join(cust_ids) if cust_ids else ""

    rows = [
        # 1. Desconto direto — geral, todos os canais
        {
            "offer_id":        "PROMO-DESC-20",
            "name":            "20% OFF seleção",
            "type":            "DIRECT_DISCOUNT",
            "mechanic_params": json.dumps({"discount_type": "percent", "discount_value": 20}),
            "trigger_products": "|".join(skus[:5]),
            "reward_products":  "",
            "start_at":        start,
            "end_at":          end_30,
            "channel_ids":     "",
            "store_ids":       "",
            "audience_type":   "ALL",
            "audience_value":  "",
            "priority":        1,
        },
        # 2. Leve 3 pague 2 — só no canal físico e app
        {
            "offer_id":        "PROMO-3X2",
            "name":            "Leve 3 Pague 2",
            "type":            "TAKE_X_PAY_Y",
            "mechanic_params": json.dumps({"take": 3, "pay": 2}),
            "trigger_products": "|".join(skus[5:9]),
            "reward_products":  "",
            "start_at":        start,
            "end_at":          end_7,
            "channel_ids":     "CH-FISICO|CH-APP",
            "store_ids":       "",
            "audience_type":   "ALL",
            "audience_value":  "",
            "priority":        2,
        },
        # 3. Compre X ganhe Y — produto trigger + reward diferente
        {
            "offer_id":        "PROMO-BUY1GET1",
            "name":            "Compre 1 Ganhe Brinde",
            "type":            "BUY_X_GET_Y",
            "mechanic_params": json.dumps({"trigger_quantity": 1, "reward_quantity": 1, "reward_discount_percent": 100}),
            "trigger_products": skus[9] if len(skus) > 9 else skus[0],
            "reward_products":  skus[10] if len(skus) > 10 else skus[1],
            "start_at":        start,
            "end_at":          end_30,
            "channel_ids":     "CH-WEB",
            "store_ids":       "",
            "audience_type":   "ALL",
            "audience_value":  "",
            "priority":        3,
        },
        # 4. Desconto progressivo
        {
            "offer_id":        "PROMO-PROGRESSIVO",
            "name":            "Desconto Progressivo por Quantidade",
            "type":            "PROGRESSIVE",
            "mechanic_params": json.dumps({"tiers": [
                {"min_qty": 2,  "discount_percent": 10},
                {"min_qty": 5,  "discount_percent": 15},
                {"min_qty": 10, "discount_percent": 20},
            ]}),
            "trigger_products": "|".join(skus[11:14]) if len(skus) > 13 else skus[0],
            "reward_products":  "",
            "start_at":        start,
            "end_at":          end_30,
            "channel_ids":     "",
            "store_ids":       "",
            "audience_type":   "ALL",
            "audience_value":  "",
            "priority":        1,
        },
        # 5. Combo — segmentado para clientes VIP
        {
            "offer_id":        "PROMO-COMBO-VIP",
            "name":            "Kit Especial Clientes VIP",
            "type":            "COMBO",
            "mechanic_params": json.dumps({"combo_discount_percent": 25}),
            "trigger_products": "|".join(skus[14:17]) if len(skus) > 16 else skus[0],
            "reward_products":  "",
            "start_at":        start,
            "end_at":          end_30,
            "channel_ids":     "",
            "store_ids":       "",
            "audience_type":   "CUSTOMER_IDS" if cust_refs else "ALL",
            "audience_value":  cust_refs,
            "priority":        5,
        },
        # 6. Cashback — geral
        {
            "offer_id":        "PROMO-CASHBACK-5",
            "name":            "5% Cashback",
            "type":            "CASHBACK",
            "mechanic_params": json.dumps({"cashback_percent": 5, "credit_type": "wallet"}),
            "trigger_products": "|".join(skus[17:20]) if len(skus) > 19 else skus[0],
            "reward_products":  "",
            "start_at":        start,
            "end_at":          end_30,
            "channel_ids":     "CH-WEB|CH-APP",
            "store_ids":       "",
            "audience_type":   "ALL",
            "audience_value":  "",
            "priority":        1,
        },
    ]

    pd.DataFrame(rows).to_csv(f"{OUTPUT_DIR}/offers.csv", index=False)
    print(f"  Ofertas:  {len(rows)} (6 tipos de promoção)")


# ================================================================== #
# ESCRITA DOS CSVs
# ================================================================== #

def write_csvs(state: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # channels.csv — stores como JSON array [{store_id, name}] para o frontend parsear
    ch_rows = []
    for ch in state["channels"].values():
        stores_for_ch = [
            {"store_id": v["store_id"], "name": state["stores"].get(v["store_id"], {}).get("name", v["store_id"])}
            for v in state["channel_stores"].values()
            if v["channel_id"] == ch["channel_id"]
        ]
        ch_rows.append({**ch, "stores": json.dumps(stores_for_ch, ensure_ascii=False)})
    pd.DataFrame(ch_rows).to_csv(f"{OUTPUT_DIR}/channels.csv", index=False)

    # stores.csv
    pd.DataFrame(list(state["stores"].values())).to_csv(f"{OUTPUT_DIR}/stores.csv", index=False)

    # channel_stores.csv
    pd.DataFrame(list(state["channel_stores"].values())).to_csv(
        f"{OUTPUT_DIR}/channel_stores.csv", index=False
    )

    # products.csv — price como float (desserializa do state que guarda como string JSON às vezes)
    prods = []
    for p in state["products"].values():
        prods.append({
            "external_id": p["external_id"],
            "name":        p["name"],
            "price":       p["price"],
            "description": p["description"],
            "image_url":   p["image_url"],
            "category":    p["category"],
            "attributes":  p["attributes"],
            "is_active":   p["is_active"],
        })
    pd.DataFrame(prods).to_csv(f"{OUTPUT_DIR}/products.csv", index=False)

    # customers.csv
    pd.DataFrame(list(state["customers"].values())).to_csv(
        f"{OUTPUT_DIR}/customers.csv", index=False
    )

    # prices.csv
    prices = list(state["prices"].values())
    pd.DataFrame(prices).to_csv(f"{OUTPUT_DIR}/prices.csv", index=False)

    # stock.csv
    stock = list(state["stock"].values())
    pd.DataFrame(stock).to_csv(f"{OUTPUT_DIR}/stock.csv", index=False)

    # offers.csv — gerado dinamicamente (full replace), não persiste no state
    _write_offers_csv(state)


# ================================================================== #
# MAIN
# ================================================================== #

if __name__ == "__main__":
    print("=" * 60)
    print("Gerando dados de teste...")
    print("=" * 60)

    state = load_state()

    prev_prods = len(state["products"])
    prev_custs = len(state["customers"])

    print("\n[1/6] Mesclando canais e lojas...")
    merge_master(state)

    print(f"\n[2/6] Gerando produtos (alvo: {TOTAL_PRODUCTS})...")
    merge_products(state)

    print(f"\n[3/6] Gerando clientes (alvo: {TOTAL_CUSTOMERS})...")
    merge_customers(state)

    print("\n[4/6] Atualizando preços...")
    merge_prices(state)

    print("\n[5/6] Atualizando estoque...")
    merge_stock(state)

    print("\n[6/7] Gerando pedidos de teste...")
    _write_orders_csv(state)

    print("\n[7/7] Gerando ofertas de teste...")

    state["meta"]["last_run"]        = datetime.now().isoformat()
    state["meta"]["total_products"]  = len(state["products"])
    state["meta"]["total_customers"] = len(state["customers"])

    save_state(state)
    write_csvs(state)

    new_prods = len(state["products"]) - prev_prods
    new_custs = len(state["customers"]) - prev_custs

    print("\n" + "=" * 60)
    print("Concluído!")
    print(f"  Canais:   {len(state['channels'])}")
    print(f"  Lojas:    {len(state['stores'])}")
    print(f"  Produtos: {len(state['products'])} ({'+' + str(new_prods) if new_prods else 'sem novos'})")
    print(f"  Clientes: {len(state['customers'])} ({'+' + str(new_custs) if new_custs else 'sem novos'})")
    print(f"  Preços:   {len(state['prices'])}")
    print(f"  Estoque:  {len(state['stock'])}")
    print(f"\nArquivos salvos em: {OUTPUT_DIR}/")
    print("=" * 60)
