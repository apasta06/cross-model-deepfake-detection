import os
import cv2
import torch
from facenet_pytorch import MTCNN
from tqdm import tqdm

# 1. Setup GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=False, device=device, post_process=True, image_size=224)

# 2. PATH FIXING SECTION
potential_roots = [
    r"E:\DeepFake Project\FakeAVCeleb_v1.2",
    r"E:\DeepFake Project\FakeAVCeleb_v1.2\FakeAVCeleb_v1.2"
]

data_root = None
for root in potential_roots:
    if os.path.exists(os.path.join(root, 'RealVideo-RealAudio')):
        data_root = root
        break

if data_root is None:
    print("❌ ERROR: Could not find the dataset folders!")
    exit()

print(f"✅ Found dataset at: {data_root}")

# --- CHANGE 1: New folder for the subset ---
output_root = r"E:\DeepFake Project\FakeAVCeleb_Subset_Faces"
os.makedirs(output_root, exist_ok=True)

categories = ['RealVideo-RealAudio', 'FakeVideo-RealAudio', 'FakeVideo-FakeAudio', 'RealVideo-FakeAudio']

print(f"Using device: {device}")

for cat in categories:
    cat_path = os.path.join(data_root, cat)
    if not os.path.exists(cat_path):
        continue
    
    label = "Real" if cat.startswith("RealVideo") else "Fake"
    target_dir = os.path.join(output_root, label)
    os.makedirs(target_dir, exist_ok=True)

    videos = []
    for root, dirs, files in os.walk(cat_path):
        for f in files:
            if f.endswith('.mp4'):
                videos.append(os.path.join(root, f))
    
    # --- CHANGE 2: Increase to 500 videos per category ---
    print(f"\nProcessing {len(videos[:500])} videos in {cat}...")
    
    for video_path in tqdm(videos[:500]): 
        video_name = os.path.basename(video_path).split('.')[0]
        cap = cv2.VideoCapture(video_path)
        
        frame_idx = 0
        success_frames = 0
        
        # --- CHANGE 3: Set to 5 faces per video (Total 10,000 images) ---
        # 5 faces is plenty for a subset and makes training much faster
        while cap.isOpened() and success_frames < 5: 
            ret, frame = cap.read()
            if not ret: break
            
            if frame_idx % 30 == 0: 
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                save_path = os.path.join(target_dir, f"{video_name}_s{success_frames}.jpg")
                
                try:
                    mtcnn(frame_rgb, save_path=save_path)
                    success_frames += 1
                except Exception:
                    pass
            frame_idx += 1
        cap.release()

print(f"\n🎉 Subset ready! Check {output_root}")