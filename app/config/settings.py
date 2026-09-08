import json, os
from dataclasses import dataclass, asdict, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(
    os.environ.get(
        "LECTURELIVE_DATA",
        str(Path(os.environ.get("LOCALAPPDATA", str(ROOT))) / "LectureLive"),
    )
)


@dataclass
class Settings:
    lecture_title: str = ""
    vocabulary: str = ""
    lock_shortcut: str = "Ctrl+Alt+C"
    pause_shortcut: str = "Ctrl+Alt+Space"
    microphone: str = ""
    mode: str = "Bilingual"
    profile: str = "balanced"
    glossary: str = "embedded_systems"
    save_transcripts: bool = True
    font_size: int = 30
    opacity: int = 78
    width: int = 1100
    spacing: int = 120
    monitor: str = ""
    placement: str = "Bottom"
    locked: bool = False
    visible: bool = True
    x: int = -1
    y: int = -1
    height: int = 230
    english_color: str = "#ffffff"
    chinese_color: str = "#8fe9d5"

    @classmethod
    def from_dict(cls, data):
        import re

        if not isinstance(data, dict):
            raise ValueError("Settings must be a JSON object")
        cfg = cls(
            **{k: v for k, v in data.items() if k in {f.name for f in fields(cls)}}
        )
        for field in fields(cls):
            value = getattr(cfg, field.name)
            if field.type is str and not isinstance(value, str):
                raise ValueError("Invalid text setting: " + field.name)
            if field.type is bool and not isinstance(value, bool):
                raise ValueError("Invalid boolean setting: " + field.name)
        for key, low, high in [
            ("font_size", 16, 64),
            ("opacity", 10, 100),
            ("width", 400, 4000),
            ("height", 130, 1200),
            ("spacing", 100, 180),
        ]:
            setattr(cfg, key, max(low, min(high, int(getattr(cfg, key)))))
        cfg.x = int(cfg.x)
        cfg.y = int(cfg.y)
        if cfg.profile not in {"fast", "balanced"}:
            cfg.profile = "balanced"
        if cfg.mode not in {"Bilingual", "English", "Chinese"}:
            cfg.mode = "Bilingual"
        if cfg.placement not in {"Top", "Bottom", "Custom"}:
            cfg.placement = "Bottom"
        if not re.fullmatch(r"[a-z_]+", cfg.glossary):
            cfg.glossary = "general"
        for key in ("english_color", "chinese_color"):
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", getattr(cfg, key)):
                setattr(cfg, key, getattr(cls(), key))
        return cfg

    @classmethod
    def load(cls):
        try:
            return cls.from_dict(
                json.loads((DATA / "settings.json").read_text(encoding="utf-8"))
            )
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self):
        DATA.mkdir(parents=True, exist_ok=True)
        tmp = DATA / "settings.tmp"
        tmp.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(DATA / "settings.json")
