# ChineseEEG-2:An EEG Dataset for Multimodal Semantic Alignment and Neural Decoding during Reading and Listening

## Introduction

Existing Electroencephalography (EEG) datasets for language processing are predominantly English-centric, limiting cross-linguistic neuroscience and brain-computer interface (BCI) research. While current resources capture single-modality tasks (e.g., silent reading or auditory comprehension), they lack synchronized multimodal alignment and ignore understudied languages like Chinese. Furthermore, most datasets face challenges in temporal precision ("teacher-forcing" paradigms) and fail to bridge neural representations with emerging multimodal AI systems.

To address these gaps, we present ChineseEEG-2, the first high-density EEG dataset enabling cross-modal semantic alignment between reading aloud and passive listening within a unified Chinese corpus. Building on the silent reading-focused ChineseEEG dataset, ChineseEEG-2 also includes:

#### Multimodal synchronization: Precisely aligned EEG, text, and audio timelines for identical semantic stimuli across reading/listening tasks.

#### Cross-task neural data: 32.4 hours of data from 12 participants (4 readers, 8 listeners) to study modality-specific and shared neural dynamics.

#### MLLM-EEG alignment: Precomputed semantic embeddings (BERT and Wav2Vec2) for direct comparison with multimodal large language models (MLLMs).

This dataset uniquely supports three research frontiers:

Cross-modal semantic processing: How the brain integrates visual (text) and auditory (speech) language inputs.

Multimodal neural decoding: Developing BCI systems leveraging complementary neural signatures of reading and listening.

Brain-MLLM alignment: Benchmarking artificial language models against human neural representations.

The repository provides full experimental code, preprocessing pipelines, and analysis tools (ISC, source reconstruction, stimulus decoding) to accelerate EEG-based language research. 

## Repository structure

The code repository contains five main modules, including scripts to prepare the materials, reproduce the experiment, data processing, data embedding, and data analysis procedures. The script `cut_chinese_novel.py` in the`novel_segmentation` folder contains the code to prepare the stimulation materials from source materials. The script `ui_experiment.py` contains code for the reading experiment and the `recording.py` enables trigger sending in the experiment, which should be guaranteed to be initiated first in the experiment. The script `experiment_listen.py` contains code for the listening experiment. The script `preprocessing.py` in `data_preprocessing` folder contains the main part of the code to apply pre-processing on EEG data and conversion to BIDS format. The script `text_embed.py` in the `text_and_audio_embeddings`  folder contains code to generate embeddings for semantic materials while the script `audio_embed.py` is for generating audio embeddings.  The script `isc_analysis.py` contains necessary code for ISC analysis, and the script `source_analysis.ipynb` is for calculating forward and inverse solution to reconstruct source space.  The code for EEG data pre-processing is highly configurable, permitting flexible adjustments of various pre-processing parameters, such as data segmentation range, downsampling rate, filtering range, and choice of ICA algorithm, thereby ensuring convenience and efficiency. Researchers can modify and optimize this code according to their specific requirements.

## Pipeline

Our EEG recording and pre-processing pipeline is as follows:

![Pipeline](image/Pipeline.jpg)

## Device

### EEG Recording: EGI Geodesic EEG 400 series

During the experiment, The EEG (electroencephalography) data were collected by a `128-channel` EEG system with Geodesic Sensor Net (EGI Inc., Eugene, OR, USA, [Geodesic EEG System 400 series (egi.com)](https://www.egi.com/clinical-division/clinical-division-clinical-products/ges-400-series)). The montage system of this device is `GSN-HydroCel-128`. We recorded the data at a sampling rate of 250 Hz in Reading-aloud tasks and 1000 HZ in Passive-reading tasks.

The 128-channel EEG system with Geodesic Sensor Net (GSN) by EGI is a sophisticated brain activity recording tool designed for high-resolution neuroscientific research. This system features an array of evenly spaced sensors providing complete scalp coverage, ensuring detailed spatial data collection without the need for interpolation. Coupled with the advanced Net Amps 400 amplifiers and intuitive Net Station 5 software, it delivers low noise, high sensitivity EEG data acquisition, and powerful data analysis capabilities, making it an ideal choice for dynamic and expanding research environments.

## Experiment

Participants were seated in an adjustable chair positioned in front of a screen displaying the text. The chair was designed for comfort and support during the extended experimental sessions, with adjustments made to maintain each participant's viewing distance at approximately 67 cm from the screen to simulate typical reading conditions and reduce eye strain. The monitor used measured 54 cm in width and 30.375 cm in height, with a resolution of 1920 × 1080 pixels and a vertical refresh rate of 60 Hz—consistent with the experimental settings in the original dataset [ChineseEEG](https://doi.org/10.57760/sciencedb.CHNNeuro.00007). For detailed information on the specific experimental paradigm, related parameter settings, and more, please refer to the [experiment](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/experiment/README.md) module for further details.

## Usage

To prepare experimental materials, conduct the experiment, and analyze the data, follow the steps below to execute the code.

### Environment Settings

Firstly, please ensure that your code running environment is properly set up, the required packages and their corresponding version information can be found in the [requirement.txt](https://github.com/ncclab-sustech/ListeningEEG/blob/main/requirements.txt) file located in the project's root directory.

### Experiment Materials Preparation

First, to prepare the textual reading materials needed for the Reading-aloud task in the experiment, you need to convert your materials into the specific format below:

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

then run the `cut_Chinese_novel.py` script located in the `novel_segmentation` folder to perform sentence segmentation of the novel text.

We have uploaded the text materials we use in our experiment to the `materials&embeddings` part in out dataset, in which the folder `original_novel` contains the Chinese versions of the novels used in our experiment **The Little Prince** and **Garnett Dream**.

To perform Passive-listening task in this experiment, you need to collect the audio read by the participants in the Reading-aloud task.

### Experiment Scripts

After material preparation, the script `ui_experiment.py` and `recording.py` can be used to perform Reading-aloud task the experiment. `recording.py` enables trigger sending in the experiment, which should be guaranteed to be initiated first in the experiment. The script `experiment_listen.py` and `recording_listen.py ` contains code for the listening experiment, `recording_listen.py ` should also be initiated first.

### Data Pre-processing

After completing the experimental data collection for all participants, we can use the `preprocessing.py` in the `data_preprocessing` module for data preprocessing. Our preprocessing workflow includes: data segmentation, downsampling, filtering, bad channel interpolation, independent component analysis (ICA), and re-referencing. You can change run_definition in the code to change your segmentation of the chapters. We provide options for manual intervention in bad channel interpolation and ICA step to ensure accuracy. All parameters for these methods can be modified by adjusting the settings in the code, the modalities and preprocessing steps are shown below. For detailed information on the preprocessing workflow, explanations of the code, and parameter settings, please refer to the [data_preprocessing](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/data_preprocessing/README.md) module.

### Data Analysis

We offer code for ISC analysis and source reconstruction including `isc_analysis.py`which contains functioni for ISC analysis, allowing for the quantification of similarities in brain responses across different subjects and `source_analysis.ipynb`, which contains code for calculating forward and inverse solutions using MNE package. It is designed to work with the pre-processed EEG data, for detailed information, please refer to the [data_analysis](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/data_analysis/README.md) module.

### Text/Audio Embeddings

We offer the embeddings of the reading materials and its resulting audio. The text material used and its corresponding audio has a corresponding embedding file saved in `.npy` format, the text embedding is saved as a whole novel while the audio is separated based on chaper sequence. These text/audio embeddings provide a foundation for a series of subsequent studies, including the decoding analysis of EEG and textual data. For detailed information, please refer to the [embeddings](https://github.com/ncclab-sustech/ChineseEEG-2/blob/main/embeddings/README.md) module.

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


