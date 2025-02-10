# EEG Pre-processing Pipeline 

This document illustrates the pipeline of our EEG pre-processing and how to use our code to deal with the EEG data. We also provide an explanation of modalities in our datase for your reference.

## Data Pre-processing Pipeline
Here, we pre-process our data to remove obvious artifact to the least extent. An overview of our pre-processing pipeline is shown in the figure below.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/Pipeline.jpg)

Our processing procedure includes these steps:

#### Data Segmentation

We will remain a short time period before and after the valid time range. We will locate the cutting position by referencing the EEG mark. Detailed information can be seen in the method `cut_single_eeg` in `preprocessing.py`. In our procedure, we set the remaining time before the valid range to 10s. Also, we defined one chapter per run for novel material, please adjust based on your definition of segmentation of runs.

#### Resample and Notch filter

Before we do ICA, we will first follow some basic steps, including down-sampling the data and filter the line frequency. In our setting, we assign the resample frequency to 256 Hz and line frequency to 50 Hz.

#### Filtering

We filter the data using a band pass filter to remove artifact. In our processing, we do two versions of filtering with pass band set to 1-40 Hz.

#### Bad Channel Interpolation

Then we will interpolate the bad channel using method implemented in the `MNE` package. The bad channel can be manually selected in GUI.

####  ICA

We use ICA to remove ocular artifact, cardial artifact, muscle movement artifact and other possible artifact. In our own processing, we set the parameter  `ica_n_component` to 40 to make sure we can find all possible artifact. We use `infomax` algorithm. Parameters can be customized base on your preference.

#### Re-reference

Lastly, we will re-reference our data. In our implementation, we use the 'average' method.

 ## Code

### Environment Requirement

We recommand Python 3.10, which is our own setting.

package `MNE`, `mne-bids`, `pybv`are required. You can get these three packages using the following commands:

``` 
conda install --channel=conda-forge mamba
mamba create --override-channels --channel=conda-forge mne
```

```
pip install --upgrade mne-bids[full]
```

```
pip install pybv
```

**Make sure that the full `mne` package is installed using the command above, otherwise you can not using the GUI of the MNE methods correctly. `MNE` version>=1.0 is required to support the GUI qt-browser**. `pybv`==0.7.5 is recommended. For more information, you can turn to these pages: https://mne.tools/stable/install/manual_install.html#manual-install, https://mne.tools/mne-bids/stable/install.html, https://pybv.readthedocs.io/en/stable/.

### Code Usage

In the code `preprocessing.py`, you can change the given parameters to pre-process the data with your own setting and **save the raw data and the pre-processed data in BIDS format**.

This code will first cut the eeg data. A short time will be remained before the start of the valid EEG segment. You can assign the time using the parameter `remaining_time_at_beginning`. After cutting, the code will run the main pre-processing pipeline. In the whole pre-processing procedure, there GUI stages will appear. The first one shows all the ICA component sources. You can exclude ones you want to drop by clicking the components. The second one shows the band pass filtered data. In this stage, you can select bad channels by clicking the channel as in the first stage. You can also mask possible bad segments of the data by annotating them with label 'bad'. The last stage will show the data after re-reference, which is the last step of the pre-processing. In this stage, you can inspect whether the pre-processed data meets your need.

The detailed information about the parameters are shown below:

| Parameter                   | type  | Explanation                                                  |
| --------------------------- | ----- | ------------------------------------------------------------ |
| eeg_path                    | str   | data path of the unprocessed eeg                             |
| sub_id                      | str   | a string of the id of the subject. Pad 0 if the id has only one digit. |
| ses                         | str   | a string describing the session of the current data. It will be contained in the file name when saving the file. |
| task                        | str   | a string describing the task of the current data. It will be contained in the file name when saving the file. |
| run                         | int   | an integer standing for the run number of the data.          |
| raw_data_root               | str   | the path of your raw data, which is also the root of the whole dataset. |
| filtered_data_root          | str   | the path of your filtered data.                              |
| processed_data_root         | str   | the path of your pre-processed data.                         |
| dataset_name                | str   | name of the dataset, which will be saved in the dataset_description.json. |
| author                      | str   | author of the dataset.                                       |
| line_freq                   | float | line frequency of the data. This is needed when saving the data into BIDS format.                   Default to be 50. |
| low_pass_freq               | float | the low pass frequency of the filter                         |
| high_pass_freq              | float | the high pass frequency of the filter                        |
| resample_freq               | float | the resample frequency of the filter                         |
| remaining_time_at_beginning | float | the remaining time before the start of the valid eeg segment |
| montage_name                | str   | the montage of the eeg                                       |
| ica_method                  | str   | which ica_method you want to use. See mne tutorial for more information |
| ica_n_components            | int   | how many ICA components you want to use. See mne tutorial for more information |
| rereference                 | str   | re-reference method you want to use                          |

## Dataset 

You can access our dataset via the ChineseNeuro Symphony community (CHNNeuro) in the Science Data Bank (ScienceDB) platform.

Our data is formatted under the requirement of the BIDS standard format as shown in the figure below. 

The detailed format of our data structure can be found in our paper at 

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/Modality.jpg)

## Manual Processing Criteria

Example Name: subject_04_eeg_01

ICA Example Figure：

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/ica1.png)
![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/ica2.png)

Components to Exclude:

ICA000-009: These component has local maxima in the frontal area, which is a typical feature of eye blink artifacts.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/eye.png)

ICA010-014: These component may represent artifacts of eye movements or eye scanning, as it shows local maxima on the frontal and lateral aspects of the scalp.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/muscle.png)

ICA018: This component has local maxima in the frontal area, which is a typical feature of eye blink artifacts.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/eye4.png)

ICA019: This component may be temporally related to electrocardiographic artifacts, as it exhibits characteristic maxima at the edges of the scalp.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/heart.png)

ICA020: This component has local maxima in the frontal area, which is a typical feature of eye blink artifacts.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/noise.png)

ICA024: This component has local maxima in the frontal area, which is a typical feature of eye blink artifacts.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/eye2.png)

ICA027: This component may be temporally related to electrocardiographic artifacts, as it is characterized by prominent maxima near the ears.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/noise2.png)

ICA034: This component may be related to eye movement and electrocardiographic artifacts, as it exhibits local maxima in the frontal region and near the ears.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/eye3.png)

ICA035: This component may be related to artifacts caused by equipment in the experiment.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/noise3.png)

ICA038: This component may be temporally related to electrocardiographic artifacts, as it exhibits characteristic maxima at the edges of the scalp.

![](https://github.com/ncclab-sustech/ListeningEEG/blob/main/image/noise4.png)
