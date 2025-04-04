from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI

# Initialize the LLM
llm = OpenAI()

# Define the prompt template
prompt_template = PromptTemplate(
    input_variables=["query"],
    template="Given the query '{query}', identify the Python function to call. Options are book_flight(), order_food(), make_payment(), or nothing().",
)

# Create a chain to identify the function
identify_function_chain = LLMChain(llm=llm, prompt=prompt_template)

# Example functions
def book_flight():
    return "Flight booked."

def order_food():
    return "Food ordered."

def make_payment(amount, method):
    return f"Payment of {amount} made using {method}."

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
    else:
        return nothing()

# Test the function
queries = [
    "I want to book a flight.",
    "Can you order food for me?",
    "Make a payment of 100 using PayPal.",
    "Do nothing.",
    "Make a payment without specifying details."
]

for query in queries:
    print(f"Query: {query}")
    print(f"Response: {process_query(query)}")
    print("\n")
