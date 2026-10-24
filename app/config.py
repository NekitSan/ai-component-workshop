import os
import sys
from dataclasses import dataclass
from typing import Literal, TypedDict, cast

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


# ---------- Типы ----------

KeepAliveTime = Literal["1m", "5m", "10m", "1h", "2h", 0, -1]
ResponseFormat = Literal["json", "text"]


# ---------- Секции ----------

class OllamaOptions(TypedDict, total=False):
    """Параметры модели, которые уходят в Ollama как `options`."""
    temperature: float
    num_predict: int
    num_ctx: int
    # top_p: float
    # top_k: int
    # repeat_penalty: float
    # seed: int


@dataclass
class AgentSettings:
    """Настройки конкретного агента."""
    keep_alive: KeepAliveTime
    options: OllamaOptions


@dataclass
class AppConfig:
    # .env
    figma_token: str
    figma_base_url: str
    figma_file_key: str
    ollama_api_url: str
    models: list[str]

    # Глобальные параметры
    stream: bool
    format: ResponseFormat

    # Настройки агентов
    refiner: AgentSettings
    architect: AgentSettings
    vue: AgentSettings


# ---------- Загрузка ----------

def _default_toml_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "llm", "config.toml")


def load_config(
    toml_path: str | None = None,
    env: dict[str, str] | None = None,
) -> AppConfig:
    """Собирает AppConfig из TOML-файла и переменных окружения.

    Args:
        toml_path: путь к config.toml. По умолчанию — рядом с этим модулем.
        env: словарь переменных окружения. По умолчанию — os.environ.
             Явная передача нужна для тестов (изоляция от глобального состояния).

    Raises:
        FileNotFoundError: если toml_path не существует.
        tomllib.TOMLDecodeError: если TOML битый.
        ValueError: если MODELS пуст или содержит только пустые строки.
    """
    if toml_path is None:
        toml_path = _default_toml_path()
    if env is None:
        env = os.environ

    with open(toml_path, "rb") as f:
        toml_data = tomllib.load(f)

    ollama_global = toml_data.get("ollama", {}).get("global", {})
    agents = toml_data.get("ollama", {}).get("agents", {})

    global_ka: KeepAliveTime = ollama_global.get("default_keep_alive", 0)

    def get_agent_settings(name: str) -> AgentSettings:
        raw_agent = dict(agents.get(name, {}))
        ka = raw_agent.pop("keep_alive", global_ka)
        return AgentSettings(
            keep_alive=cast(KeepAliveTime, ka),
            options=cast(OllamaOptions, raw_agent),
        )

    # --- models: обязательный инвариант ---
    models_raw = env.get("MODELS", "")
    models = [m.strip() for m in models_raw.split(",") if m.strip()]
    if not models:
        raise ValueError(
            "MODELS is empty. Set the MODELS env variable, e.g. "
            "MODELS='llama3.2:3b,qwen2.5-coder:7b'"
        )

    return AppConfig(
        figma_token=env.get("FIGMA_TOKEN", ""),
        figma_base_url=env.get("FIGMA_BASE_URL", "https://api.figma.com/v1/files/"),
        figma_file_key=env.get("FIGMA_FILE_KEY", ""),
        ollama_api_url=env.get("OLLAMA_API_URL", "http://localhost:11434"),
        models=models,
        stream=ollama_global.get("stream", False),
        format=cast(ResponseFormat, ollama_global.get("format", "json")),
        refiner=get_agent_settings("refiner"),
        architect=get_agent_settings("architect"),
        vue=get_agent_settings("vue"),
    )