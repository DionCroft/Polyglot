"""Offline, explicitly selected Windows GPU/NPU execution providers."""

import hashlib
import json
from pathlib import Path

PROVIDERS = {
    "gpu": "DmlExecutionProvider",
    "intel_npu": "OpenVINOExecutionProvider",
    "amd_npu": "VitisAIExecutionProvider",
}
LABELS = {
    "gpu": "Windows GPU (DirectML)",
    "intel_npu": "Intel NPU",
    "amd_npu": "AMD NPU",
}
ENCODER_SHA256 = "a9f3b752833b49e880dec91ee5b6d936112be7c3ea07c221024ba493439f46fe"


def fingerprint(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def registry_path():
    from app.config.settings import DATA

    return DATA / "acceleration.json"


def read_registry():
    try:
        data = json.loads(registry_path().read_text(encoding="utf-8"))
        return (
            data["providers"]
            if isinstance(data, dict)
            and data.get("version") == 1
            and isinstance(data.get("providers"), dict)
            else {}
        )
    except (OSError, ValueError, KeyError):
        return {}


def candidates(selection):
    if selection == "cpu":
        return []
    if selection != "auto":
        if selection not in PROVIDERS:
            raise ValueError("Unknown accelerator")
        return [selection]
    installed = read_registry()
    return [k for k in ("intel_npu", "amd_npu") if k in installed] + ["gpu"]


def verify_trace(events, provider):
    executed = {
        e.get("args", {}).get("provider") for e in events if e.get("cat") == "Node"
    }
    executed.discard(None)
    if provider not in executed or executed - {provider}:
        raise RuntimeError(
            "Encoder execution was not exclusively verified on " + provider
        )


def create_encoder(path, selection, trace_dir):
    import onnxruntime as ort

    ort.disable_telemetry_events()
    if fingerprint(path) != ENCODER_SHA256:
        raise ValueError(
            "Accelerated encoder is missing or damaged; run setup to repair it"
        )
    provider = PROVIDERS[selection]
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    options.enable_mem_pattern = False
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    for name, size in (
        ("batch_size", 1),
        ("feature_size", 80),
        ("encoder_sequence_length", 3000),
    ):
        options.add_free_dimension_override_by_name(name, size)
    options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    options.enable_profiling = True
    options.profile_file_prefix = str(trace_dir / "encoder")
    runtime = None
    try:
        if selection == "gpu":
            if provider not in ort.get_available_providers():
                raise RuntimeError("DirectML is unavailable in this build")
            session = ort.InferenceSession(str(path), options, providers=[provider])
        else:
            record = read_registry().get(selection)
            if not isinstance(record, dict):
                raise RuntimeError(
                    "Run Prepare-Acceleration.cmd on this PC before selecting its NPU"
                )
            library = Path(record["path"])
            if not library.is_absolute() or fingerprint(library) != record["sha256"]:
                raise RuntimeError(
                    "NPU provider changed; run Prepare-Acceleration.cmd again"
                )
            from winui3.microsoft.windows.applicationmodel.dynamicdependency.bootstrap import (
                initialize,
            )

            runtime = initialize()
            ort.register_execution_provider_library(provider, str(library))
            devices = [
                d
                for d in ort.get_ep_devices()
                if d.ep_name == provider
                and d.device.type == ort.OrtHardwareDeviceType.NPU
            ]
            if not devices:
                raise RuntimeError("No matching NPU device or compatible driver")
            provider_options = (
                {"device_type": "NPU"} if selection == "intel_npu" else {}
            )
            options.add_provider_for_devices([devices[0]], provider_options)
            session = ort.InferenceSession(str(path), options)
        return session, runtime
    except BaseException:
        if runtime is not None:
            runtime()
        raise
