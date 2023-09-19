import torch
from transformers import BertTokenizer, BertModel
import numpy as np

# Load the pre-trained model and tokenizer
model_name = 'deepset/bert-large-uncased-whole-word-masking-squad2'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)

# Function to generate word embeddings
def generate_word_embeddings(text_file_path):
    # Read the content of the text file
    with open(text_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Initialize an empty list to store the embeddings
    embeddings = []

    # Process each line in the text file
    for line in lines:
        # Tokenize the text
        tokens = tokenizer(line, padding=True, truncation=True, return_tensors='pt')
        
        # Get the model's output
        with torch.no_grad():
            outputs = model(**tokens)
            embeddings.append(outputs.last_hidden_state.mean(dim=1).numpy())

    # Convert the list of embeddings to a numpy array
    embeddings = np.vstack(embeddings)

    return embeddings

# Example usage
text_file_path = 'C:\\Users\\ganes\\Downloads\\log\\Android_2k.log'
output_file_path = 'C:\\Users\\ganes\\Downloads\\log\\Android_2k.npy'
embeddings = generate_word_embeddings(text_file_path)
np.save(output_file_path, embeddings)

# Now, 'embeddings' contains the word embeddings for the content in the text file
print(embeddings.shape)  # Print the shape of the embeddings matrix
