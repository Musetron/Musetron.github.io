import os
import wave
import json
import base64

output = {}

for file in os.listdir("."):
    if file.endswith(".wav"):
        with wave.open(file, "rb") as wav:
            frames = wav.readframes(wav.getnframes())

            # PCM Rohdaten als Base64 speichern (JSON-sicher)
            pcm_b64 = base64.b64encode(frames).decode("utf-8")

            output[file] = {
                "title": file,
                "channels": wav.getnchannels(),
                "sample_width": wav.getsampwidth(),
                "framerate": wav.getframerate(),
                "pcm_base64": pcm_b64
            }

with open("all_wavs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("Fertig: all_wavs.json erstellt")