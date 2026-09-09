"""Warm and verify the same local model bundle used by the lecture."""

import logging
from app.system.models import ModelStore


def check(root, profile, store=None, accelerator="auto"):
    result = {
        "speech": False,
        "translation": False,
        "vad": False,
        "npu": False,
        "messages": [],
    }
    owned = store is None
    store = store or ModelStore(root)
    try:
        bundle = store.load(profile, accelerator=accelerator)
        result.update(
            speech=True,
            translation=bundle.mt is not None,
            vad=True,
            npu=bundle.npu,
            accelerated=bundle.accelerated,
            backend=bundle.asr.name,
            messages=bundle.messages,
        )
    except Exception:
        logging.exception("Local model readiness failed")
        result["messages"].append(
            "Local model verification failed. See diagnostics and run model repair before starting."
        )
    finally:
        if owned:
            store.close()
    return result
