from pathlib import Path
from functools import cache
import onnxruntime as ort

ort.disable_telemetry_events()


@cache
def qnn_devices():
    import onnxruntime_qnn as qnn

    ort.register_execution_provider_library(qnn.EP_NAME, qnn.get_library_path())
    devices = [
        d
        for d in ort.get_ep_devices()
        if d.ep_name == qnn.EP_NAME and d.device.type == ort.OrtHardwareDeviceType.NPU
    ]
    if not devices:
        raise RuntimeError(
            "No Qualcomm NPU device available. Check the Qualcomm driver."
        )
    return devices


def session(path, npu=False, profile=False):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Local model missing: {path}")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    options.enable_profiling = profile
    options.profile_file_prefix = str(
        Path(__file__).resolve().parents[2] / "logs" / "ort"
    )
    if npu:
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        options.add_provider_for_devices(
            qnn_devices(),
            {
                "enable_htp_fp16_precision": "1",
                "htp_performance_mode": "sustained_high_performance",
                "htp_graph_finalization_optimization_mode": "3",
                "offload_graph_io_quantization": "0",
            },
        )
        return ort.InferenceSession(str(path), sess_options=options)
    return ort.InferenceSession(
        str(path), sess_options=options, providers=["CPUExecutionProvider"]
    )
