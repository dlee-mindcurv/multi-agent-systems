# Reflection Report - Munder Difflin Paper Company Multi-Agent System

## 1. Architecture Explanation

### Orchestrator-Worker Pattern

The system uses an **orchestrator-worker pattern** with four agents built on the [smolagents](https://github.com/huggingface/smolagents) framework. A single Orchestrator agent receives every customer inquiry and delegates work to three specialized workers: Inventory, Quoting, and Sales. This pattern was chosen for several reasons:

- **Separation of concerns**: Each worker agent has a focused responsibility and a small, well-defined tool set. This makes individual agents easier to reason about and debug compared to a single monolithic agent with many tools.
- **Cost efficiency**: The Orchestrator uses a more capable model (Claude Sonnet 4 / gpt-4o) for complex reasoning and request parsing, while worker agents use a smaller, cheaper model (Claude Haiku 4.5 / gpt-4o-mini) for straightforward tool-calling tasks. This keeps API costs low without sacrificing quality where it matters.
- **Controlled execution flow**: The Orchestrator enforces a consistent workflow (parse -> inventory check -> quote -> sale) and prevents workers from taking actions outside their scope. For example, the Inventory agent cannot process sales, and the Sales agent cannot generate quotes.
- **Bounded complexity**: Each worker is limited to `max_steps=3`, which prevents runaway tool-calling loops and keeps responses fast. The Orchestrator has a higher limit (`max_steps=8`) to accommodate the multi-step coordination it performs across workers.

### Agent Roles and Decision-Making

**Orchestrator** - The "brain" of the system. It receives natural-language customer requests and must: (1) parse out the specific items, quantities, and deadlines; (2) map vague product descriptions to exact catalog item names (e.g., "glossy photo paper" -> "Glossy paper" or "Photo paper"); (3) decide the order of worker delegation; and (4) compose a customer-friendly final response that explains what was fulfilled and what was not, without exposing internal data like margins or error messages. The full product catalog is included in its system prompt so it can accurately map customer descriptions.

**Inventory Agent** - Checks whether requested items are in stock and at what levels. It can query a single item (`check_inventory_item`), list everything in stock (`check_all_inventory`), or estimate supplier delivery times (`check_supplier_delivery`). This is always the first worker called to avoid quoting or selling items that are unavailable.

**Quoting Agent** - Generates price quotes with bulk discount tiers (5% for 100-499 units, 10% for 500-999, 15% for 1000+). It can also search historical quote data (`search_past_quotes`) for reference pricing and generate financial reports (`get_financial_report_tool`). It only runs after inventory availability is confirmed.

**Sales Agent** - Finalizes transactions by recording sales in the database (`process_sale`), checking the company's cash balance (`check_cash_balance`), and placing restock orders from suppliers (`process_restock_order`). It validates stock levels and cash balance before committing any transaction.

See [WORKFLOW_DIAGRAM.md](WORKFLOW_DIAGRAM.md) for a visual representation of the agent topology, tool assignments, and data flow.

### Framework Choice: smolagents

The [smolagents](https://github.com/huggingface/smolagents) framework from Hugging Face was chosen because:

1. **Minimal boilerplate**: Agents and tools are defined with simple Python decorators (`@tool`) and class constructors. No complex configuration files or schemas are needed.
2. **Native multi-agent support**: The `managed_agents` parameter on `ToolCallingAgent` provides built-in orchestrator-worker delegation without custom routing code.
3. **Model flexibility**: smolagents supports `OpenAIServerModel` for OpenAI-compatible endpoints and `LiteLLMModel` for Anthropic/other providers, making it easy to switch between the Vocareum proxy and Anthropic APIs with a single environment variable change.
4. **Tool-calling agents**: The `ToolCallingAgent` class uses structured tool calls rather than code generation, which is more reliable and safer for a system that modifies database state.

## 2. Evaluation Results Discussion

### Test Setup

The evaluation runs 20 customer inquiries from `quote_requests_sample.csv` through the agent system sequentially, ordered by request date (April 1-17, 2025). Each request is processed by the Orchestrator, and the resulting cash balance, inventory value, and customer-facing response are recorded in `test_results.csv`.

The initial state is:
- Cash balance: $45,059.70 (from the $50,000 seed minus initial stock order costs)
- Inventory value: $4,940.30 (16 of 42 catalog items stocked, with 200-800 units each)

### API Configuration

The Vocareum OpenAI proxy has a $5 budget cap that was consumed during initial development. To complete the evaluation, the system was re-run using Anthropic Claude models (Claude Sonnet 4 as orchestrator, Claude Haiku 4.5 as workers) via the `LiteLLMModel` integration in smolagents. The code auto-detects which API key is available (`ANTHROPIC_API_KEY` or `UDACITY_OPENAI_API_KEY`) and configures models accordingly.

### Results Summary

All 20 requests were processed successfully with zero errors. The system produced a healthy mix of fulfilled, partially fulfilled, and declined requests:

| Metric | Value | Rubric Requirement |
|---|---|---|
| Cash balance changes | 7 | >= 3 |
| Fulfilled requests | 4 | >= 3 |
| Declined/partial requests | 16 | Some required |
| Error responses | 0 | -- |
| Final cash balance | $45,297.28 | Changed from $45,059.70 |
| Final inventory value | $4,681.25 | Changed from $4,940.30 |

### Cash Balance Changes (7 transactions)

| Request | Change | New Balance | Description |
|---|---|---|---|
| 1 | +$61.75 | $45,121.45 | Ceremony order: glossy paper, cardstock, colored paper |
| 5 | +$47.75 | $45,169.20 | Party order: colored paper, cardstock, washi tape |
| 12 | -$22.75 | $45,146.45 | Party order with restock: cardstock, copy paper, napkins (sale minus restock cost) |
| 10 | +$64.43 | $45,210.88 | Show order with restock: glossy paper, cardstock |
| 14 | +$66.50 | $45,277.38 | Performance order: partial cardstock fulfillment |
| 15 | +$1.90 | $45,279.28 | Assembly order: small partial fulfillment |
| 16 | +$18.00 | $45,297.28 | Assembly order: A4 paper partial fulfillment |

Note: Request 12 shows a net *decrease* because the sales agent placed restock orders (stock_orders) whose cost exceeded the sale revenue for that request, demonstrating that the system correctly handles both transaction types.

### Fulfilled Requests (4 complete orders)

- **Request 1** (ceremony): 200 glossy paper + 100 cardstock + 100 colored paper = $61.75 with 5% bulk discounts
- **Request 5** (party): 500 colored paper + 300 cardstock + 200 washi tape = $125.75 with 5-10% bulk discounts
- **Request 10** (show): 500 glossy paper + 300 cardstock = $132.75 with 5-10% bulk discounts, split delivery arranged
- **Request 12** (party): 200 cardstock + 500 copy paper + 100 napkins = $48.40 with 5-10% bulk discounts

### Declined/Partial Requests (16 requests)

Requests were declined or only partially fulfilled for several reasons:

1. **Items not in inventory** (most common): Many requested items like matte paper, recycled paper, construction paper, envelopes, and A3 paper were among the 26 unstocked catalog items. Examples: requests 3, 4, 6, 7, 8, 11.

2. **Items not in catalog**: Some customer requests included non-paper products (balloons in request 2, tickets in request 20) that don't exist in the Munder Difflin catalog at all.

3. **Insufficient quantity**: Later requests (14-19) faced stock depletion from earlier sales. For example, by request 16, only 272 sheets of A4 paper remained after earlier transactions consumed stock.

4. **Tight delivery deadlines**: Some requests had delivery dates too close to allow for supplier restocking (e.g., request 13 needed delivery in 2 days, but supplier lead time was 4 days).

### System Strengths

1. **Accurate catalog matching**: The Orchestrator's system prompt includes the full catalog with exact item names, enabling it to map vague customer descriptions ("glossy photo paper" -> "Glossy paper", "printer paper" -> "A4 paper" or "Standard copy paper") to the correct catalog entries.
2. **Bulk discount application**: The quoting and sales tools consistently apply the correct discount tier (5% for 100-499, 10% for 500-999, 15% for 1000+), and customer-facing responses clearly explain the savings.
3. **Inventory awareness**: The system always checks stock before quoting or selling, preventing failed transactions. When stock is insufficient, it provides honest partial-fulfillment options rather than false promises.
4. **Professional customer communication**: All 20 responses are customer-friendly, with clear formatting, alternative suggestions for unavailable items, and no exposure of internal data (margins, cost prices, error traces).
5. **Proactive restocking**: The sales agent sometimes placed restock orders to fulfill customer requests (visible in request 12's net-negative cash change), demonstrating cross-tool coordination within an agent.

## 3. Improvement Suggestions

### Improvement 1: Customer Negotiation Agent (5th Agent)

Currently, when an item is out of stock or only partially available, the system simply declines and moves on. A dedicated **Negotiation Agent** could improve the customer experience by:

- **Suggesting alternatives**: If "Matte paper" is out of stock, offer "Glossy paper" or "Uncoated paper" as substitutes. The agent could use catalog metadata (category, price range) to find similar items.
- **Offering partial fulfillment**: Instead of declining a multi-item order entirely, propose fulfilling the available items immediately and backordering the rest with an estimated delivery date (using the existing `check_supplier_delivery` tool).
- **Handling quantity adjustments**: If a customer requests 1000 units but only 500 are in stock, the agent could offer the 500 with a note about restocking timeline.

This would fit within the 5-agent maximum and directly improve the fulfillment rate on partially-fulfillable requests (which make up the majority of the test scenarios).

### Improvement 2: Proactive Restocking with Inventory Thresholds

The current system only restocks when explicitly triggered. A **proactive restocking** enhancement would:

- **Monitor stock levels against `min_stock_level`**: After each sale, check if any item dropped below its minimum threshold.
- **Auto-trigger restock orders**: When stock falls below the minimum, automatically place a restock order for a calculated replenishment quantity, using the existing `process_restock_order` tool and `get_cash_balance` to ensure funds are available.
- **Prioritize by demand**: Track which items sell most frequently (using the transactions table) and maintain higher buffer stock for popular items.

This would prevent stockout situations that currently cause request failures, especially in sequential test scenarios where early sales deplete stock for later requests. The infrastructure already exists -- `min_stock_level` is stored in the inventory table and `process_restock_order` handles the full restock workflow including cash validation and delivery estimation.

### Improvement 3: Increased Resilience for Complex Multi-Item Requests

Several test scenarios involve 3-5 items per request. With the current `max_steps=3` limit on worker agents, complex requests can exhaust the step budget before completing all tool calls. Improvements include:

- **Dynamic step limits**: Scale `max_steps` based on the number of items detected in the request (e.g., 2 steps per item + 1 buffer).
- **Batch tool calls**: Modify tools to accept lists of items instead of one at a time, reducing the number of agent steps needed. For example, `check_inventory_items(items: list[str], as_of_date: str)` could check multiple items in a single call.
- **Retry with context**: If a worker hits its step limit, the Orchestrator could retry with the remaining items rather than failing the entire sub-task.

This would improve reliability on the larger test scenarios (requests 3, 7, 8, 14, 15) that involve multiple items and currently risk partial processing.
