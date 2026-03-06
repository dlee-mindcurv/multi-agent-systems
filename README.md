# Munder Difflin Multi-Agent System

A multi-agent AI system that automates inventory checks, quote generation, and order fulfillment for Munder Difflin Paper Company — a Udacity project built with [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Overview

This project implements a multi-agent system (up to 5 agents) to handle core business operations for a fictional paper manufacturing company. All I/O is text-based.

**Agents:**
- **Orchestrator** — routes customer inquiries to the appropriate worker agent
- **Inventory Agent** — checks stock levels, decides on reorders
- **Quoting Agent** — generates quotes with bulk discounts, references historical data
- **Sales/Ordering Agent** — finalizes transactions, updates the database

**Key capabilities:**
- Inventory checks and restocking decisions
- Quote generation for incoming sales inquiries
- Order fulfillment including supplier logistics and transactions

## Built with Claude Code

This project was developed using [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Anthropic’s CLI tool for agentic coding. Claude Code assisted with:

- Designing and implementing the multi-agent architecture
- Writing agent tool wrappers and business logic
- Debugging database interactions and transaction flows
- Iterating on prompt engineering for agent coordination
- Managing the project repository and CI workflow

The `CLAUDE.md` file in this repo provides project context that Claude Code uses to understand the codebase and maintain consistency across sessions.

## Tech Stack

- **Python 3.8+**
- **smolagents** — agent orchestration framework
- **SQLite** via SQLAlchemy — inventory, transactions, and quotes database
- **OpenAI-compatible LLM** — via Vocareum proxy endpoint

## Project Structure

```
├── project_starter.py          # Main script: DB setup, helpers, agents, test harness
├── quotes.csv                  # Historical quote data
├── quote_requests.csv          # Incoming customer requests
├── quote_requests_sample.csv   # 20 test scenarios for evaluation
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Claude Code project instructions
└── .env                        # API key (not committed)
```

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install smolagents
   ```

2. **Create a `.env` file** with your API key:

   ```
   UDACITY_OPENAI_API_KEY=your_key_here
   ```

   This project uses a custom OpenAI-compatible proxy at `https://openai.vocareum.com/v1`.

3. **Run the project:**

   ```bash
   python project_starter.py
   ```

## How It Works

The multi-agent system is defined in the `"YOUR MULTI AGENT STARTS HERE"` section of `project_starter.py`. When run:

1. `run_test_scenarios()` simulates a series of customer requests from `quote_requests_sample.csv`.
2. The orchestrator routes each request to the appropriate agent.
3. Agents coordinate inventory checks, generate quotes, and process orders.
4. Results are saved to `test_results.csv` along with a financial report.

**Database tables:**
- `inventory` — paper items with stock levels and unit prices (~17 of 42 items stocked)
- `transactions` — stock orders and sales (cash balance starts at $50,000)
- `quotes` / `quote_requests` — historical quote data

## Evaluation Criteria

The system must produce `test_results.csv` showing:
- At least 3 requests that change the cash balance
- At least 3 successfully fulfilled quote requests
- Some requests correctly not fulfilled (e.g., items not in inventory)
- Customer-facing outputs include rationale without exposing internal data

## License

This project was created as part of the [Udacity](https://www.udacity.com/) AI curriculum.