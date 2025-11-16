
import numpy as np
import scipy.io
import mne
from mne.preprocessing import ICA
from mne_icalabel import label_components
from sklearn.linear_model import LinearRegression
import os, json, sys
# A channel was defined as a bad electrode when recorded data from that electrode was correlated at <0.85 to an estimate based on other channels 

def detect_bad_channels(raw, thresh=0.85):
  bad_channels = []
  picks = mne.pick_types(raw.info, eeg=True, stim=False)
  data = raw.get_data(picks=picks)
  data = data - data.mean(axis=1, keepdims=True)   # delete mean

  n_channels, n_samples = data.shape
  for i in range(n_channels):
    y = data[i, :] # (n_samples,)
    others = np.delete(data, i, axis=0).T # (n_samples, n_channels-1)

    model = LinearRegression()
    model.fit(others, y)
    y_pred = model.predict(others)

    corr = np.corrcoef(y, y_pred)[0, 1]
    if corr < thresh:
        bad_channels.append(i)


  bads = [raw.ch_names[picks[i]] for i in bad_channels]
  return bads



# A channel was defined as bad if it had more line noise relative to its signal than all other channels (four standard deviations)
def detected_bad_line_noise(raw, line_freq=50, thresh=4):
  picks = mne.pick_types(raw.info, eeg=True, stim=False)
  data = raw.get_data(picks=picks)
  psds, freqs = mne.time_frequency.psd_array_welch(
      data, sfreq=raw.info["sfreq"], n_fft=2048
  )
  bw = 2.0
  mask = (freqs >= line_freq - bw/2) & (freqs <= line_freq + bw/2)  
  line_power = psds[:, mask].mean(axis=1)  
  total_power = psds.mean(axis=1)
  ratio = line_power / total_power
  bad_mask = ratio > ratio.mean() + thresh * ratio.std()
  bads = [raw.ch_names[picks[i]] for i in np.where(bad_mask)[0]]
  return bads, ratio



# If a channel had a longer flat-line than 5 s, it was considered bad
def detect_flatline_channels(raw, flat_sec=5.0):
  sfreq = raw.info['sfreq']                 
  win_size = int(flat_sec * sfreq)          
  picks = mne.pick_types(raw.info, eeg=True, stim=True, exclude='bads')
  data = raw.get_data(picks=picks)

  bads = []
  for i, ch in enumerate([raw.ch_names[p] for p in picks]):
    x = data[i]
    for start in range(0, len(x) - win_size + 1, 1):
      seg = x[start:start + win_size]
      if np.all(seg == seg[0]):
        bads.append(ch)
        break
    print("finish", i)
  return bads


def detect_bad_channels_std(raw, std_thresh=25e-6, artifact_thresh=100e-6, max_loss=0.5):
  """
  detect bad channels: based on std (25 µV); exclude transient large artifacts (>100 µV) 
  if valid data < 50%, this is a bad channel
  """ 

  sfreq = raw.info['sfreq']
  picks = mne.pick_types(raw.info, eeg=True, stim=True, exclude='bads')
  data = raw.get_data(picks=picks)

  bads = []
  for i, ch in enumerate([raw.ch_names[p] for p in picks]):
    x = data[i]

    # remove high-amplitude artifacts
    mask = np.abs(x) < artifact_thresh
    if mask.sum() < (1 - max_loss) * len(x):
      # if valid data < 50%, the channel will be deleted
      bads.append(ch)
      continue

    # calculate std
    std_val = np.std(x[mask])
    if std_val > std_thresh:
      bads.append(ch)

  return bads


def assess_quality(raw, high_amp_thresh=30e-6, high_amp_prop=0.20,
                   var_thresh=15e-6, time_var_prop=0.20,
                   chan_var_prop=0.30, bad_ratio_thresh=0.30):
    
    """
    Input:

    high_amp_thresh: high-amplitude threshold (default 30 µV)
    high_amp_prop: proportion threshold of high-amplitude points
    var_thresh: variance threshold (default 15 µV)
    time_var_prop: proportion threshold of high-variance time points
    chan_var_prop: proportion threshold of high-variance channels
    bad_ratio_thresh: threshold for the proportion of bad channels

    Output:
    is_bad: whether the EEG is classified as poor quality
    reasons: list of conditions indicating poor quality
    """

    picks = mne.pick_types(raw.info, eeg=True, stim=True)
    data = raw.get_data(picks=picks)

    reasons = []

    # 1) high amplitue point proportion
    high_amp_points = np.abs(data) > high_amp_thresh
    if high_amp_points.sum() / data.size > high_amp_prop:
        reasons.append("high amplitue point proportion")

    # 2) high variation of time points
    var_time = np.var(data, axis=0)  # different time points across channels
    if (var_time > var_thresh).mean() > time_var_prop:
        reasons.append("high variation of time points")

    # 3) high variation of channels
    var_chan = np.var(data, axis=1)  # different channels across time
    if (var_chan > var_thresh).mean() > chan_var_prop:
        reasons.append("high variation of channels")

    # 4) proportion of bad channels
    bad_ratio = len(raw.info['bads']) / len(picks)
    if bad_ratio > bad_ratio_thresh:
        reasons.append("proportion of bad channels")

    is_bad = len(reasons) > 0

    return is_bad, reasons

