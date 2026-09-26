"""Render complete paragraphs through the actual projector paint path.

Playback time is advanced deterministically, not a real-time lecture soak.
Coverage counts only UTF-16 spans of fully visible wrapped lines, in both columns.
"""

import json
from pathlib import Path

from app.captions.state import Caption


ENGLISH = (
    "The project manager checks the critical path, risk register and stakeholder "
    "communication plan. Each work package has an owner, a deadline and acceptance "
    "criteria. We review scope changes and explain their impact on cost and schedule. "
)
CHINESE = (
    "项目经理检查关键路径、风险登记册和利益相关者沟通计划。每个工作包都有负责人、"
    "截止日期和验收标准。我们审查范围变更，并解释这些变更对成本和进度的影响。"
)


def exercise(overlay, app, entries, screenshot_prefix=None):
    """Return rendered coverage; raise if any passage or text span was skipped."""
    overlay.reset(new_session=True)
    for entry in entries:
        overlay.enqueue(entry)
    overlay.show()
    overlay.roll_timer.stop()
    app.processEvents()
    app.processEvents()
    covered = {}
    order = []
    screenshots = set()
    frames = 0
    while frames < 20000:
        overlay.repaint()
        player = overlay.projector
        assert player.drawn and player.current is not None
        key = (player.current.epoch, player.current.identifier)
        if key not in order:
            order.append(key)
        for lang, column in player.columns.items():
            lines = column.visible_lines()
            assert lines, "Panel cannot fit one complete line"
            assert lines[-1].bottom - column.offset <= overlay.height() - 88 + 0.01
            spans = covered.setdefault((key, lang), set())
            for line in lines:
                spans.update(range(line.start, line.end))
        if screenshot_prefix and key == order[0]:
            column = next(iter(player.columns.values()))
            stage = (
                "start"
                if column.index == 0
                else (
                    "end"
                    if column.visible_lines()[-1] == column.lines[-1]
                    else "middle"
                    if column.index >= len(column.lines) // 2
                    else None
                )
            )
            if stage and stage not in screenshots:
                overlay.grab().save(str(screenshot_prefix) + f".{stage}.png")
                screenshots.add(stage)
        if not player.backlog and all(c.done for c in player.columns.values()):
            break
        # One painted frame per transition. The production timer uses wall time
        # capped at 100 ms and never skips lines after a delayed event loop.
        player.advance(10, overlay.settings.projector_line_ms / 1000)
        frames += 1
    assert frames < 20000, "Projector stalled"
    assert order == [(e.epoch, e.identifier) for e in entries]
    totals = {}
    for entry in entries:
        for lang, text in [("en", entry.english), ("zh", entry.chinese)]:
            if overlay.settings.mode not in (
                "Bilingual",
                "English" if lang == "en" else "Chinese",
            ):
                continue
            length = len(text.encode("utf-16-le")) // 2
            spans = covered[((entry.epoch, entry.identifier), lang)]
            assert set(range(length)) <= spans, (
                f"Unread text: passage {entry.identifier}, {lang}"
            )
            totals[lang] = totals.get(lang, 0) + length
    return {
        "passages": len(entries),
        "painted_frames": frames + 1,
        "fully_visible_utf16_units": totals,
    }


def scenarios():
    return {
        "long_english_short_chinese": [Caption(1, 0, 4, ENGLISH * 24, CHINESE, True)],
        "short_english_long_chinese": [
            Caption(1, 0, 4, ENGLISH, CHINESE * 24, True, source_language="zh")
        ],
        "both_long": [Caption(1, 0, 4, ENGLISH * 12, CHINESE * 12, True)],
        "eight_queued_turns": [
            Caption(
                i,
                i * 5,
                i * 5 + 4,
                f"Turn {i}. " + ENGLISH * 2,
                f"第{i}段。" + CHINESE * 2,
                True,
                i // 4,
                "complete",
                "en" if i % 2 else "zh",
            )
            for i in range(8)
        ],
        "unicode_and_paragraph_breaks": [
            Caption(
                1,
                0,
                4,
                "Robot 🤖\n\n" + "long_unbroken_identifier" * 50 + "\nTHE END",
                "机器人🤖\n\n" + CHINESE * 4 + "\n结束",
                True,
            )
        ],
    }


def run(report_path):
    from PySide6.QtWidgets import QApplication
    from app.config.settings import Settings
    from app.ui.overlay import Overlay

    app = QApplication.instance() or QApplication([])
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    overlay = Overlay(Settings(width=1100, projector_height=420, locked=True))
    result = {
        "passed": False,
        "physical_projector_tested": False,
        "speech_accuracy_tested": False,
        "clock": "simulated",
        "cases": {},
    }
    try:
        for name, entries in scenarios().items():
            result["cases"][name] = exercise(
                overlay,
                app,
                entries,
                report.with_suffix("") if name == "both_long" else None,
            )
        result.update(passed=True, native_qt_platform=app.platformName())
        return 0
    finally:
        overlay.close()
        report.write_text(json.dumps(result, indent=2), encoding="utf-8")
