from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """執行期設定；可將私人資料放在 Git 工作樹之外。"""

    environment: str = "development"
    data_dir: Path = Path("data")
    host: str = "127.0.0.1"
    port: int = 8000
    pdf_font: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="FLOWFOLIO_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def resolved_data_dir(self) -> Path:
        path = self.data_dir
        return path if path.is_absolute() else (self.project_root / path).resolve()

    @property
    def database_path(self) -> Path:
        return self.resolved_data_dir / "flowfolio.db"

    @property
    def media_dir(self) -> Path:
        return self.resolved_data_dir / "media"

    @property
    def backup_dir(self) -> Path:
        return self.resolved_data_dir / "backups"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
