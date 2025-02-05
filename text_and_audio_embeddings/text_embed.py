import os
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModel
import numpy as np

tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
model = AutoModel.from_pretrained("bert-base-chinese")

file_path = 'example/path'
df = pd.read_excel(file_path)

embeddings = []

for sentence in df.iloc[1:, 0]:
    # Tokenize the sentence
    inputs = tokenizer(sentence, return_tensors="pt", truncation=True, padding=True, max_length=512)
    
    # Get the model output
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Extract the embeddings (use the last hidden state)
    last_hidden_state = outputs.last_hidden_state  # shape: (batch_size, seq_len, hidden_size)

    sentence_embedding = last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    
    # Append the embedding to the list
    embeddings.append(sentence_embedding)

# Convert the embeddings list to a numpy array
embeddings = np.array(embeddings)

# Save the embeddings to a file (you can choose the format, e.g., numpy .npy, or pandas .csv)
np.save('example_name.npy', embeddings)  # Save embeddings as a .npy file
# Alternatively, you can save it as a pandas DataFrame to a CSV:
# df_embeddings = pd.DataFrame(embeddings)
# df_embeddings.to_csv('embeddings.csv', index=False)

print("Embeddings saved")
