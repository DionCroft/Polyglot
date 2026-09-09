"""Explicit, online setup step. Never imported by the lecture runtime."""

import json
from app.system.accelerators import PROVIDERS, fingerprint, registry_path


def main():
    from winui3.microsoft.windows.applicationmodel.dynamicdependency.bootstrap import (
        initialize,
    )
    import winui3.microsoft.windows.ai.machinelearning as winml

    records = {}
    try:
        with initialize():
            catalog = winml.ExecutionProviderCatalog.get_default()
            for provider in catalog.find_all_providers():
                keys = [
                    k for k, v in PROVIDERS.items() if v == provider.name and k != "gpu"
                ]
                if not keys:
                    continue
                print("Preparing", provider.name, flush=True)
                result = provider.ensure_ready_async().get()
                if (
                    result.status != winml.ExecutionProviderReadyResultState.SUCCESS
                    or not provider.library_path
                ):
                    print("Provider is not ready:", provider.name, flush=True)
                    continue
                records[keys[0]] = {
                    "path": provider.library_path,
                    "sha256": fingerprint(provider.library_path),
                }
    except Exception as exc:
        print("NPU preparation unavailable:", exc)
        print(
            "CPU and compatible DirectML GPU captions can still be used. See docs/WINDOWS_BETA.md."
        )
        return 1
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps({"version": 1, "providers": records}, indent=2), encoding="utf-8"
    )
    temp.replace(path)
    print("Prepared NPUs:", ", ".join(records) or "none detected on this PC")
    print(
        "The app will verify actual encoder execution before enabling any accelerator."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
