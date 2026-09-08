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
    def load(cls):
        try:
            data = json.loads((DATA / "settings.json").read_text(encoding="utf-8"))
            cfg = cls(
                **{k: v for k, v in data.items() if k in {f.name for f in fields(cls)}}
            )
            for k, low, high in [
                ("font_size", 16, 64),
                ("opacity", 10, 100),
                ("width", 400, 4000),
                ("height", 130, 1200),
                ("spacing", 100, 180),
            ]:
                setattr(cfg, k, max(low, min(high, int(getattr(cfg, k)))))
            if cfg.profile not in {"fast", "balanced", "accuracy"}:
                cfg.profile = "balanced"
            if cfg.mode not in {"Bilingual", "English", "Chinese"}:
                cfg.mode = "Bilingual"
            return cfg
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self):
        DATA.mkdir(parents=True, exist_ok=True)
        tmp = DATA / "settings.tmp"
        tmp.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(DATA / "settings.json")
