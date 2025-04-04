from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI
import re

# Initialize the LLM
llm = OpenAI()

# Define the prompt template
prompt_template = PromptTemplate(
    input_variables=["query"],
    template="Given the query '{query}', identify the Python function to call. Options are book_flight(), order_food(), make_payment(), fix_payment(), repair_payment(), fix_first_transaction(), fix_last_transaction(), fix_nth_transaction(), or nothing().",
)

# Create a chain to identify the function
identify_function_chain = LLMChain(llm=llm, prompt=prompt_template)

# Example transactions (for demonstration purposes)
transactions = [
    {"id": 1, "status": "pending"},
    {"id": 2, "status": "pending"},
    {"id": 3, "status": "pending"},
    {"id": 4, "status": "pending"},
    {"id": 5, "status": "pending"},
    {"id": 6, "status": "pending"},
    {"id": 7, "status": "pending"},
    {"id": 8, "status": "pending"},
    {"id": 9, "status": "pending"},
    {"id": 10, "status": "pending"},
]

# Example functions
def book_flight():
    return "Flight booked."

def order_food():
    return "Food ordered."

def make_payment(amount, method):
    return f"Payment of {amount} made using {method}."

def fix_payment(transaction_id):
    for transaction in transactions:
        if transaction["id"] == int(transaction_id):
            transaction["status"] = "fixed"
            return f"Payment with transaction ID {transaction_id} fixed."
    return "Transaction ID not found."

def repair_payment(transaction_id):
    for transaction in transactions:
        if transaction["id"] == int(transaction_id):
            transaction["status"] = "repaired"
            return f"Payment with transaction ID {transaction_id} repaired."
    return "Transaction ID not found."

def fix_first_transaction():
    if transactions:
        transactions[0]["status"] = "fixed"
        return f"First transaction (ID {transactions[0]['id']}) fixed."
    else:
        return "No transactions found."

def fix_last_transaction():
    if transactions:
        transactions[-1]["status"] = "fixed"
        return f"Last transaction (ID {transactions[-1]['id']}) fixed."
    else:
        return "No transactions found."

def fix_nth_transaction(n):
    try:
        n = int(n)
        if n > 0 and n <= len(transactions):
            transactions[n-1]["status"] = "fixed"
            return f"{n}th transaction (ID {transactions[n-1]['id']}) fixed."
        else:
            return "Invalid transaction number."
    except ValueError:
        return "Invalid transaction number."

def nothing():
    return "No action taken."

# Process the user query
def process_query(query):
    # Invoke the chain
    response = identify_function_chain({"query": query})
    
    # Parse the response to determine the function to call
    if "book_flight" in response:
        return book_flight()
    elif "order_food" in response:
        return order_food()
    elif "make_payment" in response:
        # Extract payment details from the query
        if "amount" in query and "method" in query:
            amount = query.split("amount")[1].split(" ")[1]
            method = query.split("method")[1].split(" ")[1]
            return make_payment(amount, method)
        else:
            return "Payment details not specified."
    elif "fix_payment" in response or "repair_payment" in response:
        # Extract transaction ID from the query
        transaction_id = extract_transaction_id(query)
        if transaction_id:
            if "fix" in query:
                return fix_payment(transaction_id)
            elif "repair" in query:
                return repair_payment(transaction_id)
        else:
            return "Transaction ID not specified."
    elif "fix_first_transaction" in response:
        return fix_first_transaction()
    elif "fix_last_transaction" in response:
        return fix_last_transaction()
    elif "fix_nth_transaction" in response:
        # Extract the nth number from the query
        match = re.search(r"(\d+)(?:th|st|nd|rd)", query)
        if match:
            return fix_nth_transaction(match.group(1))
        else:
            return "Transaction number not specified."
    else:
        return nothing()

# Function to extract transaction ID from the query
def extract_transaction_id(query):
    patterns = [
        r"transaction (\d+)",  # Matches "transaction 1234"
        r"with id (\d+)",       # Matches "with id 1234"
        r"(\d+)"                # Matches standalone numbers
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1)
    
    return None

# Test the function
queries = [
    "I want to book a flight.",
    "Can you order food for me?",
    "Make a payment of 100 using PayPal.",
    "Fix Zelle payment with transaction 8900.",
    "Repair the payment with id 8908098.",
    "Fix the transaction 9090.",
    "Fix first transaction.",
    "Fix last transaction.",
    "Fix 9th transaction.",
    "Do nothing.",
    "Make a payment without specifying details."
]

for query in queries:
    print(f"Query: {query}")
    print(f"Response: {process_query(query)}")
    print("\n")
