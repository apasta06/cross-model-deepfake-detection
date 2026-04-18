import sys
import os
import torch
import cv2
import numpy as np
import io
from PIL import Image
from torchvision import transforms, models # Added models here
from facenet_pytorch import MTCNN

# --- CONFIGURATION ---
# Change this to your new model name (best_corrected_model.pt)
VIDEO_PATH = r"E:\DeepFake Project\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2\FakeVideo-FakeAudio\Caucasian (American)\women\id01225\00300_id00231_wavtolip.mp4"
MODEL_PATH = r"best_corrected_model.pt" 
THRESHOLD_SENSITIVITY = 0.20 # Adjusted for the new model's confidence
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 1. UPDATED NORMALIZATION (Matches EfficientNet Training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                         std=[0.229, 0.224, 0.225])
])

def run_inference():
    # 2. LOAD EFFICIENTNET MODEL
    print(f"🚀 Initializing EfficientNet-B0 on {DEVICE}...")
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = torch.nn.Sequential(
        torch.nn.Dropout(p=0.3),
        torch.nn.Linear(in_features, 1)
    )
    
    # Load the new weights
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model file {MODEL_PATH} not found!")
        return
        
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE).eval()

    # 3. SETUP DETECTOR
    mtcnn = MTCNN(keep_all=False, device=DEVICE, image_size=224, post_process=False)
    
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Error: Video file not found at {VIDEO_PATH}")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"📂 Analyzing {total_frames} frames from: {os.path.basename(VIDEO_PATH)}")

    fake_scores = []
    step = max(1, total_frames // 20) 

    for i in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret: break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_img = mtcnn(frame_rgb)
        
        if face_img is not None:
            # JPEG Simulation (Texture Alignment)
            face_np = face_img.permute(1, 2, 0).byte().numpy()
            face_pil = Image.fromarray(face_np)
            
            buffer = io.BytesIO()
            face_pil.save(buffer, format="JPEG", quality=95)
            buffer.seek(0)
            face_pil_compressed = Image.open(buffer)

            # Transform and Predict
            face_tensor = transform(face_pil_compressed).unsqueeze(0).to(DEVICE)
            
            with torch.no_grad():
                output = model(face_tensor)
                # NEW: Use Sigmoid for the single-output model
                prob = torch.sigmoid(output).item()
                
                fake_scores.append(prob)
                print(f"  [Frame {i:3}] Fake Prob: {prob:.4f}")

    cap.release()

    # 4. ROBUST TEMPORAL VOTING
    if fake_scores:
        avg_fake = np.mean(fake_scores)
        max_fake = np.max(fake_scores)
        hit_rate = len([s for s in fake_scores if s > 0.6]) / len(fake_scores)

        indicators = 0
        if avg_fake > THRESHOLD_SENSITIVITY: indicators += 1
        if max_fake > 0.85: indicators += 1 # Slightly tighter for higher quality model
        if hit_rate > 0.15: indicators += 1

        verdict = "🚨 FAKE" if indicators >= 2 else "✅ REAL"
        
        print("\n" + "="*45)
        print(f" FINAL VERDICT    : {verdict}")
        print(f" AVERAGE SCORE    : {avg_fake:.4f}")
        print(f" PEAK ANOMALY     : {max_fake:.4f}")
        print(f" SUSPICIOUS RATE  : {hit_rate * 100:.2f}%")
        print("—"*45)
        print(f" ANALYSIS: {verdict} status confirmed via EfficientNet-B0.")
        print("="*45)
    else:
        print("❌ Error: No faces detected.")

if __name__ == "__main__":
    run_inference()