import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score
import time
import copy

# --- 1. CONFIGURATION ---
DATA_DIR_TRAIN = r"E:\DeepFake Project\Audio_Dataset_Final\Train"
DATA_DIR_VAL = r"E:\DeepFake Project\Audio_Dataset_Final\Val"
MODEL_SAVE_PATH = "best_audio_model.pt"

BATCH_SIZE = 16  
EPOCHS = 25      
LEARNING_RATE = 2e-4
PATIENCE = 6

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"🚀 Using Device: {DEVICE}")

# --- 2. DATA PIPELINE (WITH SPECAUGMENT) ---
transform_train = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.4, scale=(0.02, 0.1), ratio=(0.3, 3.3), value=0) # SpecAugment
])

transform_val = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

train_dataset = datasets.ImageFolder(root=DATA_DIR_TRAIN, transform=transform_train)
val_dataset = datasets.ImageFolder(root=DATA_DIR_VAL, transform=transform_val)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

# CRITICAL FIX: Ensure Fake = 1.0, Real = 0.0
fake_idx = train_dataset.class_to_idx['Fake']
print(f"📊 Dataset Loaded. PyTorch mapping: {train_dataset.class_to_idx} (Fake will map to 1.0)")

# --- 3. ARCHITECTURE ---
print("🧠 Initializing EfficientNet-B0...")
model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
in_features = model.classifier[1].in_features
model.classifier = nn.Sequential(
    nn.Dropout(p=0.4),
    nn.Linear(in_features, 1)
)

model = model.to(DEVICE)
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-5)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

# --- 4. TRAINING LOOP ---
best_val_auc = 0.0
epochs_no_improve = 0

for epoch in range(EPOCHS):
    start_time = time.time()
    model.train()
    running_loss = 0.0
    
    for inputs, labels in train_loader:
        inputs = inputs.to(DEVICE)
        # Bulletproof label mapping: If it matches 'Fake' index, set to 1.0, else 0.0
        binary_labels = torch.where(labels == fake_idx, 1.0, 0.0).float().unsqueeze(1).to(DEVICE)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, binary_labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
        
    epoch_loss = running_loss / len(train_dataset)
    scheduler.step()
    
    # -- VALIDATION PHASE --
    model.eval()
    val_loss = 0.0
    all_preds, all_labels = [], []
    
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs = inputs.to(DEVICE)
            binary_labels = torch.where(labels == fake_idx, 1.0, 0.0).float().unsqueeze(1).to(DEVICE)
            
            outputs = model(inputs)
            loss = criterion(outputs, binary_labels)
            val_loss += loss.item() * inputs.size(0)
            
            probs = torch.sigmoid(outputs).cpu().numpy()
            all_preds.extend(probs)
            all_labels.extend(binary_labels.cpu().numpy())
            
    val_loss = val_loss / len(val_dataset)
    val_auc = roc_auc_score(all_labels, all_preds)
    elapsed_time = time.time() - start_time
    
    print(f"Epoch {epoch+1:02d}/{EPOCHS} | Time: {elapsed_time:.0f}s | Train Loss: {epoch_loss:.4f} | Val AUC: {val_auc:.4f}")
    
    if val_auc > best_val_auc:
        best_val_auc = val_auc
        epochs_no_improve = 0
        torch.save(model.state_dict(), MODEL_SAVE_PATH)
        print(f"   🌟 New best model saved! (AUC: {best_val_auc:.4f})")
    else:
        epochs_no_improve += 1
        
    if epochs_no_improve >= PATIENCE:
        print("\n🛑 Early Stopping triggered! Peak real-world generalization reached.")
        break

print(f"\n✅ Final Audio Model Locked. Peak Validation AUC: {best_val_auc:.4f}")