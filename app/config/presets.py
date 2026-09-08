"""Local, versioned lecture presets. Audio is never part of a preset."""

import json
from dataclasses import asdict
from app.config.settings import Settings


class Presets:
    def __init__(self, path):
        self.path = path

    def read(self):
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("version") != 1 or not isinstance(data.get("presets"), dict):
            raise ValueError("Unsupported or damaged preset file")
        return data["presets"]

    def save(self, name, settings):
        name = name.strip()
        if not name or len(name) > 80:
            raise ValueError("Use a preset name between 1 and 80 characters")
        presets = self.read()
        presets[name] = asdict(settings)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"version": 1, "presets": presets}, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def load(self, name):
        data = self.read()[name]
        return Settings.from_dict(data)
