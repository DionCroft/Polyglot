import json
import pytest
from app.asr.decoding import WhisperTokenizer
from app.captions.glossary import Glossary
from app.config.settings import ROOT


def test_project_management_preserves_distinct_spoken_concepts():
    glossary = Glossary(ROOT / "glossaries/project_management.json")
    sentence = "The risk is different from the issue. Assurance is not insurance. The shareholder questioned the stakeholder. Compare cost with coast, float with flow, and outputs with outcomes."
    assert glossary.english(sentence) == sentence
    assert (
        Glossary(ROOT / "glossaries/embedded_systems.json").english("N P V and C P I")
        == "N P V and C P I"
    )


def test_project_management_normalises_only_explicit_variants():
    glossary = Glossary(ROOT / "glossaries/project_management.json")
    assert (
        glossary.english("N P V, C.P.I. and T C P I guide the discussion.")
        == "NPV, CPI and TCPI guide the discussion."
    )
    assert (
        glossary.english(
            "The Gant chart uses resource leveling and a work break down structure."
        )
        == "The Gantt chart uses resource levelling and a work breakdown structure."
    )
    assert (
        glossary.english("Prince two, scrum and kanban.")
        == "PRINCE2, Scrum and Kanban."
    )
    assert glossary.chinese("NPV", "wrong") == "净现值"
    assert glossary.chinese("No investment metric was mentioned", "NPV") == "NPV"


def test_all_course_lists_fit_complete_prompt_budget():
    path = ROOT / "models/whisper/fast/tokenizer.json"
    if not path.is_file():
        pytest.skip("requires installed tokenizer assets")
    tokenizer = WhisperTokenizer(path)
    lists = json.loads(
        (ROOT / "assets/co7000-vocabulary.json").read_text(encoding="utf-8")
    )["lists"]
    assert [entry["week"] for entry in lists] == list(range(1, 13))
    for entry in lists:
        full = tokenizer.encode(" " + ", ".join(entry["terms"]))
        assert len(full) <= 32
        assert tokenizer.vocabulary_tokens("\n".join(entry["terms"])) == full
        assert set(entry["slides"]) == set(entry["terms"])
        assert (ROOT / "glossaries" / (entry["glossary"] + ".json")).is_file()


def test_ambiguous_initialisms_keep_ordinary_lowercase_words():
    glossary = Glossary(ROOT / "glossaries/project_management.json")
    assert glossary.english("E A C and V A C") == "EAC and VAC"
    assert glossary.chinese("etc.", "等等") == "等等"
    assert glossary.chinese("ETC", "wrong") == "完工尚需估算"
    assert glossary.chinese("estimate to complete", "wrong") == "完工尚需估算"
