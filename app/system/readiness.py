"""Warm and verify the same local model bundle used by the lecture."""

import logging
from app.system.models import ModelStore


def check(root, profile, store=None):
    result = {
        "speech": False,
        "translation": False,
        "vad": False,
        "npu": False,
        "messages": [],
    }
    try:
        bundle = (store or ModelStore(root)).load(profile)
        result.update(
            speech=True,
            translation=bundle.mt is not None,
            vad=True,
            npu=bundle.npu,
            messages=bundle.messages,
        )
    except Exception:
        logging.exception("Local model readiness failed")
        result["messages"].append(
            "Local model verification failed. See diagnostics and run model repair before starting."
        )
    return result
