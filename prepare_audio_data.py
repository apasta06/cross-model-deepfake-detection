import os
import random
import librosa
import numpy as np
import cv2
from PIL import Image
from moviepy import VideoFileClip
import warnings

warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
BASE_DIR = r"E:\DeepFake Project\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2"
OUTPUT_DIR = r"E:\DeepFake Project\Audio_Dataset_Final"

REAL_DIRS = ["RealVideo-RealAudio", "FakeVideo-RealAudio"]
FAKE_DIRS = ["RealVideo-FakeAudio", "FakeVideo-FakeAudio"]

# We will cap it to exactly 1000 per class (800 Train / 200 Val) for diverse, rapid training
TRAIN_LIMIT = 800
VAL_LIMIT = 200

# Create explicit Train and Val folders
for split in ["Train", "Val"]:
    for label in ["Real", "Fake"]:
        os.makedirs(os.path.join(OUTPUT_DIR, split, label), exist_ok=True)

def process_video(video_path, output_path):
    try:
        video_clip = VideoFileClip(video_path)
        if video_clip.audio is None: return False
            
        temp_audio = f"temp_{random.randint(1000,9999)}.wav"
        video_clip.audio.write_audiofile(temp_audio, logger=None, fps=16000)
        video_clip.close()

        # fmax=4000 restricts the AI to the human vocal tract frequencies
        y, sr = librosa.load(temp_audio, sr=16000)
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=4000)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        mel_normalized = cv2.normalize(mel_spec_db, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        Image.fromarray(mel_normalized).save(output_path)
        
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        return True
    except:
        return False

print("🔍 Scanning and mapping identities...")
identity_dict = {}

# Map every video to its specific human identity
for d in REAL_DIRS + FAKE_DIRS:
    full_path = os.path.join(BASE_DIR, d)
    label = "Real" if "RealAudio" in d else "Fake"
    
    for root, _, files in os.walk(full_path):
        for file in files:
            if file.endswith(".mp4"):
                identity = os.path.basename(root) # Captures the 'id00029' folder name
                if identity not in identity_dict:
                    identity_dict[identity] = []
                identity_dict[identity].append((os.path.join(root, file), label))

identities = list(identity_dict.keys())
random.shuffle(identities)
split_idx = int(len(identities) * 0.8)

train_ids = identities[:split_idx]
val_ids = identities[split_idx:]

print(f"📊 Total Identities: {len(identities)} | Mapped to Train: {len(train_ids)} | Mapped to Val: {len(val_ids)}")

def extract_split(id_list, split_name, limit_per_class):
    count_real, count_fake = 0, 0
    
    print(f"\n🚀 Extracting {split_name} Set (Target: {limit_per_class} per class)...")
    for identity in id_list:
        if count_real >= limit_per_class and count_fake >= limit_per_class: break
            
        for video_path, label in identity_dict[identity]:
            if label == "Real" and count_real >= limit_per_class: continue
            if label == "Fake" and count_fake >= limit_per_class: continue
                
            out_path = os.path.join(OUTPUT_DIR, split_name, label, f"{identity}_{os.path.basename(video_path)}.png")
            if process_video(video_path, out_path):
                if label == "Real": count_real += 1
                else: count_fake += 1
                
                total = count_real + count_fake
                if total % 50 == 0:
                    print(f"   Processed {count_real} Real | {count_fake} Fake...")

extract_split(train_ids, "Train", TRAIN_LIMIT)
extract_split(val_ids, "Val", VAL_LIMIT)

print("\n✅ Strict Identity-Split Complete! The data is now leak-proof.")