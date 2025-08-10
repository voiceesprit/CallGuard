import sys
import os
import torch
import soundfile as sf
import librosa  # for resampling if needed
import io

sys.path.append(os.path.join(os.path.dirname(__file__), "aasist"))
from models.AASIST import Model

# Load model once globally
d_args = {
    "architecture": "AASIST",
    "nb_samp": 64600,
    "first_conv": 128,
    "filts": [70, [1, 32], [32, 32], [32, 64], [64, 64]],
    "gat_dims": [64, 32],
    "pool_ratios": [0.5, 0.7, 0.5, 0.5],
    "temperatures": [2.0, 2.0, 100.0, 100.0]
}

model = Model(d_args)
checkpoint = torch.load("./aasist/weights/AASIST.pth", map_location=torch.device('cpu'))
model.load_state_dict(checkpoint)

# Convert model to float32
model = model.float()
model.eval()

# def bytes_to_wav(audio_bytes):
#     audio_buffer = io.BytesIO(audio_bytes)
#     data, samplerate = sf.read(audio_buffer)
#     if samplerate != 16000:
#         data = librosa.resample(data, orig_sr=samplerate, target_sr=16000)
#     return data

# def detect_spoof_from_bytes(audio_bytes):
#     # Convert bytes to waveform numpy array (16kHz)
#     waveform = bytes_to_wav(audio_bytes)

#     # Convert waveform to tensor (float32) with shape (batch=1, seq_len)
#     waveform_tensor = torch.tensor(waveform).unsqueeze(0).float()

#     with torch.no_grad():
#         last_hidden, output = model(waveform_tensor)
#         # output shape: (1, 2) => logits for [non-spoof, spoof]
#         spoof_logits = output[0, 1]
#         spoof_prob = torch.sigmoid(spoof_logits).item()

#     return spoof_prob



import numpy as np
import io
import soundfile as sf
import librosa
import torch

def bytes_to_wav(audio_bytes, target_sr=16000, target_len=None):
    """
    Return 1-D float32 numpy array (N,).
    Converts stereo->mono, squeezes singleton dims, resamples.
    Optionally pad/truncate to target_len (samples).
    """
    audio_buffer = io.BytesIO(audio_bytes)
    data, sr = sf.read(audio_buffer)   # data shape may be (N,), (N,1), or (N,channels)
    data = np.asarray(data)

    # if multi-channel -> average channels
    if data.ndim > 1:
        data = data.mean(axis=1)

    # remove singleton dims (e.g., (N,1) -> (N,))
    data = np.squeeze(data)

    # ensure float32
    data = data.astype(np.float32)

    # resample if needed
    if sr != target_sr:
        data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)

    # optional pad/truncate
    if target_len is not None:
        if len(data) > target_len:
            data = data[:target_len]
        elif len(data) < target_len:
            pad_len = target_len - len(data)
            data = np.pad(data, (0, pad_len), mode="constant", constant_values=0.0)

    # final guarantee it's 1-D float32
    data = np.asarray(data, dtype=np.float32)
    if data.ndim != 1:
        raise ValueError(f"bytes_to_wav returned array with ndim={data.ndim}, expected 1")
    return data


def detect_spoof_from_bytes(audio_bytes, pad_or_truncate_to_nb_samp=True, debug=False):
    """
    Passes a (1, seq_len) tensor to the model (model will add the channel dim).
    Returns (spoof_prob, label).
    """
    target_len = d_args.get("nb_samp") if pad_or_truncate_to_nb_samp else None
    waveform = bytes_to_wav(audio_bytes, target_sr=16000, target_len=target_len)

    if debug:
        print("after bytes_to_wav:", "dtype:", waveform.dtype, "ndim:", waveform.ndim, "shape:", waveform.shape)

    # final safety: ensure 1D
    waveform = np.squeeze(waveform)
    if waveform.ndim != 1:
        raise RuntimeError(f"Waveform not 1-D after squeeze: ndim={waveform.ndim}")

    # Build tensor as (batch=1, seq_len) <-- IMPORTANT: only one unsqueeze
    waveform_tensor = torch.from_numpy(waveform).float().unsqueeze(0)  # shape (1, N)

    if debug:
        print("waveform_tensor.shape (before model):", waveform_tensor.shape, "dtype:", waveform_tensor.dtype)

    with torch.no_grad():
        last_hidden, output = model(waveform_tensor)   # model will do its own unsqueeze
        spoof_logits = output[0, 1]
        spoof_prob = torch.sigmoid(spoof_logits).item()

    label = "SPOOF" if spoof_prob > 0.5 else "BONAFIDE"
    return spoof_prob, label
