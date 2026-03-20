export const TEXTS = {
  APP: {
    NAME: "Recommender.ai",
    TENANT_PREFIX: "Tenant:",
  },

  LOGIN: {
    TITLE: "Bem-vindo de volta",
    SUBTITLE: "Entre com suas credenciais para acessar o painel",
    LABEL_EMAIL: "E-mail Corporativo",
    LABEL_PASSWORD: "Senha",
    PLACEHOLDER_EMAIL: "admin@empresa.com",
    BTN_SUBMIT: "Acessar Plataforma",
    BTN_LOADING: "Autenticando...",
    ERROR_GENERIC: "Falha na autenticação. Verifique suas credenciais.",
    FORGOT_PASSWORD: "Esqueceu a senha?",
  },

  SIDEBAR: {
    SECTION_MAIN: "Principal",
    SECTION_SIMULATOR: "Simulador & IA",
    DASHBOARD: "Dashboard",
    CARGAS: "Cargas",
    CATALOG: "Catálogo",
    CONFIG: "Configurações",
    LOGOUT: "Sair do Sistema",
  },

  CARGAS: {
    TITLE: "Cargas de Dados",
    SUBTITLE: "Importe seus dados via CSV para cada entidade do sistema.",
    DROP_HINT: "Clique ou arraste o arquivo CSV aqui",
    BTN_PROCESS: "Processar CSV",
    PROCESSING: "Processando...",
    ERROR_MSG: "Erro ao processar o arquivo. Verifique o formato.",
    SEND_ANOTHER: "Enviar outro arquivo",
    CREATED: "criados",
    UPDATED: "atualizados",
    UNCHANGED: "sem alteração",
    ERRORS: "erros",
    CHANNELS: "Canais",
    CHANNELS_DESC: "Canais de venda (web, app, loja física) com suas lojas vinculadas.",
    STORES: "Lojas",
    STORES_DESC: "Lojas individuais por canal de venda.",
    PRODUCTS: "Produtos",
    PRODUCTS_DESC: "Catálogo de produtos com enriquecimento automático por IA.",
    CUSTOMERS: "Clientes",
    CUSTOMERS_DESC: "Base de clientes importada do ERP ou CRM.",
    PRICES: "Preços",
    PRICES_DESC: "Preços operacionais por produto, canal e loja.",
    STOCK: "Estoque",
    STOCK_DESC: "Disponibilidade de estoque por canal e loja.",
    ORDERS: "Pedidos",
    ORDERS_DESC: "Histórico de pedidos do ERP. Formato desnormalizado: uma linha por item.",
    OFFERS: "Ofertas",
    OFFERS_DESC: "Promoções por produto, canal e audiência. Upload substitui todas as ofertas ativas.",
  },
  HEADER: {
    TITLE: "Painel Administrativo",
  },

  UPLOAD: {
    TITLE: "Importar Catálogo de Produtos",
    SUBTITLE: "Envie seu arquivo CSV/JSON para alimentar a Inteligência Artificial.",
    DRAG_DROP_TITLE: "Clique ou arraste seu arquivo CSV/JSON aqui",
    DRAG_DROP_SUBTITLE: "Suportamos arquivos de até 10MB (Formato: ID, Nome, Descrição, Preço, Categoria)",
    BTN_SELECT: "Selecionar Arquivo",
    FILE: "Arquivo CSV/JSON",
    TXT_FILE: "Selecionar arquivo do seu computador.",
    BTN_UPLOAD: "Iniciar Processamento",
    BTN_CANCEL: "Cancelar",
    SUCCESS_TITLE: "Processamento Concluído!",
    SUCCESS_MSG: "produtos foram indexados com sucesso no banco vetorial.",
    ERROR_TITLE: "Falha no Upload",
    ERROR_MSG: "Ocorreu um erro ao enviar o arquivo. Verifique o formato.",
    PROCESSING: "Processando e gerando Embeddings...",
  },

  CATALOG: {
    TITLE: "Catálogo & Inteligência Vetorial", // Ajustado
    SUBTITLE: "Explore a similaridade semântica entre os produtos do seu inventário.",
    SEARCH_PLACEHOLDER: "Buscar produto por nome...",
    EMPTY_STATE: "Nenhum produto encontrado. Faça o upload de um CSV primeiro.",
    
    // Novos textos da Gaveta
    DRAWER_TITLE: "Análise de Similaridade",
    DRAWER_SUBTITLE: "Produtos semanticamente parecidos encontrados no Banco Vetorial:",
    
    // Grupos de Preço
    GROUP_CHEAPER: "📉 Mais Baratos (Down-sell)",
    GROUP_SAME: "⚖️ Mesma Faixa de Preço (Substitutos)",
    GROUP_EXPENSIVE: "📈 Mais Caros (Up-sell)",
    
    SCORE_LABEL: "Similaridade de Conteúdo", // Mais preciso
    PRICE_PREFIX: "R$ ",
    BTN_DETAILS: "Analisar",
  },

  COMMON: {
    LOADING: "Carregando...",
    SUCCESS: "Sucesso",
    ERROR: "Erro",
    COPYRIGHT: "© 2024 Recommender.ai Inc. Todos os direitos reservados.",
    BTN_UPDATE: "Atualizar"
  },

  DASHBOARD: {
    TITLE: "Dashboard Analítico",
    SUBTITLE: "Monitoramento em tempo real da infraestrutura de recomendação.",

    CARD_PRODUCTS: "Produtos",
    CARD_PRODUCTS_SUB: "Itens no catálogo",
    CARD_CATEGORIES: "Categorias",
    CARD_CATEGORIES_SUB: "Nós de navegação",
    CARD_CHANNELS: "Canais",
    CARD_CHANNELS_SUB: "Canais de venda ativos",
    CARD_STORES: "Lojas",
    CARD_STORES_SUB: "Lojas cadastradas",
    CARD_CUSTOMERS: "Clientes",
    CARD_CUSTOMERS_SUB: "Base de clientes",
    CARD_PRICES: "Preços",
    CARD_PRICES_SUB: "Entradas canal × loja",
    CARD_STOCK: "Estoques",
    CARD_STOCK_SUB: "Entradas canal × loja",
    CARD_ORDERS: "Pedidos",
    CARD_ORDERS_SUB_FN: (items: number) => `${items.toLocaleString()} itens`,
    CARD_OFFERS: "Ofertas",
    CARD_OFFERS_SUB_FN: (active: number) => `${active} ativas agora`,
    CARD_VECTORS: "Vetores (Qdrant)",
    STATUS_SYNCED: "Sincronizado",
    STATUS_INDEXING: "Processando/Incompleto",
    CARD_TENANT: "Tenant Ativo",
    CARD_TENANT_SUB: "Ambiente de Produção",

    SECTION_CATALOG: "Catálogo",
    SECTION_OPERATIONS: "Operações",
    SECTION_AI: "Inteligência Artificial",
  },

  CATALOG_DETAIL: {
    PRICES_TITLE: "Preços por Canal e Loja",
    STOCK_TITLE: "Estoque por Canal e Loja",
    COL_CHANNEL: "Canal",
    COL_STORE: "Loja",
    COL_PRICE: "Preço",
    COL_QTY: "Qtd.",
    COL_AVAILABLE: "Disponível",
    AVAILABLE_YES: "Sim",
    AVAILABLE_NO: "Não",
    EMPTY_PRICES: "Nenhum preço cadastrado para este produto.",
    EMPTY_STOCK: "Nenhum estoque cadastrado para este produto.",
  }

};