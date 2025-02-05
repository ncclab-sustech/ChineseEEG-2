# ChineseEEG-2 Text/Audio embeddings

## Introduction

This README file aims to show how to get text/audio embeddings using pretrained language models and how to transcribe audios.

## Environment

The required packages and their corresponding version information can be found in the [requirement.txt](https://github.com/ncclabsustech/Chinese_reading_task_eeg_processing/blob/main/requirements.txt) file located in the project's root directory.

## Explanation

### Text Embeddings

We offer the code `text_embedding.py` and audio_embed to generate the text embeddings. Embeddings of the text and audio of the two novels were calculated using a pre-trained language and speech model BERT-base-Chinese and Wav2Vec2 to generate text and audio embeddings, enabling multi-model alignment with EEG recordings.

We offered text/audio embeddings in `ReadingAloud/materials&embeddings` in the dataset. **Notice: The audio recording for Subject 1(male) in the reading aloud task was incomplete due to technical issues, resulting in the last chapter of *Garnett Dream* not being recorded. **

### Audio Transcription

To acquire audio transcriptions for comparison or reasearch purpose, this code can help transcribe the audio corresponding to different chapters in the novel to structure:

```
transcript--subject--novel--transcript.tsv
```

First you should organize the audio to be transcribed into folder:

```
data_path--subject--recall--novel--recall_audio
```

After running the script, you should find the audio transcribed to a whole .tsv file, which can later be used for psychological study or participant concentration analysis
