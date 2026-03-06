import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################

from smolagents import tool, CodeAgent, ToolCallingAgent, OpenAIServerModel

dotenv.load_dotenv()

anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
openai_key = os.environ.get("UDACITY_OPENAI_API_KEY")

if anthropic_key:
    from smolagents import LiteLLMModel
    model = LiteLLMModel(
        model_id="anthropic/claude-sonnet-4-20250514",
        api_key=anthropic_key,
    )
    worker_model = LiteLLMModel(
        model_id="anthropic/claude-haiku-4-5-20251001",
        api_key=anthropic_key,
    )
    print("Using Anthropic Claude models.")
elif openai_key:
    model = OpenAIServerModel(
        model_id="gpt-4o",
        api_base="https://openai.vocareum.com/v1",
        api_key=openai_key,
    )
    worker_model = OpenAIServerModel(
        model_id="gpt-4o-mini",
        api_base="https://openai.vocareum.com/v1",
        api_key=openai_key,
    )
    print("Using OpenAI (Vocareum) models.")
else:
    raise RuntimeError(
        "No API key found. Set ANTHROPIC_API_KEY or UDACITY_OPENAI_API_KEY in .env"
    )

# ── Tools for Inventory Agent ──────────────────────────────────────────

@tool
def check_inventory_item(item_name: str, as_of_date: str) -> str:
    """Check the current stock level of a specific item.

    Args:
        item_name: The exact name of the item to check (e.g. 'A4 paper').
        as_of_date: The date to check stock as of, in YYYY-MM-DD format.

    Returns:
        A string describing the stock level for the item.
    """
    result = get_stock_level(item_name, as_of_date)
    stock = int(result["current_stock"].iloc[0])
    if stock > 0:
        return f"{item_name}: {stock} units in stock as of {as_of_date}."
    return f"{item_name}: OUT OF STOCK as of {as_of_date}."


@tool
def check_all_inventory(as_of_date: str) -> str:
    """Get a summary of all items currently in stock.

    Args:
        as_of_date: The date to check inventory as of, in YYYY-MM-DD format.

    Returns:
        A formatted string listing all items with positive stock levels.
    """
    inventory = get_all_inventory(as_of_date)
    if not inventory:
        return "No items currently in stock."
    lines = [f"- {name}: {qty} units" for name, qty in inventory.items()]
    return "Current inventory as of {}:\n{}".format(as_of_date, "\n".join(lines))


@tool
def check_supplier_delivery(order_date: str, quantity: int) -> str:
    """Estimate the delivery date from the supplier for a given order quantity.

    Args:
        order_date: The date the order would be placed, in YYYY-MM-DD format.
        quantity: The number of units to order.

    Returns:
        A string with the estimated delivery date.
    """
    delivery_date = get_supplier_delivery_date(order_date, quantity)
    return f"Estimated delivery date for {quantity} units ordered on {order_date}: {delivery_date}."


# ── Tools for Quoting Agent ───────────────────────────────────────────

@tool
def calculate_quote(item_name: str, quantity: int, as_of_date: str) -> str:
    """Generate a price quote for a specific item and quantity, applying bulk discounts.

    Discount tiers: 5% for 100-499 units, 10% for 500-999, 15% for 1000+.

    Args:
        item_name: The exact name of the item.
        quantity: The number of units requested.
        as_of_date: The date of the quote request, in YYYY-MM-DD format.

    Returns:
        A formatted quote string with pricing, discounts, and stock availability.
    """
    # Find unit price from catalog
    unit_price = None
    for item in paper_supplies:
        if item["item_name"].lower() == item_name.lower():
            unit_price = item["unit_price"]
            break
    if unit_price is None:
        return f"Item '{item_name}' not found in our catalog."

    # Check stock
    stock_df = get_stock_level(item_name, as_of_date)
    current_stock = int(stock_df["current_stock"].iloc[0])

    # Calculate discount
    if quantity >= 1000:
        discount_pct = 15
    elif quantity >= 500:
        discount_pct = 10
    elif quantity >= 100:
        discount_pct = 5
    else:
        discount_pct = 0

    discounted_price = unit_price * (1 - discount_pct / 100)
    total = round(discounted_price * quantity, 2)

    lines = [
        f"Quote for {quantity}x {item_name}:",
        f"  Unit price: ${unit_price:.2f}",
    ]
    if discount_pct > 0:
        lines.append(f"  Bulk discount: {discount_pct}%")
        lines.append(f"  Discounted unit price: ${discounted_price:.2f}")
    lines.append(f"  Total: ${total:.2f}")
    if current_stock >= quantity:
        lines.append(f"  Availability: IN STOCK ({current_stock} units available)")
    elif current_stock > 0:
        lines.append(f"  Availability: PARTIAL — only {current_stock} of {quantity} units in stock")
    else:
        lines.append(f"  Availability: OUT OF STOCK")
    return "\n".join(lines)


@tool
def search_past_quotes(search_terms: list[str]) -> str:
    """Search historical quotes by keywords (e.g. item types, event types).

    Args:
        search_terms: List of keywords to search for in past quotes.

    Returns:
        A formatted string of matching historical quotes.
    """
    results = search_quote_history(search_terms, limit=5)
    if not results:
        return "No matching historical quotes found."
    lines = []
    for i, q in enumerate(results, 1):
        lines.append(
            f"{i}. Amount: ${q['total_amount']:.2f} | Type: {q['job_type']} | "
            f"Size: {q['order_size']} | Event: {q['event_type']}\n"
            f"   Explanation: {q['quote_explanation']}"
        )
    return "Historical quotes:\n" + "\n".join(lines)


@tool
def get_financial_report_tool(as_of_date: str) -> str:
    """Generate a financial report including cash balance, inventory value, and top sellers.

    Args:
        as_of_date: The date for the report, in YYYY-MM-DD format.

    Returns:
        A formatted financial report string.
    """
    report = generate_financial_report(as_of_date)
    lines = [
        f"Financial Report as of {report['as_of_date']}:",
        f"  Cash Balance: ${report['cash_balance']:.2f}",
        f"  Inventory Value: ${report['inventory_value']:.2f}",
        f"  Total Assets: ${report['total_assets']:.2f}",
    ]
    if report["top_selling_products"]:
        lines.append("  Top Selling Products:")
        for p in report["top_selling_products"]:
            lines.append(f"    - {p.get('item_name', 'N/A')}: ${p.get('total_revenue', 0):.2f}")
    return "\n".join(lines)


# ── Tools for Sales Agent ─────────────────────────────────────────────

@tool
def process_sale(item_name: str, quantity: int, as_of_date: str) -> str:
    """Process a sale transaction: validate stock, apply bulk discounts, and record the sale.

    Args:
        item_name: The exact name of the item to sell.
        quantity: The number of units to sell.
        as_of_date: The date of the sale, in YYYY-MM-DD format.

    Returns:
        A string confirming the sale or explaining why it failed.
    """
    # Check stock
    stock_df = get_stock_level(item_name, as_of_date)
    current_stock = int(stock_df["current_stock"].iloc[0])
    if current_stock <= 0:
        return f"SALE FAILED: '{item_name}' is out of stock."
    if current_stock < quantity:
        return (
            f"SALE FAILED: Insufficient stock for '{item_name}'. "
            f"Requested {quantity}, only {current_stock} available."
        )

    # Get unit price
    unit_price = None
    for item in paper_supplies:
        if item["item_name"].lower() == item_name.lower():
            unit_price = item["unit_price"]
            break
    if unit_price is None:
        return f"SALE FAILED: '{item_name}' not found in catalog."

    # Apply discount
    if quantity >= 1000:
        discount_pct = 15
    elif quantity >= 500:
        discount_pct = 10
    elif quantity >= 100:
        discount_pct = 5
    else:
        discount_pct = 0

    discounted_price = unit_price * (1 - discount_pct / 100)
    total_price = round(discounted_price * quantity, 2)

    # Record the sale
    txn_id = create_transaction(item_name, "sales", quantity, total_price, as_of_date)
    return (
        f"SALE SUCCESSFUL: Sold {quantity}x {item_name} for ${total_price:.2f} "
        f"(discount: {discount_pct}%). Transaction ID: {txn_id}."
    )


@tool
def check_cash_balance(as_of_date: str) -> str:
    """Check the current cash balance of the company.

    Args:
        as_of_date: The date to check the balance as of, in YYYY-MM-DD format.

    Returns:
        A string with the current cash balance.
    """
    balance = get_cash_balance(as_of_date)
    return f"Current cash balance as of {as_of_date}: ${balance:.2f}"


@tool
def process_restock_order(item_name: str, quantity: int, as_of_date: str) -> str:
    """Place a restock order from the supplier for a given item.

    Args:
        item_name: The exact name of the item to restock.
        quantity: The number of units to order.
        as_of_date: The date the order is placed, in YYYY-MM-DD format.

    Returns:
        A string confirming the restock order or explaining why it failed.
    """
    # Get unit price
    unit_price = None
    for item in paper_supplies:
        if item["item_name"].lower() == item_name.lower():
            unit_price = item["unit_price"]
            break
    if unit_price is None:
        return f"RESTOCK FAILED: '{item_name}' not found in catalog."

    total_cost = round(unit_price * quantity, 2)

    # Check cash
    balance = get_cash_balance(as_of_date)
    if balance < total_cost:
        return (
            f"RESTOCK FAILED: Insufficient funds. Need ${total_cost:.2f}, "
            f"only ${balance:.2f} available."
        )

    txn_id = create_transaction(item_name, "stock_orders", quantity, total_cost, as_of_date)
    delivery = get_supplier_delivery_date(as_of_date, quantity)
    return (
        f"RESTOCK SUCCESSFUL: Ordered {quantity}x {item_name} for ${total_cost:.2f}. "
        f"Transaction ID: {txn_id}. Estimated delivery: {delivery}."
    )


# ── Agent Definitions ─────────────────────────────────────────────────

inventory_agent = ToolCallingAgent(
    tools=[check_inventory_item, check_all_inventory, check_supplier_delivery],
    model=worker_model,
    name="inventory_agent",
    description=(
        "Checks inventory stock levels for specific items or all items, "
        "and estimates supplier delivery dates. Call this agent with an item name "
        "and date to find out availability."
    ),
    max_steps=3,
)

quoting_agent = ToolCallingAgent(
    tools=[calculate_quote, search_past_quotes, get_financial_report_tool],
    model=worker_model,
    name="quoting_agent",
    description=(
        "Generates price quotes with bulk discounts for requested items, "
        "searches historical quote data, and produces financial reports. "
        "Call with item name, quantity, and date to get a quote."
    ),
    max_steps=3,
)

sales_agent = ToolCallingAgent(
    tools=[process_sale, check_cash_balance, process_restock_order],
    model=worker_model,
    name="sales_agent",
    description=(
        "Processes sales transactions, checks cash balance, and handles restock orders. "
        "Call with item name, quantity, and date to finalize a sale."
    ),
    max_steps=3,
)

# Build the catalog listing for the orchestrator prompt
_catalog_lines = []
for item in paper_supplies:
    _catalog_lines.append(f"  - {item['item_name']} (${item['unit_price']:.2f}/unit, category: {item['category']})")
_catalog_str = "\n".join(_catalog_lines)

orchestrator = ToolCallingAgent(
    tools=[],
    model=model,
    managed_agents=[inventory_agent, quoting_agent, sales_agent],
    name="orchestrator",
    description="Routes customer requests to the appropriate worker agents.",
    max_steps=8,
    instructions=(
        "You are the Orchestrator for Munder Difflin Paper Company. "
        "Your job is to handle customer inquiries about paper products by coordinating "
        "three worker agents: inventory_agent, quoting_agent, and sales_agent.\n\n"
        "FULL PRODUCT CATALOG (use these EXACT item names when calling agents):\n"
        f"{_catalog_str}\n\n"
        "WORKFLOW for each customer request:\n"
        "1. Parse the request to identify the item(s), quantities, and any deadlines.\n"
        "2. Map customer descriptions to the EXACT item names from the catalog above.\n"
        "   For example, 'glossy photo paper' maps to 'Glossy paper' or 'Photo paper'.\n"
        "3. Call inventory_agent to check stock availability for the requested items.\n"
        "4. If items are in stock, call quoting_agent to generate a quote.\n"
        "5. If the customer wants to proceed (assume yes for quote requests), "
        "   call sales_agent to process the sale.\n"
        "6. If items are NOT in stock (0 units), politely inform the customer that "
        "   we cannot fulfill the order for those items. Do NOT attempt to sell out-of-stock items.\n\n"
        "IMPORTANT RULES:\n"
        "- Always include the request date (from the customer message) in all agent calls.\n"
        "- NEVER expose internal data like profit margins, system errors, or cost prices.\n"
        "- Provide clear, professional, customer-friendly responses.\n"
        "- Explain any bulk discounts that were applied.\n"
        "- If an item cannot be fulfilled, explain that it is not currently available.\n"
        "- Your final answer must be a customer-facing response summarizing what was done.\n"
    ),
)

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        try:
            response = str(orchestrator.run(request_with_date))
        except Exception as e:
            response = f"We're sorry, we were unable to process your request at this time. Please try again later."
            print(f"Agent error: {e}")

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
