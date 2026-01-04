# KeepAIS - Emarsys + GA4 SaaS

## Visao geral
Projeto SaaS que unifica dados do Emarsys e GA4 para gerar dashboards e insights de marketing.

## O que o projeto tem ate agora

### Backend (Node.js + TypeScript + Express)
- Rota de health check: `GET /health`
- Rotas de relatorios (mock):
  - `GET /api/reports/emarsys`
  - `GET /api/reports/ga4`
  - `GET /api/reports/combined`
- Mocks organizados em `backend/src/mocks`
- Estrutura preparada para integracoes futuras:
  - `backend/src/services/emarsysService.ts`
  - `backend/src/services/ga4Service.ts`

### Frontend (React + Vite + TypeScript)
- Landing page com secoes: Recursos, Modulos, Planos e Integracoes
- Animacoes de entrada na rolagem (stagger)
- Back-office com sidebar e rotas:
  - Overview
  - Campaigns
  - Abandoned Carts
  - Analytics
  - AI Advisor (chat UI)
  - Playbooks
- Dashboard principal com cards, grafico e paines
- Toggle de tema (dark/light) apenas no back-office

## Linguagens e tecnologias
- Linguagens: TypeScript, HTML, CSS
- Backend: Node.js (LTS), Express, dotenv, axios
- Frontend: React, Vite, React Router, React Query

## Como rodar localmente

### Instalar dependencias
```
npm install --prefix backend
npm install --prefix frontend
```

### Rodar backend e frontend
```
npx concurrently "npm --prefix backend run dev" "npm --prefix frontend run dev"
```

## Enderecos locais
- Frontend: http://localhost:5173/
- Dashboard: http://localhost:5173/dashboard
- Backend: http://localhost:3001/health

## Observacoes
- Os dados de Emarsys e GA4 estao mockados.
- O backend ja esta preparado para integrar APIs reais.
