import logging
from logging.handlers import RotatingFileHandler


def configure(folder):
    folder.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        folder / "lecturelive.log", maxBytes=2_000_000, backupCount=4, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    logging.basicConfig(level=logging.INFO, handlers=[handler])
