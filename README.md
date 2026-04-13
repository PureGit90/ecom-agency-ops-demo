# eCom Agency AI Operations Dashboard — Working Demo

## What This Does

An AI-powered operations dashboard for e-commerce agencies. Incoming orders are auto-triaged by Claude (priority classification + next action assignment), and client requests get AI-drafted responses ready for one-click approval. Low-priority routine orders are auto-handled without manual intervention.

## How It Works

Order/Request received → Claude Haiku triage → Priority assigned → Auto-handle OR queue for review → AI-draft response → Ops approves → Sent + logged

## Quick Start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run app.py
```

Then open http://localhost:8501

## Features

- **Order Queue** — 5 mock orders (bulk restock, rush, returns, delayed shipment). Click "Triage All with AI" to see Claude classify each by priority and assign next actions
- **Client Requests** — 4 linked client messages. "Draft All Responses" generates context-aware replies in seconds
- **Automation Log** — Every AI action logged with timestamp, type, and outcome
- **Metrics** — Live counters for pipeline value, auto-handled %, open requests

## Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required for AI triage and response drafting |

For Streamlit Cloud: add `ANTHROPIC_API_KEY` under Settings → Secrets as:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

## Demo Limitations

This is an MVP demonstration — it uses embedded mock data. A production version would add:
- Shopify/WooCommerce webhook integration for live order ingestion
- Notion/Airtable sync for persistent CRM records
- Gmail/Outlook API for direct email dispatch
- Slack escalation for High-priority orders
- Scheduled daily ops summary reports
