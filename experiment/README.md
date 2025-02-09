# Reading-aloud task and Passive-listening task display project

## Introduction

This project aims to conduct a novel reading task with **real-time highlighted sentence** based on **Chinese language corpora** while simultaneously recording participants' brainwave (EEG) data. The collected data can be utilized for EEG language decoding and related research endeavors.

## Device Models

EGI: 128-channel

## Environment

**This project must be based on Python version 3.10!!!** You can use Anaconda to create a new environment to run this project. The command is as follows:

```
conda create -n psychopy_tobii python=3.10
```

Then you can activate this environment to install packages we need:

```
conda activate psychopy_tobii
```

### Psychopy

The entire experimental program is written based on Psychopy. You can download Psychopy either through the command line using the following command or by downloading it from the Psychopy official website: https://www.psychopy.org/.

```
pip install psychopy
```

There are two modes in Psychopy: builder and coder. In our project, we use the coder to implement our experiment.


### egi-pynetstation

egi-pynetstation is a python package to enable the use of a Python-based API for EGI's NetStation EEG amplifier interface. Install it using the following command:

```
pip install egi-pynetstation
```

For more information about this package, you can visit this website: https://github.com/nimh-sfim/egi-pynetstation

## Code Explanation

Before you conduct the experiment, you should first cut your novel to our required format using `cut_Chinese_novel.py` in the `novel_segmentation` section. You can read the README in that section for detailed information. 

After material preparation, the script `ui_experiment.py` and `recording.py` can be used to perform Reading-aloud task the experiment. The script `experiment_listen.py` and `recording_listen.py`  contains code for the listening experiment.

### Main Experiment

#### Main Procedure

`recording.py` enables trigger sending in the experiment, which should be guaranteed to be initiated first in the reading experiment, `recording_listen.py`  should also be initiated first in listening experiment
#### Parameters

Detailed explanations of the parameters will be provided below. Note that you must change the bold parameter to your own settings, or there may be some errors and calculation inaccuracies.

| Parameter                      | type  | default                                | usage                                                        |
| ------------------------------ | ----- | -------------------------------------- | ------------------------------------------------------------ |
| highlight_color                | str   | 'red'                                  | Highlight color of the characters                            |                  
| shift_time                     | float | 0.25                                   | The shifting time of the highlighted character               |                  
| novel_path                     | str   | "segmented_Chinese_novel_main.xlsx"    | The path of the  .xlsx format novel you want to play         |
| preface_path                   | str   | "segmented_Chinese_novel_preface.xlsx" | The path of the  .xlsx format preface you want to play       |
| fullscreen                     | bool  | True                                   | Whether to set a full screen                                 |
| rest_period                    | int   | 1                                      | The chapter interval of rest                                 |
| force_rest_time                | int   | 20                                     | The forced rest time                                         |
| isFirstSession                 | bool  | True                                   | Whether this is the first session of the experiment, this will determine whether to display the preface before the formal experiment. |

**Notice**: As mentioned in the previous section, we may run this script multiple times in the experiment to sequentially present each part of the novel. You need to specify the parameter "isFirstSession" every time you run this program to let it know if this is the first playback. If the value is "True," the program will play the preface to do practice reading before the formal reading begins. If it is "False," the practice reading part will be skipped, and the program will start directly from the main content.

#### EEG Markers

If you use the EGI device to record EEG signals during the experiment, our program will place markers at certain corresponding time points. These markers will assist you in aligning eye tracker recordings and EEG signals, as well as locating texts corresponding to specific segments of EEG signals.

The detailed information of markers are shown below:

```
BEGN: EGI starts to record
STOP: EGI stops recording
CH01：Beginning of specific chapter (Numbers correspond with chapters) 
ROWS: Beginning of a row
ROWE: End of a row
PRES：Beginning of the preface
PREE：End of the preface
```

## Experiment Procedure

The experimental setup is as below:

![](https://github.com/ncclabsustech/Chinese_reading_task_eeg_processing/blob/main/image/exp_layout.png)

Below are the operational steps and an example of starting the project from scratch, using the novel *The Little Prince* as an example.

### Activate Environment

First, activate the environment we set up before, and then navigate to the directory where the project is located.

```
conda activate psychopy_tobii
cd <your_path_to_project>
```

### Novel Segmentation

Take a `.txt` novel file that meets the format requirements (format requirements can be found in the "Sentence Segmentation" section of the Code Explanation) as input. Specify the parameter to divide the text into several parts. Run `cut_Chinese_novel.py`, and you will obtain the corresponding number of `.xlsx` files.

### Main Experiment

- First, connect the EGI equipment.
- Next, adjust the parameters and run the main program. Set the addresses for the main body and preface parts in the variables `novel_path` and `preface_path`, respectively. Change `host_IP`and `egi_IP` to the IP numbers of your own devices. Set `isFirstSession` to True during the first run to include the preview session. Other adjustable parameters can be found in the "Parameters" section of the Code Explanation under Main Experiment. Note that you may need to modify some size and distance-related parameters according to your own setup. In subsequent runs, change the `novel_path` to read different parts of the novel and set `isFirstSession` to False.

- **During the forced break period, the EGI system will be disconnected. ** ***At this time, you need to restart the EGI system to ensure it is in a running state before the participant continues the experiment, or the program will crash!!!***

- **At the end of each experimental session, it is necessary to replenish the saline for the participant's EEG cap and restart the EGI system.** 

- The main process of the experiment includes: preface session (only in the first part) - formal reading - rest (including mandatory rest and participant-initiated rest periods). 

  - Preface Reading

  - Formal Reading

  - Rest

    **restart the EGI system to ensure it is in a running state before the participant continues the experiment**

  



