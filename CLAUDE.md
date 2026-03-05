# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Munder Difflin Paper Company multi-agent system — a Udacity project to build a multi-agent AI system (max 5 agents) that automates inventory checks, quote generation, and order fulfillment for a fictional paper company. All I/O is text-based.

## Setup & Running

```bash
pip install -r requirements.txt
# Also install your chosen agent framework:
pip install smolagents   # or pydantic-ai or npcsh[lite]
```

Create a `.env` file with:
```
UDACITY_OPENAI_API_KEY=your_key_here
```
API endpoint: `https://openai.vocareum.com/v1` (OpenAI-compatible proxy).

Run the project:
```bash
python project_starter.py
```

## Architecture

**Single file**: `project_starter.py` contains everything — database setup, helper functions, agent definitions (to be implemented), and test harness.

**Database**: SQLite (`munder_difflin.db`) via SQLAlchemy. Tables:
- `inventory` — paper items with stock levels and unit prices (seeded at 40% of the full `paper_supplies` catalog)
- `transactions` — all stock orders and sales (cash balance computed from sum of sales minus stock orders)
- `quotes` — historical quote data (loaded from `quotes.csv`)
- `quote_requests` — customer inquiries (loaded from `quote_requests.csv`)

**Helper functions that MUST all be used** (per rubric): `create_transaction`, `get_all_inventory`, `get_stock_level`, `get_supplier_delivery_date`, `get_cash_balance`, `generate_financial_report`, `search_quote_history`.

**Data files**:
- `quotes.csv` / `quote_requests.csv` — historical data loaded into DB at init
- `quote_requests_sample.csv` — 20 test scenarios used for evaluation

## Agent System Design

Implementation goes in the `"YOUR MULTI AGENT STARTS HERE"` section (~line 586). Required agents:
1. **Orchestrator** — routes customer inquiries to worker agents
2. **Inventory agent** — checks stock, decides reorders
3. **Quoting agent** — generates quotes with bulk discounts, references historical quotes
4. **Sales/ordering agent** — finalizes transactions, updates DB

Agent tools should wrap the helper functions above according to the chosen framework's conventions.

## Key Business Logic

- Initial cash balance: $50,000 (seeded as a sales transaction)
- Inventory is partial (~17 of 42 items stocked); not all requests can be fulfilled
- Delivery lead times scale with quantity (0–7 days via `get_supplier_delivery_date`)
- Transaction types: `"stock_orders"` (buying from supplier) or `"sales"` (selling to customer)
- Item names must match DB exactly or transactions fail
- Dates must be included when passing data between agents

## Evaluation Criteria

From `run_test_scenarios()`, the system must produce `test_results.csv` showing:
- At least 3 requests that change the cash balance
- At least 3 successfully fulfilled quote requests
- Some requests NOT fulfilled (e.g., items not in inventory)
- Customer-facing outputs must include rationale but not expose internal data (margins, errors)
