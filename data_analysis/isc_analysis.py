import os
import numpy as np
import pandas as pd
import mne
from scipy import stats
from itertools import combinations
from collections import defaultdict
import multiprocessing as mp
from multiprocessing import Pool
import cupy as cp
from scipy.signal import hilbert
import random

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

INPUT_BASE = "../data/frequency"  
OUTPUT_BASE = "output_path"
FREQUENCY_BANDS = ['Delta', 'Theta', 'Alpha', 'Beta']
BONFERRONI_P_THRESH = 1e-6
NUM_PROCESSES = 3  


def analyze_band_proportions(significant_chs, band, total_common_chs):

    significant_count = len(significant_chs)
    proportion = significant_count / total_common_chs if total_common_chs > 0 else 0
    
    return {
        "band": band,
        "total_common_chs": total_common_chs,
        "significant_count": significant_count,
        "proportion": proportion,
    }

def extract_epoch_data(raw, event_groups):
    if not event_groups:
        print("no valid event groups found")
        return None

    first_group = event_groups[0]
    last_group = event_groups[-1]
    
    start_sample = first_group['rows_sample']
    end_sample = last_group['rowe_sample']
    sfreq = raw.info['sfreq']

    tmin = start_sample / sfreq
    tmax = end_sample / sfreq

    try:
        epoch_raw = raw.copy().crop(tmin=tmin, tmax=tmax, include_tmax=True)
        return epoch_raw
    except Exception as e:
        print(f"data processing failed: {e}")
        return None


def align_data_based_on_events(subj1_data, subj2_data, subj1_event_data, subj2_event_data, common_chs):

    subj1_events = subj1_event_data.get('event_groups', [])
    subj2_events = subj2_event_data.get('event_groups', [])
    subj1_sfreq = subj1_event_data.get('sfreq', None)
    subj2_sfreq = subj2_event_data.get('sfreq', None)
    
    if subj1_sfreq and subj2_sfreq and subj1_sfreq != subj2_sfreq:
        print("unmatching sampling rates")
        return None, {
            "alignment_method": "sampling_rate_mismatch",
            "subj1_sfreq": subj1_sfreq,
            "subj2_sfreq": subj2_sfreq
        }

    if not subj1_events or not subj2_events:
        print("no events found in one or both subjects")
        return None, {
            "alignment_method": "no_events_found",
            "subj1_event_count": len(subj1_events),
            "subj2_event_count": len(subj2_events),
            "subj1_event_source": subj1_event_data.get('source', 'unknown'),
            "subj2_event_source": subj2_event_data.get('source', 'unknown')
        }
    
    subj1_start = subj1_events[0]['rows_sample']
    subj1_end = subj1_events[-1]['rowe_sample']
    subj2_start = subj2_events[0]['rows_sample']
    subj2_end = subj2_events[-1]['rowe_sample']
    subj1_length = subj1_end - subj1_start
    subj2_length = subj2_end - subj2_start
    min_length = min(subj1_length, subj2_length)
    aligned_data = {}
    alignment_info = {
        "alignment_method": "event_based",
        "subj1_event_range": {"start": subj1_start, "end": subj1_end, "length": subj1_length},
        "subj2_event_range": {"start": subj2_start, "end": subj2_end, "length": subj2_length},
        "aligned_length": min_length
    }
    
    for ch in common_chs:
        subj1_ch_data = subj1_data.get(ch, np.array([]))
        subj2_ch_data = subj2_data.get(ch, np.array([]))
        if len(subj1_ch_data) < min_length or len(subj2_ch_data) < min_length:
            print(f"Warning: {ch} has not enough data for alignment")
            continue
        aligned_data[ch] = {
            "subj1": subj1_ch_data[:min_length],
            "subj2": subj2_ch_data[:min_length]
        }
    
    return aligned_data, alignment_info

def find_bids_events_file(bids_root, subject, session, task, run):

    events_fname = f"sub-{subject}_ses-{session}_task-{task}_run-{run}_events.tsv"
    events_path = os.path.join(
        bids_root,
        f"sub-{subject}",
        f"ses-{session}",
        "eeg",
        events_fname
    )
    
    if os.path.exists(events_path):
        print(f"Found events path: {events_path}")
        return events_path
    
    print(f"Not found: {events_path}")
    return None
def load_subject_data(subject, session, run, band, bids_root, task):
    data_dir = os.path.join(INPUT_BASE, f"{subject}_electrode", band)
    electrode_data = {}
    
    for fname in os.listdir(data_dir):
        if f"{subject}_{session}_{run}_{band}" in fname and "_envelope.npy" in fname:
            ch_name = fname.split("_")[-2]
            file_path = os.path.join(data_dir, fname)
            electrode_data[ch_name] = np.load(file_path)
    
    event_data = {}
    vhdr_path = find_bids_vhdr_file(bids_root, subject, session, task, run)
    events_path = find_bids_events_file(bids_root, subject, session, task, run)
    
    if vhdr_path and os.path.exists(vhdr_path):
        try:
            raw = mne.io.read_raw_brainvision(vhdr_path, preload=True)
            sfreq = raw.info['sfreq']
            events_from_vhdr = None
            try:
                events_from_vhdr = mne.events_from_annotations(raw)
                print(f"reading {len(events_from_vhdr[0])} events")
            except Exception as e:
                print(f"Failed reading events: {e}")
            
            events_from_tsv = None
            if events_path and os.path.exists(events_path):
                try:
                    events_df = pd.read_csv(events_path, sep='	')
                    rows_events = events_df[events_df['trial_type'].str.lower().str.contains('rows', na=False)]
                    rowe_events = events_df[events_df['trial_type'].str.lower().str.contains('rowe', na=False)]
                    rows_samples = (rows_events['onset'] * sfreq).round().astype(int).tolist()
                    rowe_samples = (rowe_events['onset'] * sfreq).round().astype(int).tolist()
                    event_groups = []
                    min_length = min(len(rows_samples), len(rowe_samples))
                    
                    for i in range(min_length):
                        event_groups.append({
                            'group_id': i + 1,
                            'rows_sample': rows_samples[i],
                            'rowe_sample': rowe_samples[i]
                        })
                    
                    events_from_tsv = {
                        'event_groups': event_groups,
                        'sfreq': sfreq,
                        'ch_names': raw.ch_names,
                        'source': 'tsv_file'
                    }
                 
                except Exception as e:
                    print(f"Failed reading events: {e}")
            
            if events_from_tsv:
                event_data = events_from_tsv
            elif events_from_vhdr:

                events, event_id = events_from_vhdr
                rows_mask = np.array([str(k).lower().startswith('rows') for k in event_id.keys()])
                rowe_mask = np.array([str(k).lower().startswith('rowe') for k in event_id.keys()])
                
                rows_codes = np.array(list(event_id.values()))[rows_mask]
                rowe_codes = np.array(list(event_id.values()))[rowe_mask]
                
                rows_samples = events[np.isin(events[:, 2], rows_codes), 0].tolist()
                rowe_samples = events[np.isin(events[:, 2], rowe_codes), 0].tolist()

                event_groups = []
                min_length = min(len(rows_samples), len(rowe_samples))
                
                for i in range(min_length):
                    event_groups.append({
                        'group_id': i + 1,
                        'rows_sample': rows_samples[i],
                        'rowe_sample': rowe_samples[i]
                    })
                
                event_data = {
                    'event_groups': event_groups,
                    'sfreq': sfreq,
                    'ch_names': raw.ch_names,
                    'source': 'vhdr_annotations'
                }
            else:
                print("Did not read any events")
                event_data = {'event_groups': [], 'sfreq': sfreq, 'ch_names': raw.ch_names, 'source': 'no_events'}
            
            if event_data['event_groups']:
                epoch_raw = extract_epoch_data(raw, event_data['event_groups'])
                if epoch_raw is not None:
                    epoch_data = epoch_raw.get_data()
                    ch_names = epoch_raw.ch_names

                    for i, ch in enumerate(ch_names):
                        if ch in electrode_data:
                            electrode_data[ch] = electrode_data[ch][:len(epoch_data[i])]
                    event_data.update({
                        'start_sample': event_data['event_groups'][0]['rows_sample'],
                        'end_sample': event_data['event_groups'][-1]['rowe_sample'],
                        'data_length': len(epoch_data[0]) if epoch_data.size > 0 else 0
                    })
            
        except Exception as e:
            print(f"Failed loading data: {e}")
            event_data = {'event_groups': [], 'sfreq': None, 'ch_names': [], 'source': 'load_failure'}
    else:
        print(f"{subject} vhdr not found")
        event_data = {'event_groups': [], 'sfreq': None, 'ch_names': [], 'source': 'file_not_found'}
    
    event_data['source_file'] = vhdr_path
    event_data['events_file'] = events_path
    
    return {
        'electrode_data': electrode_data,
        'event_data': event_data
    }
def find_bids_vhdr_file(bids_root, subject, session, task, run):
    vhdr_fname = f"sub-{subject}_ses-{session}_task-{task}_run-{run}_eeg.vhdr"
    vhdr_path = os.path.join(
        bids_root,
        f"sub-{subject}",
        f"ses-{session}",
        "eeg",
        vhdr_fname
    )
    
    if os.path.exists(vhdr_path):
        return vhdr_path
    
    print(f"BIDS not found: {vhdr_path}")
    return None



def extract_envelope_gpu(signal_data):
    if not GPU_AVAILABLE or len(signal_data) < 100:
        from scipy.signal import hilbert
        try:
            analytic_signal = hilbert(signal_data)
            envelope = np.abs(analytic_signal)
            return envelope
        except Exception as e:
            return signal_data
    
    try:
        signal_gpu = cp.asarray(signal_data)
        N = len(signal_gpu)
        if N < 2:
            return cp.asnumpy(signal_gpu)
        fft_signal = cp.fft.fft(signal_gpu)
        h = cp.zeros(N)
        if N % 2 == 0:
            h[0] = h[N // 2] = 1
            h[1:N // 2] = 2
        else:
            h[0] = 1
            h[1:(N + 1) // 2] = 2
        analytic_signal = cp.fft.ifft(fft_signal * h)
        envelope = cp.abs(analytic_signal)
        return cp.asnumpy(envelope)
        
    except Exception as e:

        from scipy.signal import hilbert
        analytic_signal = hilbert(signal_data)
        return np.abs(analytic_signal)

def create_time_shifted_data_gpu(signal_data, num_shuffles=500):

    if not GPU_AVAILABLE or len(signal_data) < 100:
        return create_time_shifted_data_cpu(signal_data, num_shuffles)
    
    try:
        signal_gpu = cp.asarray(signal_data)
        signal_length = len(signal_gpu)
        
        if signal_length < 2:
            return [cp.asnumpy(signal_gpu)] * num_shuffles
        
        shift_points = cp.random.randint(1, signal_length, size=num_shuffles)
        
        shuffled_signals = []
        for shift_point in shift_points:
            shifted_signal = cp.concatenate([
                signal_gpu[shift_point:],
                signal_gpu[:shift_point]
            ])
            shuffled_signals.append(cp.asnumpy(shifted_signal))
        
        return shuffled_signals
        
    except Exception as e:
        return create_time_shifted_data_cpu(signal_data, num_shuffles)

def create_time_shifted_data_cpu(signal_data, num_shuffles=500):
    shuffled_signals = []
    signal_length = len(signal_data)
    
    if signal_length < 2:
        return [signal_data] * num_shuffles
    
    for _ in range(num_shuffles):
        shift_point = random.randint(1, signal_length - 1)
        shifted_signal = np.concatenate([
            signal_data[shift_point:],
            signal_data[:shift_point]
        ])
        shuffled_signals.append(shifted_signal)
    
    return shuffled_signals

def pearson_correlation_gpu(x, y):
    if not GPU_AVAILABLE or len(x) < 100:
        return stats.pearsonr(x, y)
    
    try:
        x_gpu = cp.asarray(x)
        y_gpu = cp.asarray(y)
        
        mean_x = cp.mean(x_gpu)
        mean_y = cp.mean(y_gpu)
        
        x_centered = x_gpu - mean_x
        y_centered = y_gpu - mean_y
        
        numerator = cp.sum(x_centered * y_centered)
        denominator = cp.sqrt(cp.sum(x_centered**2) * cp.sum(y_centered**2))
        
        if denominator == 0:
            return 0.0, 1.0
        
        r = numerator / denominator
        n = len(x)
        if n < 3:
            p = 1.0
        else:
            t_stat = r * cp.sqrt((n-2)/(1-r**2 + 1e-10))
            p = 2 * (1 - stats.t.cdf(abs(float(t_stat)), n-2))
        
        return float(r), float(p)
        
    except Exception as e:
        return stats.pearsonr(x, y)

def calculate_electrode_correlation_worker(args):
    ch, data1_aligned, data2_aligned, subj2_event_data = args
    
    result = {
        "channel": ch,
        "original": {"r": 0, "p": 1, "method": "envelope_correlation"},
        "random": {"method": "time_shift_shuffle", "statistics": {}},
        "noise": {"r": 0, "p": 1, "method": "envelope_correlation"}
    }
    
    try:
        # 1. correlation of original data
        if len(data1_aligned) > 1 and len(data2_aligned) > 1:
            envelope1 = extract_envelope_gpu(data1_aligned)
            envelope2 = extract_envelope_gpu(data2_aligned)
            
            orig_r, orig_p = pearson_correlation_gpu(envelope1, envelope2)
            result["original"]["r"] = orig_r
            result["original"]["p"] = orig_p
        else:
            envelope1, envelope2 = np.array([]), np.array([])
        
        # 2. time shift shuffle
        if len(envelope2) > 1:
            shifted_signals = create_time_shifted_data_gpu(data2_aligned, num_shuffles=500)
            
            rand_r_values = []
            rand_p_values = []
            
            for shifted_signal in shifted_signals:
                shifted_envelope = extract_envelope_gpu(shifted_signal)
                min_len = min(len(envelope1), len(shifted_envelope))
                
                if min_len > 1:
                    r_val, p_val = pearson_correlation_gpu(
                        envelope1[:min_len], 
                        shifted_envelope[:min_len]
                    )
                    rand_r_values.append(r_val)
                    rand_p_values.append(p_val)
                else:
                    rand_r_values.append(0)
                    rand_p_values.append(1)
            
            result["random"]["statistics"] = {
                "r_mean": float(np.mean(rand_r_values)) if rand_r_values else 0,
                "r_std": float(np.std(rand_r_values)) if rand_r_values else 0,
                "r_min": float(np.min(rand_r_values)) if rand_r_values else 0,
                "r_max": float(np.max(rand_r_values)) if rand_r_values else 0,
                "p_mean": float(np.mean(rand_p_values)) if rand_p_values else 1,
                "num_shuffles": len(rand_r_values)
            }
        
        # 3. noise
        if len(envelope2) > 1:
            sfreq = subj2_event_data.get('sfreq', 1000)
            window_size = max(int(0.1 * sfreq), 10)
            overlap = int(window_size * 0.5)
            
            noise = np.zeros_like(data2_aligned)
            n_samples = len(data2_aligned)
            start = 0
            
            while start < n_samples:
                end = min(start + window_size, n_samples)
                window_data = data2_aligned[start:end]
                
                local_mean = np.mean(window_data)
                local_std = max(np.std(window_data), 1e-6)
                
                window_noise = np.random.normal(
                    loc=local_mean,
                    scale=local_std,
                    size=len(window_data)
                )
                
                if start == 0:
                    noise[start:end] = window_noise
                else:
                    noise[start:end] = (noise[start:end] + window_noise) / 2
                
                start += window_size - overlap
            
            # extract noise envelope
            noise_envelope = extract_envelope_gpu(noise)
            min_len = min(len(envelope1), len(noise_envelope))
            
            if min_len > 1:
                noise_r, noise_p = pearson_correlation_gpu(
                    envelope1[:min_len], 
                    noise_envelope[:min_len]
                )
                result["noise"]["r"] = noise_r
                result["noise"]["p"] = noise_p
        
    except Exception as e:
        print(f"{ch}calculation failed: {e}")
    
    return result

def calculate_pair_correlation_parallel(subj1_data, subj2_data, subj1_event_data, subj2_event_data, common_chs):
    subj1_electrode = subj1_data['electrode_data']
    subj2_electrode = subj2_data['electrode_data']

    work_args = []
    for ch in common_chs:
        aligned_data, alignment_info = align_data_based_on_events(
            subj1_electrode, 
            subj2_electrode,
            subj1_event_data,
            subj2_event_data,
            [ch]
        )
        
        if aligned_data is None or ch not in aligned_data:
            data1 = subj1_electrode.get(ch, np.array([]))
            data2 = subj2_electrode.get(ch, np.array([]))
            
            if len(data1) != len(data2):
                min_len = min(len(data1), len(data2))
                data1_aligned = data1[:min_len]
                data2_aligned = data2[:min_len]
            else:
                data1_aligned = data1
                data2_aligned = data2
        else:
            data1_aligned = aligned_data[ch]["subj1"]
            data2_aligned = aligned_data[ch]["subj2"]
        
        work_args.append((ch, data1_aligned, data2_aligned, subj2_event_data))
    
    with Pool(processes=NUM_PROCESSES) as pool:
        results = pool.map(calculate_electrode_correlation_worker, work_args)

    correlation_results = {}
    for result in results:
        ch = result["channel"]
        correlation_results[ch] = {
            "original": result["original"],
            "random": result["random"],
            "noise": result["noise"]
        }
    
    return correlation_results

def process_session_run_parallel(task, session, run, subjects, bids_root):
    output_dir = os.path.join(OUTPUT_BASE, task, session, run)
    os.makedirs(output_dir, exist_ok=True)
    
    all_subj_data = {}
    for subj in subjects:
        subj_data = {}
        for band in FREQUENCY_BANDS:
            subj_data[band] = load_subject_data(subj, session, run, band, bids_root, task)
        all_subj_data[subj] = subj_data
    
    all_pairs = list(combinations(subjects, 2))
    
    for (subj1, subj2) in all_pairs:
        pair_key = f"{subj1}_{subj2}"
        pair_results = {
            "subjects": [subj1, subj2],
            "bands": {}
        }
        
        print(f"processing : {pair_key}")
        
        for band in FREQUENCY_BANDS:
            print(f"processing band: {band}")
            
            subj1_data = all_subj_data[subj1][band]
            subj2_data = all_subj_data[subj2][band]
            
            subj1_chs = set(subj1_data['electrode_data'].keys())
            subj2_chs = set(subj2_data['electrode_data'].keys())
            common_chs = list(subj1_chs & subj2_chs)
            
            if not common_chs:
                print(f"Warning: {pair_key} has no common electrode at {band} band")
                continue
            
            corr_data = calculate_pair_correlation_parallel(
                subj1_data, 
                subj2_data,
                subj1_data['event_data'],
                subj2_data['event_data'],
                common_chs
            )
            
            significant_chs = [
                ch for ch in common_chs 
                if corr_data[ch]["original"]["p"] < BONFERRONI_P_THRESH
            ]
            
            band_stats = analyze_band_proportions(significant_chs, band, len(common_chs))
            
            pair_results["bands"][band] = {
                "correlation": corr_data,
                "significant_chs": significant_chs,
                "common_ch_count": len(common_chs),
                "statistics": band_stats
            }
            
            print(f"Band {band}: {len(common_chs)} common elextrodes, {len(significant_chs)} correlated electrodes")
        
        pair_npy_path = os.path.join(output_dir, f"{session}_{run}_{pair_key}_correlation.npy")
        np.save(pair_npy_path, pair_results)
        
        print(f"Storage Finish: Session {session} | Run {run} | subject {pair_key}")

def main(bids_params):
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    for session in bids_params["sessions"]:
        current_runs = bids_params["runs"] if session == "littleprince" else bids_params.get("runs2", [])
        for run in current_runs:
            subjects = bids_params["subjects"]
            task = bids_params["task"]
            process_session_run_parallel(task, session, run, subjects, bids_params["bids_root"])

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    analysis_params = {
        "bids_root": "bids_data", 
        "sessions": ["littleprince","garnettdream"],   
        "runs": ["runs1", "runs2"], 
        "runs2":["runs1", "runs2"],
        "subjects": ["subj1", "subj2"],            
        "task": "reading"                                       
    }
    main(analysis_params)
