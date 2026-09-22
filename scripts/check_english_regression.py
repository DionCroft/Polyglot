"""Reproduce the fixed manual-English regression set on Windows Snapdragon.

Run as a module after preparing the accent and translation fixtures. This compares
real CPU/QNN model outputs, not classroom word accuracy. No audio is uploaded.
"""

import gc, json, sys, time, wave
from pathlib import Path
import numpy as np
from app.system.offline import enforce_offline
from app.asr.cpu_whisper import CpuWhisper
from app.asr.qnn_whisper import QnnWhisper
from app.translation.opus_mt import OpusMT
from app.captions.glossary import Glossary

enforce_offline()
root = Path(__file__).resolve().parents[1]
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", required=True)
parser.add_argument(
    "--baseline", default="docs/evidence/auto-0.7-english-regression.json"
)
args = parser.parse_args()
result = {"speech": [], "translation": []}
cases = json.loads(
    (root / "tests/fixtures/accent-cases.json").read_text(encoding="utf-8")
)["cases"]
cases = cases[:2] + cases[20:22] + cases[-2:]
for backend in ["cpu", "fast", "balanced"]:
    model = (
        CpuWhisper(root / "models/whisper/fast")
        if backend == "cpu"
        else QnnWhisper(root / "models/whisper" / backend)
    )
    for mode in ["standard", "careful"]:
        model.configure_recognition(mode, "")
        for case in cases:
            with wave.open(str(root / case["path"])) as source:
                audio = (
                    np.frombuffer(source.readframes(source.getnframes()), "<i2").astype(
                        np.float32
                    )
                    / 32768
                )
            text = model.transcribe(audio)
            result["speech"].append(
                dict(backend=backend, mode=mode, case=case["id"], text=text)
            )
    del model
    gc.collect()
    print("Finished", backend, flush=True)
model = OpusMT(root / "models/translation/opus")
for case in json.loads(
    (root / "tests/fixtures/translation-corpus.json").read_text(encoding="utf-8")
)["cases"]:
    text = model.translate(case["english"])
    glossary = Glossary(root / "glossaries" / (case["glossary"] + ".json"))
    result["translation"].append(
        dict(case=case["id"], raw=text, caption=glossary.chinese(case["english"], text))
    )
Path(args.output).write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    "Saved",
    len(result["speech"]),
    "speech and",
    len(result["translation"]),
    "translation cases",
    flush=True,
)

expected = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
assert result == expected, "Manual English regression outputs changed"
print("Exact baseline match", flush=True)
