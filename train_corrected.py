import os
import sys
import json
import random
import argparse
import numpy as np
from pathlib import Path
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import cv2
from torchvision import transforms, models
from sklearn.metrics import roc_auc_score, classification_report
from tqdm import tqdm

# ─── CONFIGURATION ─────────────────────────────────────────────────────────
FACE_SIZE        = 224    
FRAMES_PER_VIDEO = 10     
RANDOM_SEED      = 42
BATCH_SIZE       = 16
EPOCHS           = 25     # Sufficient for a solid medium subset
LR               = 0.0001
TRAIN_RATIO      = 0.70
VAL_RATIO        = 0.15
# ───────────────────────────────────────────────────────────────────────────

CATEGORY_MAP = {
    "RealVideo-RealAudio": {"binary": 0},
    "FakeVideo-RealAudio": {"binary": 1},
    "RealVideo-FakeAudio": {"binary": 1},
    "FakeVideo-FakeAudio": {"binary": 1},
}

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — STRATIFIED VIDEO-LEVEL SPLIT
# ═══════════════════════════════════════════════════════════════════════════

def collect_and_split_videos(dataset_root: str):
    random.seed(RANDOM_SEED)
    root = Path(dataset_root)
    
    real_pool = []
    fake_pool = []

    for category_folder, label_info in CATEGORY_MAP.items():
        cat_path = root / category_folder
        if not cat_path.exists(): continue
        video_files = list(cat_path.rglob("*.mp4"))
        for vf in video_files:
            entry = {"path": str(vf), "label": label_info["binary"]}
            if label_info["binary"] == 0: real_pool.append(entry)
            else: fake_pool.append(entry)

    # Use all 500 Real videos and match with 500 Fake videos for perfect balance
    limit = min(len(real_pool), len(fake_pool))
    random.shuffle(real_pool); random.shuffle(fake_pool)
    
    def split_data(vids):
        n = len(vids)
        tr, vl = int(n * TRAIN_RATIO), int(n * VAL_RATIO)
        return vids[:tr], vids[tr:tr+vl], vids[tr+vl:]

    tr_r, vl_r, ts_r = split_data(real_pool[:limit])
    tr_f, vl_f, ts_f = split_data(fake_pool[:limit])

    train_vids = tr_r + tr_f
    val_vids   = vl_r + vl_f
    test_vids  = ts_r + ts_f

    random.shuffle(train_vids)
    print(f"⚖️ BALANCED DATASET: {len(train_vids)} Train | {len(val_vids)} Val | {len(test_vids)} Test")
    return train_vids, val_vids, test_vids

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — PICKLE-SAFE DATASET
# ═══════════════════════════════════════════════════════════════════════════

class FakeAVDataset(Dataset):
    def __init__(self, video_list, transform=None):
        self.samples = []
        self.transform = transform
        self.face_cascade = None 

        for entry in tqdm(video_list, desc="🔍 Indexing", leave=False):
            cap = cv2.VideoCapture(entry["path"])
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            if total < FRAMES_PER_VIDEO: continue
            indices = np.linspace(0, total - 1, FRAMES_PER_VIDEO, dtype=int)
            for idx in indices:
                self.samples.append((entry["path"], int(idx), entry["label"]))

    def __len__(self): return len(self.samples)

    def _get_cascade(self):
        if self.face_cascade is None:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        return self.face_cascade

    def __getitem__(self, idx):
        v_path, f_idx, lbl = self.samples[idx]
        cap = cv2.VideoCapture(v_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read(); cap.release()

        if not ret or frame is None:
            frame = np.zeros((FACE_SIZE, FACE_SIZE, 3), dtype=np.uint8)
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._get_cascade().detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
                frame = cv2.resize(frame[y:y+h, x:x+w], (FACE_SIZE, FACE_SIZE))
            else:
                frame = cv2.resize(frame, (FACE_SIZE, FACE_SIZE))

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.transform: img = self.transform(img)
        return img, torch.tensor(lbl, dtype=torch.float32)

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — TRAINING & EVAL
# ═══════════════════════════════════════════════════════════════════════════

def run_epoch(model, loader, criterion, optimizer, device, is_train=True):
    model.train() if is_train else model.eval()
    total_loss, all_probs, all_labels = 0, [], []
    
    with torch.set_grad_enabled(is_train):
        for imgs, labels in tqdm(loader, desc="🚀 Training" if is_train else "🧪 Eval", leave=False):
            imgs, labels = imgs.to(device), labels.to(device).unsqueeze(1)
            if is_train: optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            if is_train: loss.backward(); optimizer.step()
            
            total_loss += loss.item() * imgs.size(0)
            all_probs.extend(torch.sigmoid(outputs).cpu().detach().numpy().flatten())
            all_labels.extend(labels.cpu().numpy().flatten())

    auc = roc_auc_score(all_labels, all_probs) if len(set(all_labels)) > 1 else 0.0
    return total_loss / len(loader.dataset), auc

def main(dataset_root):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_vids, val_vids, test_vids = collect_and_split_videos(dataset_root)
    
    t_tf = transforms.Compose([
        transforms.ToPILImage(),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.1, 0.1),
        transforms.Resize((FACE_SIZE, FACE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    train_loader = DataLoader(FakeAVDataset(train_vids, t_tf), batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(FakeAVDataset(val_vids, t_tf), batch_size=BATCH_SIZE, num_workers=0)

    model = models.efficientnet_b0(weights="IMAGENET1K_V1")
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 1)
    model.to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=LR)
    
    best_auc = 0
    for epoch in range(1, EPOCHS + 1):
        tr_loss, tr_auc = run_epoch(model, train_loader, criterion, optimizer, device)
        vl_loss, vl_auc = run_epoch(model, val_loader, criterion, optimizer, device, is_train=False)
        print(f"Epoch {epoch:02d} | Train AUC: {tr_auc:.4f} | Val AUC: {vl_auc:.4f}")
        
        if vl_auc > best_auc:
            best_auc = vl_auc
            torch.save(model.state_dict(), "best_corrected_model.pt")
            print(f"🌟 Saved new best model (AUC: {vl_auc:.4f})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_root", required=True)
    main(parser.parse_args().dataset_root)