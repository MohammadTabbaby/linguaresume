from linguaresume.llm.client import MockLLMClient
from linguaresume.config import Config, OllamaConfig, OutputConfig, ValidationConfig
from linguaresume.tailoring.engine import TailoringEngine


def make_cfg(tmp_path, cv_map):
    ollama_cfg = OllamaConfig(url="http://127.0.0.1:1234/v1/chat/completions", model="mock", timeout=60, temperature=0.3)
    cfg = Config(
        ollama=ollama_cfg,
        cv_map=cv_map,
        fallback_cv="./cvs/master_en.md",
        output=OutputConfig(subdir=str(tmp_path / "outputs"), max_retries=1),
        section_aliases={},
        static_section_keys=["education", "languages"],
        junior_keywords=[],
        enable_junior_special_case=False,
        corrections_fr=[],
        corrections_de=[],
        stopwords=[],
        resume_css="",
        validation=ValidationConfig(),
    )
    return cfg


def test_select_master_cv_prefers_de(tmp_path):
    cv_map = {
        "de_webdev": "./cvs/web_de.md",
        "webdev": "./cvs/web_en.md",
        "other": "./cvs/nontech_master_en.md",
    }
    cfg = make_cfg(tmp_path, cv_map)
    mock = MockLLMClient(responses={})
    engine = TailoringEngine(cfg, mock, force=True)
    engine.target_lang = "de"
    engine.domain = "webdev"
    engine.select_master_cv()
    assert engine.master_lang == "de"
    assert engine.master_md.strip()


def test_select_master_cv_fallback_to_en(tmp_path):
    cv_map = {
        "webdev": "./cvs/web_en.md",
    }
    cfg = make_cfg(tmp_path, cv_map)
    mock = MockLLMClient(responses={})
    engine = TailoringEngine(cfg, mock, force=True)
    engine.target_lang = "de"
    engine.domain = "webdev"
    engine.select_master_cv()
    assert engine.master_lang == "en"
    assert engine.master_md.strip()
