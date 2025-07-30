# ChineseEEG-2:An EEG Dataset for Multimodal Semantic Alignment and Neural Decoding during Reading and Listening

## Introduction

Existing Electroencephalography (EEG) datasets for language processing are predominantly English-centric, limiting cross-linguistic neuroscience and brain-computer interface (BCI) research. While current resources capture single-modality tasks (e.g., silent reading or auditory comprehension), they lack synchronized multimodal alignment and ignore understudied languages like Chinese. Furthermore, most datasets face challenges in temporal precision ("teacher-forcing" paradigms) and fail to bridge neural representations with emerging multimodal AI systems.

To address these gaps, we present ChineseEEG-2, the first high-density EEG dataset enabling cross-modal semantic alignment between reading aloud and passive listening within a unified Chinese corpus. Building on the silent reading-focused ChineseEEG dataset, ChineseEEG-2 also includes:

> Multimodal synchronization: Aligned EEG, text, and audio timelines for identical semantic stimuli across reading/listening tasks.

> Cross-task neural data: 32.4 hours of data from 12 participants (4 readers, 8 listeners) to study modality-specific and shared neural dynamics.

> MLLM-EEG alignment: Precomputed semantic embeddings (BERT and Wav2Vec2) for direct comparison with multimodal large language models (MLLMs).

This dataset uniquely supports three research frontiers:

Cross-modal semantic processing: How the brain integrates visual (text) and auditory (speech) language inputs.

Multimodal neural decoding: Developing BCI systems leveraging complementary neural signatures of reading and listening.

Brain-MLLM alignment: Benchmarking artificial language models against human neural representations.

The repository provides full experimental code, preprocessing pipelines, and analysis tools (ISC, source reconstruction, stimulus decoding) to accelerate EEG-based language research. 

**Dataset Access**: [Science Data Bank](https://doi.org/10.57760/sciencedb.CHNNeuro.00001)

## Repository Structure
```
├── novel_segmentation/ # Text material processing
│ └── cut_chinese_novel.py
├── experiment/ # Task implementation
│ ├── ui_experiment.py # Reading-aloud UI
│ ├── recording.py # RL trigger handling
│ ├── experiment_listen.py # Passive-listening UI
│ └── recording_listen.py # PL trigger handling
├── data_preprocessing/ # EEG pipeline
│ └── preprocessing.py # Fully configurable BIDS converter
├── text_and_audio_embeddings/ # Multimodal embeddings
│ ├── text_embed.py
│ └── audio_embed.py
└── analysis/ # Neural decoding tools
├── isc_analysis.py # Intersubject correlation
└── source_analysis.ipynb # MNE-Python source reconstruction
```
## Pipeline

Our EEG recording and pre-processing pipeline is as follows:

![Pipeline](image/Pipeline_01.jpg)

## Device

### EEG Recording: EGI Geodesic EEG 400 series

During the experiment, The EEG (electroencephalography) data were collected by a `128-channel` EEG system with Geodesic Sensor Net (EGI Inc., Eugene, OR, USA, [Geodesic EEG System 400 series (egi.com)](https://www.egi.com/clinical-division/clinical-division-clinical-products/ges-400-series)). The montage system of this device is `GSN-HydroCel-128`. We recorded the data at a sampling rate of 250 Hz in Reading-aloud tasks and 1000 HZ in Passive-reading tasks.

The 128-channel EEG system with Geodesic Sensor Net (GSN) by EGI is a sophisticated brain activity recording tool designed for high-resolution neuroscientific research. This system features an array of evenly spaced sensors providing complete scalp coverage, ensuring detailed spatial data collection without the need for interpolation. Coupled with the advanced Net Amps 400 amplifiers and intuitive Net Station 5 software, it delivers low noise, high sensitivity EEG data acquisition, and powerful data analysis capabilities, making it an ideal choice for dynamic and expanding research environments.

## Experiment

Participants were seated in an adjustable chair positioned in front of a screen displaying the text. The chair was designed for comfort and support during the extended experimental sessions, with adjustments made to maintain each participant's viewing distance at approximately 67 cm from the screen to simulate typical reading conditions and reduce eye strain. The monitor used measured 54 cm in width and 30.375 cm in height, with a resolution of 1920 × 1080 pixels and a vertical refresh rate of 60 Hz—consistent with the experimental settings in the original dataset [ChineseEEG](https://doi.org/10.57760/sciencedb.CHNNeuro.00007). For detailed information on the specific experimental paradigm, related parameter settings, and more, please refer to the [experiment](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/experiment/README.md) module for further details.


### Environment Settings

Please ensure that your code running environment is properly set up. The required packages and their corresponding version information can be found in the [requirement.txt](https://github.com/ncclab-sustech/ListeningEEG/blob/main/requirements.txt) file located in the project's root directory.

### Experiment Materials Preparation

To prepare the textual reading materials needed for the Reading-aloud task in the experiment, you need to convert your materials into the specific format below:

```
Chinese_novel.txt
Ch0
This is the preface of the novel
Ch1
Chapter 1 of the novel
Ch2
Chapter 2 of the novel
...
...
...
```

Execute the `cut_Chinese_novel.py` script in the `novel_segmentation` directory to perform sentence segmentation on literary texts.

### Experiment Implementation

#### Reading Aloud (RA) Task
1. Initiate `recording.py` first for trigger synchronization
2. Execute `ui_experiment.py` for task presentation

#### Passive Listening (PL) Task
1. Record audio from the Reading-aloud task to serve as stimulus inputs for PL experiments.
2. Launch `recording_listen.py` for trigger initialization
3. Run `experiment_listen.py` for stimulus delivery

## EEG Data Preprocessing
Execute `preprocessing.py` (`data_preprocessing` module) for pipeline processing:

**Processing Workflow:**
1. Data segmentation (adjust `run_definition` for chapter segmentation)
2. Downsampling
3. Bandpass filtering
4. Bad channel interpolation (manual override available)
5. Independent Component Analysis (manual component rejection)
6. Re-referencing

**Customization:**  
Modify in-code parameters for all processing steps.  

[Preprocessing details](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/data_preprocessing/README.md)

## EEG Analysis
### Intersubject Correlation (ISC)
- `isc_analysis.py`: Quantifies neural response similarity across subjects

### Source Reconstruction
- `source_analysis.ipynb`: Computes forward/inverse solutions using MNE-Python

**Input Requirement:** Preprocessed EEG data  

[Analysis documentation](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/data_analysis/README.md)

## Multimodal Embeddings
### Data Organization
- Text embeddings: Whole-novel `.npy` files
- Audio embeddings: Chapter-segmented `.npy` files
- File naming convention: `[novel]_[modality].npy`

### Applications
- EEG-text decoding
- Cross-modal alignment studies
- Neural encoding models

[Embedding specifications](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/embeddings/README.md)
## Credit

- [Chen Sitong](https://github.com/adhjk) - Coder for most parts of the project, Experiment conductor, Data processing.
- [He Cuilin](https://github.com/CuilinHe) - Experiment conductor.
- Li Beiqianyi - Experiment conductor.
- [Li Dongyang](https://github.com/dongyangli-del) - Coder for parts of the scripts used in experiment, Experiment conductor.
- Feel free to contact us if you have any questions about the project.

## Collaborators

- [Wu Haiyan](https://github.com/haiyan0305)  -  University of Macau
- Liu Quanying - Southern University of Science and Technology
- [Wang Xindi](https://github.com/sandywang)
- Wu Mingyang - Southern University of Science and Technology
- Shen Xinke - Southern University of Science and Technology
- Wang Song - Southern University of Science and Technology
- Wei Xuetao - Southern University of Science and Technology
## Funding


