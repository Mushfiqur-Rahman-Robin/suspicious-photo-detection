"""Unit tests: torch device resolution (embedding/device.py)."""

from __future__ import annotations

import torch

from config.settings import DeviceKind
from embedding.device import resolve_torch_device


def test_cpu_maps_to_cpu():
    assert resolve_torch_device(DeviceKind.CPU) == torch.device("cpu")


def test_cuda_maps_to_cuda():
    assert resolve_torch_device(DeviceKind.CUDA) == torch.device("cuda")


def test_mps_maps_to_mps():
    assert resolve_torch_device(DeviceKind.MPS) == torch.device("mps")


def test_auto_maps_to_a_real_device():
    device = resolve_torch_device(DeviceKind.AUTO)
    assert device.type in {"cpu", "cuda", "mps"}
