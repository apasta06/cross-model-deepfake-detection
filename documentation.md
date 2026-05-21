

# 🧠 Cross-Model Deepfake Detection - Backend System

**Institution:** Ramaiah Institute of Technology (MSRIT) - 8th Semester Project  
**Sub-System:** Unimodal Visual Forgery Detection  
**Active Branch:** `unimodal`  
**Frontend Integration Target:** `apeksha/ui`  

This document serves as the complete technical reference for the backend deepfake detection system, detailing the file structure, AI architecture, inference logic, and the API contract required for frontend integration.

---

## 📂 1. Directory & File Structure

Here is the anatomy of the `unimodal` branch and what each critical file does:

```text
cross-model-deepfake-detection/
│
├── Unimodal/                   # Core directory for visual-only detection
│   ├── detect_video.py         # 🚀 Main Inference API Script (The "Engine")
│   ├── train_efficientnet.py   # 🧪 Training Pipeline (Data splitting, training loop)
│   └── Eval/                   # Evaluation scripts for generating AUC/ROC metrics
│
├── best_corrected_model.pt     # 🧠 The trained EfficientNet-B0 weights (Requires Git LFS or Drive link if >100MB)
├── requirements.txt            # 📦 Python dependencies (PyTorch, OpenCV, MTCNN, etc.)
├── .gitignore                  # 🛡️ Prevents large datasets and local environments from pushing to GitHub
└── backend_docs.md             # 📄 This documentation file

```

### 📄 File Dictionary

* **`detect_video.py`**: The production-ready inference script. It takes an input video, runs MTCNN face extraction, simulates JPEG compression, passes frames to EfficientNet-B0, and applies Temperature Scaling to return a final verdict. This is the script the frontend API will trigger.
* **`train_efficientnet.py`**: The script used to train the model on the FakeAVCeleb dataset. It handles the stratified 1:1 sampling and strict video-level identity splitting.
* **`best_corrected_model.pt`**: The finalized neural network weights achieving a 0.9869 Validation AUC.
* **`.gitignore`**: Crucial for team collaboration. It explicitly ignores `venv/`, `__pycache__`, `*.mp4` (video files), and the `FakeAVCeleb_Faces/` dataset folder to keep the GitHub repository lightweight.

---

## 🏗️ 2. AI Architecture & Core Logic

Our system moves beyond a basic binary classifier by implementing several "production-grade" engineering fixes to ensure real-world reliability.

### **The Backbone: EfficientNet-B0**

* Utilizes **Compound Scaling** and **MBConv (Inverted Residual Blocks)** to extract high-level forgery artifacts (blending lines, chromatic aberration) with minimal computational latency.
* Optimized to run real-time inference on standard consumer hardware (e.g., RTX 3050).

### **The "Data Science" Fixes**

* **Identity Isolation:** During training, we used **Video-Level Splitting**. If a subject's face was in the training set, they were completely excluded from the test set. This ensures the model detects *forgeries*, not *identities*.
* **Balanced Weights:** Trained on a perfectly stratified 500 Real / 500 Fake video split to eliminate majority-class bias.

### **Inference Optimizations (Live Video)**

1. **JPEG Buffer Simulation:** Live camera/uploaded frames are virtually compressed to a JPEG buffer (quality=95) before processing. This aligns the digital texture of live video with the compressed training dataset.
2. **Temperature Scaling ($T=8.0$):** Neural networks are notoriously overconfident. We divide the output logits by 8.0 before activation. This calibrates the model to output nuanced, decimal-based **Suspiciousness Scores** (e.g., `0.9241`) rather than a hard `0` or `1`.
3. **Temporal Voting:** The system analyzes 20 equidistant frames across a video and uses a majority-indicator logic (Average Score + Peak Anomaly + Hit Rate) to render the final `REAL` or `FAKE` verdict.

---

## 🔌 3. Frontend API Contract

To connect the React/UI frontend to this backend, the frontend must make a `POST` request using `multipart/form-data`.

### **Endpoint Definition**

* **Route:** `/api/v1/detect-video` *(Adjust based on final FastAPI/Flask routing)*
* **Method:** `POST`
* **Content-Type:** `multipart/form-data`

### **Request Payload**

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `video` | `File` | **Yes** | The uploaded video file (`.mp4`, `.mov`, `.avi`). |
| `temperature` | `Float` | No | Overrides default Temperature Scaling. Default is `8.0`. |

### **Success Response (200 OK)**

*The frontend should use this JSON structure to populate the results dashboard and "Suspiciousness Timeline" chart.*

```json
{
  "status": "success",
  "data": {
    "file_name": "uploaded_video.mp4",
    "analysis_summary": {
      "verdict": "FAKE",
      "average_suspiciousness": 0.9241,
      "peak_anomaly": 0.9984,
      "suspicious_rate_percentage": 100.0,
      "frames_analyzed": 20
    },
    "frame_breakdown": [
      {
        "frame_number": 0,
        "suspiciousness_score": 0.9241,
        "is_flagged": true
      },
      {
        "frame_number": 14,
        "suspiciousness_score": 0.9102,
        "is_flagged": true
      }
    ],
    "metadata": {
      "model_used": "EfficientNet-B0",
      "processing_time_seconds": 12.4
    }
  }
}

```

### **Error Responses**

The frontend must handle these gracefully and display a user-friendly alert.

* **400 Bad Request:** `{"error": "NO_FACE_DETECTED", "message": "MTCNN could not locate a clear face."}`
* **415 Unsupported Media Type:** `{"error": "INVALID_FORMAT", "message": "Please upload a valid .mp4 or .avi file."}`

---

## 🚀 4. Local Setup Instructions (For Teammates)

If you need to spin up the backend on your local machine to test the UI:

1. **Clone the repo & switch to the unimodal branch:**
```bash
git clone [https://github.com/apasta06/cross-model-deepfake-detection.git](https://github.com/apasta06/cross-model-deepfake-detection.git)
cd cross-model-deepfake-detection
git checkout unimodal

```


2. **Create and activate a virtual environment:**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```


4. **Add the Model Weights:**
* Download `best_corrected_model.pt` from the team Google Drive.
* Place it in the root directory.


5. **Run the API server:**
*(Command depends on whether we wrap `detect_video.py` in FastAPI/Flask)*

```

```