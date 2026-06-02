from linguaresume.llm.client import MockLLMClient
from linguaresume.config import Config, OllamaConfig, OutputConfig, ValidationConfig
from linguaresume.tailoring.engine import TailoringEngine
import os


def test_tailoring_with_mock(tmp_path, monkeypatch):
    # Construct a minimal Config to avoid YAML dependency in tests
    ollama_cfg = OllamaConfig(url="http://127.0.0.1:1234/v1/chat/completions", model="mock", timeout=60, temperature=0.3)
    cfg = Config(
        ollama=ollama_cfg,
        cv_map={"other": "./cvs/nontech_master_en.md"},
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

    # Use a Mock LLM that returns a minimal resume middle
    mock = MockLLMClient(responses={})
    engine = TailoringEngine(cfg, mock, force=True)

    # Avoid importing Playwright by faking PDF conversion
    def fake_convert_to_pdf(self, md_path):
        pdf_path = os.path.splitext(md_path)[0] + ".pdf"
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%EOF")
        return pdf_path

    monkeypatch.setattr(TailoringEngine, "convert_to_pdf", fake_convert_to_pdf)

    job_file = tmp_path / "job.txt"
    job_file.write_text("Looking for a Test Engineer")

    md_path, pdf_path = engine.run(str(job_file))
    assert os.path.exists(md_path)
    assert md_path.endswith(".md")
