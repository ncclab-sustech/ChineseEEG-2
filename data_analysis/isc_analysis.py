"""
Written by Sitong Chen
This code contains function for Inter-subject correlation analysis
"""
import os
import random
import numpy as np
import matplotlib.pyplot as plt
import mne
from sklearn.preprocessing import StandardScaler
from sklearn.cross_decomposition import CCA


def train_on_one_subject(data_tra, train_subj_dat, subject1, n_components):
    """
    Train CCA on one subject and return the spatial filters (W).
    Also return the fitted scaler.
    """
    subject_data_1 = train_subj_dat[subject1]
    X_1 = subject_data_1.T  # Transpose for CCA (n_samples, n_channels)
    cca = CCA(n_components=n_components)
    scaler = StandardScaler()
    W_list = {}
    scaler_list = {}
    for subj, subj_data in data_tra.items():
        Y = subj_data.T  # Transpose for (n_samples, n_channels)
        cca = CCA(n_components=n_components)
        cca.fit(X_1, Y)  # Fit CCA
        W_avg = cca.x_weights_  # Return the spatial filter
        W_avg = W_avg[:, -3:]  # Slice to get the last 3 components
        W_list[subj] = W_avg
        scaler_list[subj] = scaler
    return W_list, scaler_list


def test_on_other_subjects(data_test, train_subj_data, W_avg_lis, n_components):
    """
    Test the spatial filter W_avg on all other subjects' data and compute average ISC and variance, using only the last 5 components.
    """
    all_components = []
    all_components_X = []
    for subj,subj_data in train_subj_data.items():
        train = subj_data.T

    for subj, subj_data in data_test.items():
        W_avg = W_avg_lis[subj]
        Y = subj_data.T  # Transpose for (n_samples, n_channels)
        X_c = np.dot(Y, W_avg)
        train_X = np.dot(train, W_avg)  # Canonical components
        all_components.append(X_c)
        all_components_X.append(train_X)
    all_components_X = np.array(all_components_X)
    all_components_X = all_components_X[:, :, -3:]  # Use last 3 components

    all_components = np.array(all_components)
    all_components = all_components[:, :, -3:]  # Use last 3 components
    print(all_components.size)
    print(all_components_X.size)

    isc_values = []
    for subj_index, subj_components in enumerate(all_components):
        # Directly use the index to access the corresponding X_component
        X_component = all_components_X[subj_index]
        print(X_component.shape)

        for i in range(3):
            component = subj_components[:, i]
            print(component.shape)
            X = X_component[:, i]
            isc = np.corrcoef(component, X)[0, 1]
            isc_values.append(isc)

    isc_mean = np.mean(isc_values)
    isc_variance = np.var(isc_values)

    return isc_mean, isc_variance


def combine_data(all_data):
    """
    Combines data from different tasks (BIDS folders) into one dictionary.
    Assumes data from all tasks is aligned by subject ID.
    """
    combined_data = {}

    # Merge data from both tasks
    for task_data in all_data.values():
        for subj, data in task_data.items():
            if subj not in combined_data:
                combined_data[subj] = []
            combined_data[subj].append(data)

    # Now, combine the data for each subject into a single array (e.g., concatenation)
    for subj, data_list in combined_data.items():
        combined_data[subj] = np.concatenate(data_list, axis=1)  # Concatenate along the time axis

    return combined_data


def run_isc_analysis_single_subject_training(
        bids_paths, subject_mapping, tasks, session, run, sfreq, start_sec, end_sec, n_components, run_list
        , W=None):
    """
    Train on one subject and test on all other subjects.
    The function now processes data from both BIDS folders and combines them.
    """
    all_data = {}
    # Load and preprocess data from both BIDS folders
    for bids_path, subject_list, task in zip(bids_paths, subject_mapping, tasks):
        data = load_bids_data(bids_path, subject_list, session, task, run)
        filtered_data = filter_data(data, sfreq)
        prepared_data = prepare_data_for_cca(filtered_data, start_sec, end_sec, sfreq)
        all_data[task] = prepared_data

    # Combine the data from both folders
    combined_data = combine_data(all_data)

    isc_results = {}  # Store ISC results for each subject as the training subject
    isc_variance = {}  # Store variance for each subject

    subjects = list(combined_data.keys())

    for train_subj in subjects:
        print(f"Training on Subject {train_subj}...")

        for run_train in run_list:
            n = run_list.index(run_train)
            all_data_train = {}
            # Load and preprocess data from both BIDS folders
            for bids_path, subject_list, task in zip(bids_paths, subject_mapping, tasks):
                data_t = load_bids_data(bids_path, subject_list, session, task, run_train)
                filtered_data_t = filter_data(data_t, sfreq)
                prepared_data_t = prepare_data_for_cca(filtered_data_t, start_sec, end_sec, sfreq)
                all_data_train[task] = prepared_data_t
                # Combine the data from both folders
                combined_data_train = combine_data(all_data_train)

            # Prepare training data (train_subj) and testing data (all others)
            data_train = {subj: combined_data_train[subj] for subj in subjects if subj != train_subj}
            tra_subj_dat = {train_subj: combined_data_train[train_subj]}
            # Train on one subject and get the spatial filters (W_avg) and scaler
            W_avg_lis, scaler_lis = train_on_one_subject(data_train, tra_subj_dat, train_subj, n_components)

            print(n)
            if n == 0:
                W_avg_dic_all = W_avg_lis
            else:
                for subj in subjects:
                    if subj != train_subj:
                        W_avg_dic_all[subj] += W_avg_lis[subj]

        W_avg_dic_all = {subj: W_avg_dic_all[subj] / len(run_list) for subj in subjects if subj != train_subj}

        data_test = {subj: combined_data[subj] for subj in subjects if subj != train_subj}
        train_subj_data = {train_subj: combined_data[train_subj]}
        
        avg_isc, isc_var = test_on_other_subjects(data_test, train_subj_data, W_avg_lis, n_components)
        isc_results[train_subj] = avg_isc
        isc_variance[train_subj] = isc_var / len(data_test)
    return isc_results


def load_bids_data(bids_path, subjects, session, task, run):
    """
    Load EEG data in BIDS format using MNE.
    """
    data = {}

    for subj in subjects:
        vhdr_path = os.path.join(
            bids_path,
            f"sub-{subj}",
            f"ses-{session}",
            "eeg",
            f"sub-{subj}_ses-{session}_task-{task}_run-{run}_eeg.vhdr",
        )
        if not os.path.exists(vhdr_path):
            raise FileNotFoundError(f"File not found: {vhdr_path}")
        raw = mne.io.read_raw_brainvision(vhdr_path, preload=True)
        raw.pick_types(eeg=True)
        data[subj] = raw.get_data()  # Ensure this is a 2D array
    return data


def filter_data(data, sfreq, l_freq=1.0):
    """
    Band-pass filter the data to retain only frequencies above 1Hz.
    """
    filtered_data = {}

    for subj, subj_data in data.items():
        # Ensure the data is 2D and contains the correct shape
        if subj_data.ndim != 2:
            raise ValueError(f"Subject {subj} data is not 2D. Shape: {subj_data.shape}")

        # Create RawArray object for filtering
        n_channels = subj_data.shape[0]  # Number of channels based on data shape
        raw = mne.io.RawArray(subj_data, mne.create_info(n_channels, sfreq, ch_types="eeg"))
        raw.filter(l_freq=l_freq, h_freq=None, method="iir")

        # Store filtered data
        filtered_data[subj] = raw.get_data()

    return filtered_data


def prepare_data_for_cca(data_dict, start_sec, end_sec, fs):
    """
    Prepare the data for CCA by selecting a specific time segment.
    """
    subjects = list(data_dict.keys())
    start_sample = int(start_sec * fs)
    end_sample = int(end_sec * fs)

    formatted_data = {}

    for subj in subjects:
        data = data_dict[subj]
        if not isinstance(data, np.ndarray) or data.ndim != 2:
            raise ValueError(f"Subject {subj} has invalid data shape: {getattr(data, 'shape', None)}")
        if end_sample > data.shape[1]:
            raise ValueError(f"End sample ({end_sample}) exceeds the data length for subject {subj}.")
        # Extract the segment
        formatted_data[subj] = data[:, start_sample:end_sample]

    return formatted_data

