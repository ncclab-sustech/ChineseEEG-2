'''
Written by: Xinyu Mou

With changes made by Sitong Chen on 2024/11/12:
Defined one chapter per run for novel material.
For previous version, please refer to:
https://github.com/ncclabsustech/Chinese_reading_task_eeg_processing/blob/main/data_preprocessing_and_alignment/README.md
This is for preprocessing the EEG data to BIDS format.
For preprocessing pipeline and usage, please refer to:
https://github.com/ncclab-sustech/ListeningEEG/blob/main/data_preprocessing/README.md
'''


import mne
from mne.preprocessing import ICA
import numpy as np
import argparse
from convert_eeg_to_bids import convert_to_bids


def get_chapter_events(raw):
    """
    Extracts all chapter events (e.g., 'CH01', 'CH02', ...) from the raw annotations.

    :param raw: MNE Raw object
    :return: List of tuples containing (chapter_number, onset_time)
    """
    annotations = raw.annotations
    chapter_events = []
    for desc, onset in zip(annotations.description, annotations.onset):
        if desc.startswith('CH') and desc[2:].isdigit():
            chapter_num = int(desc[2:])
            chapter_events.append((chapter_num, onset))
    # Sort by chapter number
    chapter_events.sort(key=lambda x: x[0])
    return chapter_events


def segment_runs(raw, chapter_events, run_definitions, remaining_time_at_beginning=5):
    """
    Segments the raw data into runs based on chapter events and run definitions.

    :param raw: MNE Raw object
    :param chapter_events: List of tuples containing (chapter_number, onset_time)
    :param run_definitions: Dictionary defining chapters for each run {run_number: (start_chap, end_chap)}
    :param remaining_time_at_beginning: Time to include before the start of the first chapter
    :return: List of tuples containing (run_number, raw_segment, crop_start_time)
    """
    runs = []
    sfreq = raw.info['sfreq']  # Sampling frequency


    for run_num, (start_chap, end_chap) in run_definitions.items():
        # Initialize start_onset and end_onset
        start_onset = None
        end_onset = None

        # Find start and end onsets based on chapter numbers
        for chap_num, onset in chapter_events:
            if chap_num == start_chap:
                start_onset = onset - remaining_time_at_beginning
            if chap_num == end_chap:
                end_onset = onset
                break

        # Handle case where end_chap is None
        if end_chap is None:
            end_onset = raw.times[-1]

        # Check if both onsets were found
        if start_onset is None or end_onset is None:
            print(f"Run {run_num}: Could not find chapters {start_chap} to {end_chap}. Skipping.")
            continue

        # Prevent start_onset from being negative
        if start_onset < 0:
            print(f"Run {run_num}: start_onset {start_onset} is negative. Adjusting to 0.")
            start_onset = 0.0

        # Ensure end_onset does not exceed the last time point minus epsilon
        max_onset = raw.times[-1]
        if end_onset > max_onset:
            print(f"Run {run_num}: end_onset {end_onset} exceeds max_onset {max_onset}. Adjusting to max_onset.")
            end_onset = max_onset

        # Crop the raw data for the run
        run_raw = raw.copy().crop(tmin=start_onset, tmax=end_onset)
        runs.append((run_num, run_raw, start_onset))

    return runs



def read_mff_file(eeg_path, montage_name='GSN-HydroCel-128', preload=False):
    '''
    Read .mff file, set annotations and pick 128 channels, set montage
    '''
    raw = mne.io.read_raw_egi(eeg_path)
    events = mne.find_events(raw, shortest_event=1)
    event_id = raw.event_id
    event_desc = {value: key for key, value in event_id.items()}

    annotations = mne.annotations_from_events(events, sfreq=raw.info['sfreq'], event_desc=event_desc)

    raw.set_annotations(annotations)

    raw.pick_types(eeg=True)
    raw.drop_channels(['VREF'])

    montage = mne.channels.make_standard_montage(montage_name)
    raw.set_montage(montage)

    if preload:
        raw = raw.load_data()

    return raw


def create_new_raw(raw, crop_time_at_beginning, montage_name='GSN-HydroCel-128', preload=False):
    '''
    Create a raw object which can be saved as BrainVision format without losing annotation information

    :param crop_time_at_beginning: the time of the crop point
    '''
    # Get raw data and annotations
    data = raw.get_data()
    annotations = raw.annotations
    onset = annotations.onset
    duration = annotations.duration
    description = annotations.description

    # Create new annotations by adjusting onsets
    new_onset = onset - crop_time_at_beginning

    # Define valid onset range
    sfreq = raw.info['sfreq']
    epsilon = 1.0 / sfreq
    valid_onset_min = 0.0
    valid_onset_max = raw.times[-1] - epsilon

    # Identify valid annotations
    valid_idx = (new_onset >= valid_onset_min) & (new_onset <= valid_onset_max)

    # Print diagnostic message if any annotations are out of range
    if not np.all(valid_idx):
        num_invalid = np.sum(~valid_idx)
        print(f"create_new_raw: Removing {num_invalid} annotations outside the valid range [{valid_onset_min}, {valid_onset_max}].")

    # Filter annotations to keep only valid ones
    new_onset = new_onset[valid_idx]
    new_duration = duration[valid_idx]
    new_description = np.array(description)[valid_idx]

    # Create new Annotations object
    new_annotations = mne.Annotations(onset=new_onset, duration=new_duration,
                                      description=new_description)

    # Create new Raw object
    new_raw = mne.io.RawArray(data, raw.info)
    new_raw.set_annotations(new_annotations)

    # Set montage
    montage = mne.channels.make_standard_montage(montage_name)
    new_raw.set_montage(montage)

    if preload:
        new_raw = new_raw.load_data()

    return new_raw



def process_single_run(run_num, raw, crop_start_time, args, run_output_root):
    '''
    Process and save a single run of EEG data.

    :param run_num: The run number (e.g., 1 or 2)
    :param raw: MNE Raw object for the run
    :param crop_start_time: Time to crop from the beginning
    :param args: Parsed command-line arguments
    :param run_output_root: Root directory to save the run data
    '''
    print(f'-------------------- Processing Run {run_num} --------------------')

    convert_to_bids(raw, ica_component=None, ica_topo_figs=None, ica_dict=None, bad_channel_dict=None,
                    sub_id=args.sub_id, ses=args.ses, task=args.task, run=run_num,
                    bids_root=args.raw_data_root, dataset_name=args.dataset_name,
                    dataset_type='raw', author=args.author, line_freq=args.line_freq)

    raw.info["bads"].extend(args.bad_channels)
    raw = raw.interpolate_bads()

    print('-------------------- raw interpolated --------------------')

    # Downsample
    raw.resample(args.resample_freq)
    print('-------------------- raw resampled --------------------')

    # Notch filter
    raw = raw.notch_filter(freqs=(args.line_freq))
    print('-------------------- notch filter finished --------------------')

    # Band pass filter
    raw = raw.filter(l_freq=args.low_pass_freq, h_freq=args.high_pass_freq)
    print('-------------------- band pass filter finished --------------------')

    # Create new raw with adjusted annotations
    filt_raw = create_new_raw(raw=raw, crop_time_at_beginning=crop_start_time,
                              montage_name=args.montage_name, preload=False)

    convert_to_bids(filt_raw, ica_component=None, ica_topo_figs=None, ica_dict=None,
                    bad_channel_dict=None, sub_id=args.sub_id, ses=args.ses,
                    task=args.task, run=run_num, bids_root=args.filtered_data_root,
                    dataset_name=args.dataset_name, dataset_type='derivative',
                    author=args.author, line_freq=args.line_freq)

    print('-------------------- filtering finished --------------------')

    # Plot to mark bad electrodes
    raw.plot(block=True)

    bad_channels = raw.info['bads']
    print('bad_channels: ', bad_channels)

    bad_channel_dict = {'bad channels': bad_channels}

    # Bad channel interpolation
    raw = raw.interpolate_bads()
    print('-------------------- bad channels interpolated --------------------')

    # raw.set_annotations(Annotations([], [], []))
    # ICA
    ica = ICA(n_components=args.ica_n_components, max_iter='auto', method=args.ica_method, random_state=97)
    ica.fit(raw, reject_by_annotation=True)

    ica_components = ica.get_sources(raw).get_data()
    ica.plot_sources(raw, show_scrollbars=False, block=True)
    ica_topo_figs = ica.plot_components()

    print('exclude ICA components: ', ica.exclude)

    ica_dict = {'shape': ica_components.shape, 'exclude': ica.exclude}

    ica.apply(raw)
    print('-------------------- ICA finished --------------------')

    # Re-reference
    raw.set_eeg_reference(ref_channels=args.rereference)
    print('-------------------- rereference finished --------------------')

    # Plot final data
    raw.plot(block=True)

    # Create preprocessed raw
    preproc_raw = create_new_raw(raw=raw, crop_time_at_beginning=crop_start_time,
                                 montage_name=args.montage_name, preload=False)

    convert_to_bids(preproc_raw, ica_component=ica_components, ica_topo_figs=ica_topo_figs,
                    ica_dict=ica_dict, bad_channel_dict=bad_channel_dict, sub_id=args.sub_id,
                    ses=args.ses, task=args.task, run=run_num, bids_root=args.processed_data_root,
                    dataset_name=args.dataset_name, dataset_type='derivative',
                    author=args.author, line_freq=args.line_freq)


def process_eeg_segments(eeg_path, args):
    """
    Main processing function to handle segmentation and processing of runs.

    :param eeg_path: Path to the EEG .mff file
    :param args: Parsed command-line arguments
    """
    raw = read_mff_file(eeg_path=eeg_path, montage_name=args.montage_name, preload=True)

    # Get all chapter events
    chapter_events = get_chapter_events(raw)
    if not chapter_events:
        print("No chapter events found. Exiting.")
        return

    # Define runs: run_number: (start_chapter, end_chapter)
    if args.ses == "littleprince":
        run_definitions = {
            1_1: (1, 2),
            1_2: (2, 3),
            1_3: (3, 4),
            1_4: (4, 5),
            1_5: (5, 6),
            1_6: (6, 7),
            1_7: (7, 8),
            1_8: (8, 9),
            1_9: (9, 10),
            1_10: (10, 11),
            1_11: (11, 12),
            1_12: (12, 13),
            1_13: (13, 14),
            1_14: (14, 15),
            2_1: (15, 16),
            2_2: (16, 17),
            2_3: (17, 18),
            2_4: (18, 19),
            2_5: (19, 20),
            2_6: (20, 21),
            2_7: (21, 22),
            2_8: (22, 23),
            2_9: (23, 24),
            2_10: (24, 25),
            2_11: (25, 26),
            2_12: (26, 27),
            2_13: (27, None),
        }
    if args.ses == "garnettdream":
        run_definitions = {
            1_1: (1, 2),
            1_2: (2, 3),
            1_3: (3, 4),
            1_4: (4, 5),
            1_5: (5, 6),
            2_1: (6, 7),
            2_2: (7, 8),
            2_3: (8, 9),
            2_4: (9, None),
            
        }

    # Segment the runs
    runs = segment_runs(raw, chapter_events, run_definitions,
                        remaining_time_at_beginning=args.remaining_time_at_beginning)

    if not runs:
        print("No runs to process. Exiting.")
        return

    for run_num, run_raw, crop_start_time in runs:
        process_single_run(run_num, run_raw, crop_start_time, args, run_output_root=args.processed_data_root)


def main():
    parser = argparse.ArgumentParser(description='Parameters that can be changed in this experiment')
    parser.add_argument('--eeg_path', type=str, default=r'/example/path')
    parser.add_argument('--sub_id', type=str, default='01')
    parser.add_argument('--ses', type=str, default='littleprince')
    parser.add_argument('--task', type=str, default='lis')
    # Removed 'run' argument as runs are now determined automatically
    parser.add_argument('--raw_data_root', type=str, default='example_bids')
    parser.add_argument('--filtered_data_root', type=str, default='example_bids/derivatives/filtered')
    parser.add_argument('--processed_data_root', type=str, default='example_bids/derivatives/preprocessed')
    parser.add_argument('--dataset_name', type=str, default='Chinese Novel Reading')
    parser.add_argument('--author', type=str, default='Sitong Chen, Dongyang Li, Cuilin He, Beiqianyi Li')
    parser.add_argument('--line_freq', type=float, default=50)
    # Removed 'start_chapter' argument as chapters are handled automatically
    parser.add_argument('--low_pass_freq', type=float, default=1)
    parser.add_argument('--high_pass_freq', type=float, default=40)
    parser.add_argument('--resample_freq', type=float, default=250)
    parser.add_argument('--remaining_time_at_beginning', type=float, default=5)
    parser.add_argument('--bad_channels', type=list, default=[])  # e.g. ['E1', 'E2']
    parser.add_argument('--montage_name', type=str, default='GSN-HydroCel-128')
    parser.add_argument('--ica_method', type=str, default='infomax')
    parser.add_argument('--ica_n_components', type=int, default=40)
    parser.add_argument('--rereference', type=str, default='average')

    args = parser.parse_args()

    process_eeg_segments(eeg_path=args.eeg_path, args=args)


if __name__ == "__main__":
    main()
