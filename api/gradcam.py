"""Grad-CAM explainability for the multimodal video deepfake detector.

This helper produces a class-activation heatmap that highlights which
regions of a face crop pushed the EfficientNet-B0 video model toward the
"fake" decision. It is intentionally self-contained and only imported on
the opt-in heatmap path so the default analysis flow is untouched.

Color handling note: everything stays in BGR (OpenCV's native order)
until the final JPEG encode. cv2.applyColorMap returns BGR and
cv2.imencode expects BGR, so no RGB<->BGR swaps happen in between.

Model-head note: the video model's classifier ends in Linear(in, 1) -- a
single logit, not a softmax over classes. Grad-CAM therefore backprops
from that one scalar logit rather than a class-indexed output.
"""
from __future__ import annotations

import base64

try:  # Heavy inference deps are optional for lightweight unit tests.
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None


class GradCAMError(RuntimeError):
    """Raised when Grad-CAM cannot be computed (missing deps/target layer)."""


def _require(*deps: tuple[str, object]) -> None:
    missing = [name for name, dep in deps if dep is None]
    if missing:
        raise GradCAMError(
            "Missing Grad-CAM dependencies: " + ", ".join(missing) + "."
        )


class GradCAM:
    """Grad-CAM over the final conv block of an EfficientNet-B0.

    Usage:
        cam = GradCAM(video_model)
        try:
            heat = cam.generate(face_tensor)          # normalized 0..1, 224x224
            data_url = GradCAM.to_data_url(
                GradCAM.render_overlay(heat, face_bgr)
            )
        finally:
            cam.cleanup()

    A single instance is created per analysis and reused across frames so
    the forward/backward hooks are registered only once. cleanup() removes
    the hooks; always call it in a finally block.
    """

    def __init__(self, model) -> None:
        _require(("torch", torch), ("numpy", np))
        self._model = model
        self._activations = None
        self._gradients = None
        self._handles = []

        target_layer = self._resolve_target_layer(model)
        # Forward hook captures activations A_k of the target conv block.
        self._handles.append(
            target_layer.register_forward_hook(self._forward_hook)
        )
        # Full backward hook captures gradients dY/dA_k.
        self._handles.append(
            target_layer.register_full_backward_hook(self._backward_hook)
        )

    @staticmethod
    def _resolve_target_layer(model):
        # torchvision EfficientNet-B0 exposes the conv stack as `features`;
        # features[-1] is the final conv block, output [B, 1280, 7, 7].
        features = getattr(model, "features", None)
        if features is None or len(features) == 0:
            raise GradCAMError(
                "Model has no `features` stack; expected EfficientNet-B0."
            )
        return features[-1]

    def _forward_hook(self, _module, _inp, output) -> None:
        # Retain the activation tensor for CAM weighting.
        self._activations = output.detach()

    def _backward_hook(self, _module, _grad_in, grad_out) -> None:
        # grad_out is a tuple; element 0 is dLoss/dActivation.
        self._gradients = grad_out[0].detach()

    def generate(self, face_tensor) -> "np.ndarray":
        """Return a normalized (0..1) 224x224 CAM for a single face tensor.

        face_tensor: shape [1, 3, 224, 224], already on the model device.
        Runs one grad-enabled forward + backward on the scalar logit.
        Does not alter the no_grad scoring path used for the frame score.
        """
        self._model.zero_grad(set_to_none=True)
        # Grad must be enabled here even if the caller is inside no_grad.
        with torch.enable_grad():
            face_tensor = face_tensor.clone().requires_grad_(True)
            output = self._model(face_tensor)  # [1, 1] single logit
            score = output[:, 0].sum()
            score.backward()

        if self._activations is None or self._gradients is None:
            raise GradCAMError("Hooks did not capture activations/gradients.")

        # alpha_k = global-average-pooled gradients over spatial dims.
        activations = self._activations[0]          # [C, H, W]
        gradients = self._gradients[0]              # [C, H, W]
        weights = gradients.mean(dim=(1, 2))        # [C]

        cam = torch.relu((weights[:, None, None] * activations).sum(dim=0))
        cam = cam.cpu().numpy().astype("float32")

        # Normalize to 0..1 (guard the all-zero / flat case).
        cam -= cam.min()
        max_val = cam.max()
        if max_val > 1e-8:
            cam /= max_val
        else:
            cam[:] = 0.0
        return cam

    @staticmethod
    def render_overlay(cam, face_bgr, alpha: float = 0.45) -> bytes:
        """Blend a normalized CAM onto a BGR face crop; return JPEG bytes.

        cam:      normalized 0..1 float array, any HxW (resized to face here).
        face_bgr: the face crop in BGR uint8 (OpenCV native order).
        Stays in BGR throughout: applyColorMap -> BGR, imencode -> BGR.
        """
        _require(("cv2", cv2), ("numpy", np))
        h, w = face_bgr.shape[:2]
        cam_resized = cv2.resize(cam, (w, h))
        cam_uint8 = np.uint8(255 * cam_resized)
        heatmap_bgr = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)  # BGR
        blended = cv2.addWeighted(heatmap_bgr, alpha, face_bgr, 1 - alpha, 0)
        ok, buffer = cv2.imencode(".jpg", blended)  # expects BGR
        if not ok:
            raise GradCAMError("Failed to JPEG-encode the heatmap overlay.")
        return buffer.tobytes()

    @staticmethod
    def to_data_url(jpeg_bytes: bytes) -> str:
        """Wrap JPEG bytes as a base64 data URL (matches thumbnail format)."""
        encoded = base64.b64encode(jpeg_bytes).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def cleanup(self) -> None:
        """Remove hooks. Safe to call multiple times."""
        for handle in self._handles:
            try:
                handle.remove()
            except Exception:  # pragma: no cover - defensive
                pass
        self._handles = []
        self._activations = None
        self._gradients = None
