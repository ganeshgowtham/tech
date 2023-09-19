import os
import torch
from transformers import BertForQuestionAnswering, BertTokenizer

# Function to load content from log files and train the model
def train_log_model(log_dir):
    # Initialize an empty list to store log content
    log_content = []

    # Loop through log files in the specified directory
    for filename in os.listdir(log_dir):
        if filename.endswith(".log"):  # Assuming log files have a .txt extension
            file_path = os.path.join(log_dir, filename)
            with open(file_path, 'r') as file:
                for content in file.readlines():
                    log_content.append(content)
                    print('cool')

    # Load the BERT model and tokenizer
    
    model = BertForQuestionAnswering.from_pretrained("deepset/bert-large-uncased-whole-word-masking-squad2")
    tokenizer = BertTokenizer.from_pretrained("bert-large-uncased-whole-word-masking")

    # Preprocess the log content and train the model (simplified for illustration)
    # In practice, you'd define your questions and perform more detailed training
    questions = ["What happened?", "When did it occur?"]
    for log_entry in log_content:
        for question in questions:
            print('question ', question)
            print(' log_entry ', log_entry)                  
            inputs = tokenizer(question, log_entry, return_tensors="pt")
            outputs = model(**inputs)
            # Store or process the answers as needed
            answer_start = torch.argmax(outputs.start_logits)
            answer_end = torch.argmax(outputs.end_logits)
            print('answer start')
            answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end]))
            # You can store or process the 'answer' here
            print('answer end')
    # Return the trained model
    return model

# Function to query the trained model and respond to queries
def query_model(model, question, context):
    tokenizer = BertTokenizer.from_pretrained("bert-large-uncased-whole-word-masking")
    inputs = tokenizer(question, context, return_tensors="pt")
    outputs = model(**inputs)
    answer_start = torch.argmax(outputs.start_logits)
    answer_end = torch.argmax(outputs.end_logits)
    answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end]))
    return answer

# Example usage:
if __name__ == "__main__":
    log_directory = "C:\\Users\\ganes\\Downloads\\log"
    trained_model = train_log_model(log_directory)
    
    # Example query
    query = "what is capital of France"
    context = "Paris is capital of France"
    print('executing query')
    response = query_model(trained_model, query, context)
    
    print("Response:", response)
