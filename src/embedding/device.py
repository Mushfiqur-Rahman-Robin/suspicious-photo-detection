"""Torch device resolution for embedders.

Centralizes the mapping from the ``DeviceKind`` config enum to a concrete
``torch.device`` so ``auto`` means exactly one thing everywhere and the check
runs once per process.
"""

from __future__ import annotations

import torch

from config.settings import DeviceKind


def resolve_torch_device(device: DeviceKind) -> torch.device:
    """Map a configured ``DeviceKind`` to a concrete torch device."""
    if device is DeviceKind.CPU:
        return torch.device("cpu")
    if device is DeviceKind.CUDA:
        return torch.device("cuda")
    if device is DeviceKind.MPS:
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
