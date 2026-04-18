import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from torchvision import transforms, models
from sklearn.metrics import roc_curve, auc, confusion_matrix, classification_report, ConfusionMatrixDisplay
from train_corrected import collect_and_split_videos, FakeAVDataset # Import your existing logic

# --- CONFIGURATION ---
DATASET_ROOT = r"E:/DeepFake Project/FakeAVCeleb_v1.2/FakeAVCeleb_v1.2"
MODEL_PATH = "best_corrected_model.pt"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FACE_SIZE = 224

def generate_metrics():
    # 1. Recreate the EXACT same test split
    print("🔍 Recreating the Test Set split...")
    _, _, test_vids = collect_and_split_videos(DATASET_ROOT)
    
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((FACE_SIZE, FACE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    test_loader = DataLoader(FakeAVDataset(test_vids, transform), batch_size=16, num_workers=0)

    # 2. Load the Model
    print(f"🚀 Loading weights from {MODEL_PATH}...")
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 1)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE).eval()

    # 3. Collect Predictions
    all_probs = []
    all_labels = []
    
    print("🧪 Running inference on Test Set...")
    with torch.no_grad():
        for imgs, labels in test_loader:
            imgs = imgs.to(DEVICE)
            outputs = model(imgs)
            probs = torch.sigmoid(outputs).cpu().numpy().flatten()
            all_probs.extend(probs)
            all_labels.extend(labels.numpy().flatten())

    # 4. GENERATE PLOTS
    print("📊 Generating Metrics and Plots...")
    
    # --- ROC CURVE ---
    fpr, tpr, _ = roc_curve(all_labels, all_probs)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC)')
    plt.legend(loc="lower right")
    plt.savefig('roc_curve.png')
    print("✅ Saved: roc_curve.png")

    # --- CONFUSION MATRIX ---
    preds = [1 if p > 0.5 else 0 for p in all_probs]
    cm = confusion_matrix(all_labels, preds)
    
    plt.figure(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Real', 'Fake'])
    disp.plot(cmap=plt.cm.Blues)
    plt.title('Confusion Matrix')
    plt.savefig('confusion_matrix.png')
    print("✅ Saved: confusion_matrix.png")

    # --- CLASSIFICATION REPORT ---
    print("\n" + "="*45)
    print("🎓 MSRIT FINAL EVALUATION REPORT")
    print("="*45)
    print(classification_report(all_labels, preds, target_names=['Real', 'Fake']))
    print("="*45)

if __name__ == "__main__":
    generate_metrics()