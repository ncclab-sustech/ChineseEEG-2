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

For ISC analysis we offer several functions that the user can adjust its usage based on different datasets:`combine_data`, `load_bids_data`, `filter_data`, `prepare_data_for_cca`, `train_subject`, `test_on_other_subjects`, and `run_isc_analysis`

`combine_data`, `load_bids_data`, `filter_data`, `prepare_data_for_cca`: Functions for loading the data, filtering, preparing data into dict format, and combining data from multiple folders for potential between-group analysis. Please use the functions as the example below:

```
def main():
    bids_paths = ["dataset1", "dataset2"]  # Two BIDS folders
    # Define subject lists for each folder
    subject_mapping = [
        ["m1", "m2", "f1", "f2"],  # Folder 1: Bids folder 1 subject names
        ["01", "02", "03", "04", "05", "06", "07", "08"]  # Folder 2: Bids folder 2 subject names
    ]
    tasks = ["reading", "lis"]  # Tasks for each folder (Folder 1: reading, Folder 2: listening)
    runs_list = ['11','12','13','14','15','16','17','18','19','110']
    session = "littleprince"
    run = "113"
    sfreq = 128
    start_sec = 30
    end_sec = 40
    n_components = 3  
    # Run ISC analysis for both BIDS folders
    run_isc_analysis_single_subject_training(
        bids_paths, subject_mapping, tasks, session, run, sfreq, start_sec, end_sec, n_components, runs_list
    )
```

## Audio reconstruction
We also performed audio reconstruction to validate our dataset, to use this code, please refer to [mTRF-Toolbox](https://sourceforge.net/projects/aespa/)
