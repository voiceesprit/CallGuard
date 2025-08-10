from workflow import detect_spoof_from_bytes
import io

# Read the WAV file bytes
with open(r"D:\HackNation\fake\25.wav", "rb") as f:
    audio_bytes = f.read()

# Pass the raw bytes to your function
prob, label = detect_spoof_from_bytes(audio_bytes, pad_or_truncate_to_nb_samp=True, debug=True)
print("Spoof score:",prob)


