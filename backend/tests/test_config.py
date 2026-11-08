from pathlib import Path

from app.core.config import Settings


def test_settings_loads_flowfolio_environment(monkeypatch, tmp_path: Path):
    data_dir = tmp_path / "flowfolio-data"
    font_path = tmp_path / "font.ttf"
    monkeypatch.setenv("FLOWFOLIO_ENV", "test")
    monkeypatch.setenv("FLOWFOLIO_DATA_DIR", str(data_dir))
    monkeypatch.setenv("FLOWFOLIO_HOST", "127.0.0.2")
    monkeypatch.setenv("FLOWFOLIO_PORT", "8123")
    monkeypatch.setenv("FLOWFOLIO_PDF_FONT", str(font_path))

    settings = Settings()

    assert settings.environment == "test"
    assert settings.data_dir == data_dir
    assert settings.host == "127.0.0.2"
    assert settings.port == 8123
    assert settings.pdf_font == str(font_path)
