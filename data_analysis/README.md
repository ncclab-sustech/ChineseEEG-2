# Analysis for EEG Data

## Introduction

The script in this folder contains code for source reconstruction and Inter-Subject Correlation (ISC) analysis.

## Source Reconstruction

We use defined head models as template to help create solutions:

[head model download](https://github.com/connectomicslab/connectomemapper3)

The detailed information about the parameters are shown below:

| Parameter                   | type  | Explanation                                                  |
| --------------------------- | ----- | ------------------------------------------------------------ |
| onset_start                 | float | start of the time window processed in the epoch.             |
| onset_end                   | float | end of the time window processed in the epoch.               |
| time_start                  | float | start of the EEG segment being analyzed.                     |
| time_end                    | float | end of the EEG segment being analyzed.                       | 
| bids_root                   | str   | path to the root of your BIDS dataset.                       |
| subject_name                | str   | name of the subject in your dataset you want to analyze.     |
| session                     | str   | name of the session in your dataset you want to analyze.     |
| run                         | str   | number of run in your dataset you want to analyze.           |
| task                        | str   | name of the task in your dataset you want to analyze.        |
| output_dir                  | str   | path to output the solutions and source spaces.              |
| fsaverage_data_dir          | str   | path to the downloaded data template.                        |

## ISC analysis

This Python script performs a comprehensive Inter-Subject Correlation (ISC) analysis on EEG data. The script is designed for high-throughput analysis, leveraging both GPU acceleration (via CuPy) and CPU parallel processing to handle large datasets efficiently.

### Workflow

The analysis follows these key steps:

1.  **Data Loading & Alignment:**
    *   For each subject, loads pre-filtered EEG data, separated into frequency bands (`Delta`, `Theta`, `Alpha`, `Beta`).
    *   Aligns the data segments from different subjects based on these shared event markers, ensuring that the correlation is calculated on temporally synchronized neural activity.

2.  **Pairwise Correlation:**
    *   The script iterates through all possible pairs of subjects for a given task, session, and run.
    *   For each pair and each frequency band, it calculates the correlation for every common electrode channel.
3.  **Output:**
    *   The final results for each subject pair are saved as a `.npy` file containing a detailed dictionary with the original correlation `r-value`, `p-value`, statistics from the random permutation analysis, and a list of channels that showed statistically significant correlation.
