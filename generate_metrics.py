import os
import sys
import torch
import cv2
import numpy as np
import io
import warnings
from PIL import Image
from torchvision import transforms, models
from facenet_pytorch import MTCNN
import librosa
from moviepy import VideoFileClip
from sklearn.metrics import roc_curve, auc, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

# --- 1. CONFIGURATION ---
TEST_DIR = r"E:\DeepFake Project\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2"
VIDEO_MODEL_PATH = r"best_corrected_model.pt" 
AUDIO_MODEL_PATH = r"best_audio_model.pt" 

VIDEO_THRESHOLD = 0.60 
AUDIO_THRESHOLD = 0.50
TEMPERATURE = 8.0 
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# --- 2. PIPELINE TRANSFORMS ---
transform_video = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

transform_audio = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- 3. LOAD MODELS ---
print("🧠 Loading models for metric generation...")
model_v = models.efficientnet_b0(weights=None)
model_v.classifier = torch.nn.Sequential(torch.nn.Dropout(p=0.3), torch.nn.Linear(model_v.classifier[1].in_features, 1))
model_v.load_state_dict(torch.load(VIDEO_MODEL_PATH, map_location=DEVICE, weights_only=True))
model_v = model_v.to(DEVICE).eval()

model_a = models.efficientnet_b0(weights=None)
model_a.classifier = torch.nn.Sequential(torch.nn.Dropout(p=0.4), torch.nn.Linear(model_a.classifier[1].in_features, 1))
model_a.load_state_dict(torch.load(AUDIO_MODEL_PATH, map_location=DEVICE, weights_only=True))
model_a = model_a.to(DEVICE).eval()

mtcnn = MTCNN(keep_all=False, device=DEVICE, image_size=224, post_process=False)

# --- 4. INFERENCE CORE FUNCTIONS ---
def get_video_score(video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fake_scores = []
    step = max(1, total_frames // 10) # Downsample to 10 frames per video for faster evaluation
    
    for i in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret: break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_img = mtcnn(frame_rgb)
        if face_img is not None:
            face_np = face_img.permute(1, 2, 0).byte().numpy()
            face_pil = Image.fromarray(face_np)
            face_tensor = transform_video(face_pil).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                output = model_v(face_tensor)
                prob = torch.sigmoid(output / TEMPERATURE).item()
                fake_scores.append(prob)
    cap.release()
    return np.mean(fake_scores) if fake_scores else 0.0

def get_audio_score(video_path):
    try:
        video_clip = VideoFileClip(video_path)
        if video_clip.audio is None: return 0.0
        temp_audio = "temp_eval_audio.wav"
        video_clip.audio.write_audiofile(temp_audio, logger=None, fps=16000)
        video_clip.close()
        
        y, sr = librosa.load(temp_audio, sr=16000)
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=4000)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_normalized = cv2.normalize(mel_spec_db, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        if os.path.exists(temp_audio): os.remove(temp_audio)
        
        audio_tensor = transform_audio(Image.fromarray(mel_normalized)).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            output = model_a(audio_tensor)
            return torch.sigmoid(output / TEMPERATURE).item()
    except:
        return 0.0

# --- 5. DATASET HARVESTING ---
subfolders = {
    "RVRA": "RealVideo-RealAudio",
    "FVRA": "FakeVideo-RealAudio",
    "RVFA": "RealVideo-FakeAudio",
    "FVFA": "FakeVideo-FakeAudio"
}

video_pool = []
ground_truth_labels = [] 

print("📂 Gathering evaluation sample files...")
for class_idx, (class_name, folder_name) in enumerate(subfolders.items()):
    full_path = os.path.join(TEST_DIR, folder_name)
    count = 0
    for root, _, files in os.walk(full_path):
        for file in files:
            if file.endswith(".mp4") and count < 15: # Evaluate 15 videos per quadrant (60 total)
                video_pool.append((os.path.join(root, file), class_idx, class_name))
                count += 1

# --- 6. EVALUATION LOOP ---
y_true = []
y_pred = []
video_probs = []
audio_probs = []

print(f"🚀 Running bimodal evaluation on {len(video_pool)} items...")
for idx, (v_path, true_class, class_name) in enumerate(video_pool):
    v_score = get_video_score(v_path)
    a_score = get_audio_score(v_path)
    
    is_v_fake = v_score > VIDEO_THRESHOLD
    is_a_fake = a_score > AUDIO_THRESHOLD
    
    if not is_v_fake and not is_a_fake: pred_class = 0 # RVRA
    elif is_v_fake and not is_a_fake:   pred_class = 1 # FVRA
    elif not is_v_fake and is_a_fake:   pred_class = 2 # RVFA
    else:                               pred_class = 3 # FVFA
        
    y_true.append(true_class)
    y_pred.append(pred_class)
    
    video_probs.append(v_score)
    audio_probs.append(a_score)
    print(f"  [{idx+1}/{len(video_pool)}] True: {class_name} | Pred: {list(subfolders.keys())[pred_class]} (V: {v_score:.2f}, A: {a_score:.2f})")

# --- 7. PLOTTING METRICS ---
print("\n📊 Generating Presentation Artifacts...")

# 1. CONFUSION MATRIX
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=subfolders.keys(), yticklabels=subfolders.keys())
plt.title('Bimodal Fusion Matrix - Confusion Matrix')
plt.ylabel('Actual Category')
plt.xlabel('Predicted Category')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=300)
print("  💾 Saved: confusion_matrix.png")

# 2. ROC CURVES
plt.figure(figsize=(8, 6))

v_true_binary = [1 if y in [1, 3] else 0 for y in y_true]
fpr_v, tpr_v, _ = roc_curve(v_true_binary, video_probs)
roc_auc_v = auc(fpr_v, tpr_v)
plt.plot(fpr_v, tpr_v, color='blue', lw=2, label=f'Visual Model ROC (AUC = {roc_auc_v:.4f})')

a_true_binary = [1 if y in [2, 3] else 0 for y in y_true]
fpr_a, tpr_a, _ = roc_curve(a_true_binary, audio_probs)
roc_auc_a = auc(fpr_a, tpr_a)
plt.plot(fpr_a, tpr_a, color='red', lw=2, label=f'Acoustic Model ROC (AUC = {roc_auc_a:.4f})')

plt.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curves')
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig('roc_curves.png', dpi=300)
print("  💾 Saved: roc_curves.png")

print("\n✅ Metric Generation Complete. Images saved to your project folder!")