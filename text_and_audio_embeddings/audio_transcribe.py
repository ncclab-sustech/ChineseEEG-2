import os
import csv
import torch
import librosa
import soundfile as sf
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# Set device (use GPU if available)
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load the Whisper model and processor
model_id = "openai/whisper-large-v3"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

# Set up the pipeline
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)
subject = "subject-name"
novel = "LP"
num = "1"

# Define the path to your audio folder
audio_folder = f"data_path/{subject}/recall"

# List of audio files to process
audio_files = [f"{audio_folder}/audio_{num}.MP3", f"{audio_folder}/audio_{num}.m4a"]

# Define the path to save audio chunks
chunks_folder = f"transcript/{subject}/recall/audio_chunks"
os.makedirs(chunks_folder, exist_ok=True)  # Create folder if it doesn't exist

# Define the output TSV file
output_path = f"transcript/{subject}/{novel}"
output_tsv = f"transcript/{subject}/{novel}/transcript.tsv"


def chunk_audio(audio_path, output_folder, chunk_length=30):
    """
    Splits audio into chunks of a specified length and saves them to a folder.
    Args:
        audio_path (str): Path to the audio file.
        output_folder (str): Path to save the chunks.
        chunk_length (int): Length of each chunk in seconds.
    """
    audio, sr = librosa.load(audio_path, sr=None)
    total_duration = librosa.get_duration(y=audio, sr=sr)
    os.makedirs(output_folder, exist_ok=True)

    for start in range(0, int(total_duration), chunk_length):
        end = min(start + chunk_length, total_duration)
        chunk = audio[int(start * sr):int(end * sr)]
        chunk_path = os.path.join(output_folder, f"chunk_{int(start):04d}-{int(end):04d}.wav")
        sf.write(chunk_path, chunk, sr)


def convert_to_wav(audio_path):
    """
    Converts audio to WAV format if it's not already in WAV format.
    Args:
        audio_path (str): Path to the audio file.
    Returns:
        str: Path to the converted or original WAV file.
    """
    if audio_path.endswith(".wav"):
        return audio_path  # No conversion needed

    audio, sr = librosa.load(audio_path, sr=None)
    wav_path = os.path.splitext(audio_path)[0] + ".wav"
    sf.write(wav_path, audio, sr)
    return wav_path


# STEP 1: Chunk the audio files
for audio_file in audio_files:
    if os.path.exists(audio_file):  # Check if the file exists
        print(f"Processing: {audio_file}")

        # Convert to WAV if necessary
        audio_file = convert_to_wav(audio_file)

        # Create a folder for the chunks of this audio file
        audio_name = os.path.splitext(os.path.basename(audio_file))[0]
        audio_chunk_folder = os.path.join(chunks_folder, audio_name)

        # Split the audio into chunks and save them to the folder
        chunk_audio(audio_file, audio_chunk_folder, chunk_length=30)
    else:
        print(f"File not found: {audio_file}")

# STEP 2: Transcribe the audio chunks and save the transcription
# Ensure the parent directory of the output file exists
parent_directory = os.path.dirname(output_tsv)
os.makedirs(parent_directory, exist_ok=True)

# Open the file for writing, and create it if it doesn't exist
with open(output_tsv, mode="w", newline="", encoding="utf-8") as tsvfile:
    # Create a CSV writer with tab delimiter
    writer = csv.writer(tsvfile, delimiter="\t")

    # Write the header row
    writer.writerow(["File Name", "Transcription"])

    # Iterate through the chunk folders for transcription
    for audio_name in os.listdir(chunks_folder):
        audio_chunk_folder = os.path.join(chunks_folder, audio_name)

        if os.path.isdir(audio_chunk_folder):  # Ensure it's a directory
            print(f"Transcribing: {audio_name}")
            full_transcription = ""

            # Iterate through each chunk in the folder
            for chunk_file in sorted(os.listdir(audio_chunk_folder)):
                chunk_path = os.path.join(audio_chunk_folder, chunk_file)

                if chunk_path.endswith(".wav"):
                    # Transcribe the chunk
                    result = pipe(chunk_path)  # Process the file directly
                    full_transcription += result["text"] + " "  # Concatenate transcriptions

            # Write the combined transcription to the TSV file
            writer.writerow([audio_name, full_transcription.strip()])

