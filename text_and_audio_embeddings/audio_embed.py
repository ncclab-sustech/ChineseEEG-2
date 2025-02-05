import os
import torch
import torchaudio
from transformers import Wav2Vec2Processor, Wav2Vec2Model
import numpy as np
from transformers import AutoProcessor, AutoModelForCTC

processor = AutoProcessor.from_pretrained("airesearch/wav2vec2-large-xlsr-53-th")
model = AutoModelForCTC.from_pretrained("airesearch/wav2vec2-large-xlsr-53-th")
root_dir = "example/path"


processor = Wav2Vec2Processor.from_pretrained("airesearch/wav2vec2-large-xlsr-53-th")
model = Wav2Vec2Model.from_pretrained("airesearch/wav2vec2-large-xlsr-53-th")

root_dir = "example/root"  #

def extract_audio_embeddings(audio_path):
    # Load the audio file using torchaudio
    waveform, sample_rate = torchaudio.load(audio_path)
    print(f"Loaded waveform shape: {waveform.shape} (Channels, Frames)")

    # Resample the audio to 16kHz if necessary (Wav2Vec2 expects 16kHz sample rate)
    if sample_rate != 16000:
        waveform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)(waveform)
    print(f"Resampled waveform shape: {waveform.shape} (Channels, Frames)")

    # Ensure the waveform is mono (1 channel), if stereo (2 channels), take the mean of the channels
    if waveform.ndim > 1:  # If the waveform has more than 1 channel (i.e., stereo)
        waveform = waveform.mean(dim=0)  # Convert to mono by averaging channels
        print(f"Converted to mono waveform shape: {waveform.shape} (Channels, Frames)")

    # Ensure the waveform has the correct shape: [batch_size, num_channels, num_frames]
    if waveform.ndimension() == 2:  # If waveform has shape [num_channels, num_frames]
        waveform = waveform.unsqueeze(0)  # Add a batch dimension: [1, num_channels, num_frames]
    print(f"Final waveform shape (before processor): {waveform.shape} (Batch, Channels, Frames)")

    # Process the audio using the Hugging Face processor
    inputs = processor(waveform, return_tensors="pt", sampling_rate=16000)

    # Print out the shape of the inputs before passing to the model
    print(f"Input shape to processor: {inputs['input_values'].shape}")

    # Get the model output (last hidden state)
    with torch.no_grad():
        outputs = model(**inputs)

    # Extract the embeddings (use the last hidden state)
    embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()  # Taking mean of all token embeddings

    return embeddings

# Loop through the folders and extract embeddings for each audio file
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".wav"):
            audio_path = os.path.join(subdir, file)
            print(f"Processing: {audio_path}")
            
            # Extract the embedding for the current audio file
            embeddings = extract_audio_embeddings(audio_path)
            
            # Save the embeddings with the name "audio_embedding_n.npy"
            embedding_filename = f"audio_embedding_{file.split('.')[0]}.npy"
            embedding_path = os.path.join(subdir, embedding_filename)
            
            # Store the embedding as a .npy file
            np.save(embedding_path, embeddings)

print("Embeddings generation and saving completed!")