import os
import sys

import pytest

from app.config import load_config

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


MINIMAL_TOML = """
[ollama.global]
stream = false
format = "json"
default_keep_alive = 0

[ollama.agents.refiner]
keep_alive = 0
temperature = 0.1
num_predict = 1024
num_ctx = 8192
"""


def _write_toml(tmp_path, content: str) -> str:
    f = tmp_path / "config.toml"
    f.write_text(content, encoding="utf-8")
    return str(f)


# ---------- Успешные сценарии ----------

def test_load_config_ok(tmp_path):
    path = _write_toml(tmp_path, MINIMAL_TOML)

    cfg = load_config(
        toml_path=path,
        env={"MODELS": "llama3.2:3b,qwen2.5-coder:7b"},
    )

    assert cfg.models == ["llama3.2:3b", "qwen2.5-coder:7b"]
    assert cfg.stream is False
    assert cfg.format == "json"
    assert cfg.ollama_api_url == "http://localhost:11434"
    assert cfg.figma_token == ""


def test_models_strip_spaces(tmp_path):
    path = _write_toml(tmp_path, MINIMAL_TOML)

    cfg = load_config(
        toml_path=path,
        env={"MODELS": "  a , b ,  c  "},
    )

    assert cfg.models == ["a", "b", "c"]


def test_agent_keep_alive_overrides_global(tmp_path):
    toml = """
[ollama.global]
default_keep_alive = "5m"

[ollama.agents.refiner]
keep_alive = "1h"
temperature = 0.1
"""
    path = _write_toml(tmp_path, toml)

    cfg = load_config(toml_path=path, env={"MODELS": "m1"})

    assert cfg.refiner.keep_alive == "1h"
    assert cfg.figma.keep_alive == "5m"
    assert cfg.vue.keep_alive == "5m"


def test_missing_agent_section_gives_defaults(tmp_path):
    path = _write_toml(tmp_path, MINIMAL_TOML)

    cfg = load_config(toml_path=path, env={"MODELS": "m1"})

    assert cfg.figma.keep_alive == 0
    assert cfg.figma.options == {}
    assert cfg.vue.options == {}


def test_missing_global_section_uses_defaults(tmp_path):
    toml = """
[ollama.agents.refiner]
temperature = 0.5
"""
    path = _write_toml(tmp_path, toml)

    cfg = load_config(toml_path=path, env={"MODELS": "m1"})

    assert cfg.stream is False
    assert cfg.format == "json"
    assert cfg.refiner.keep_alive == 0

def test_real_config_toml_is_valid():
    """Проверяет, что настоящий config.toml в проекте парсится без ошибок."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Возможные пути, где может лежать файл
    possible_paths = [
        os.path.join(project_root, "app", "llm", "config.toml"),
        os.path.join(project_root, "app", "config.toml"),
        os.path.join(project_root, "config.toml"),
    ]
    
    real_toml_path = next((p for p in possible_paths if os.path.exists(p)), None)
    
    if not real_toml_path:
        pytest.skip("Real config.toml not found in expected locations.")
        return

    # Если нашли - тестируем
    try:
        cfg = load_config(
            toml_path=real_toml_path,
            env={"MODELS": "dummy_model"}
        )
    except Exception as e:
        pytest.fail(f"Real config.toml is broken ({real_toml_path}): {e}")

    assert isinstance(cfg.stream, bool), "stream must be bool"
    assert isinstance(cfg.format, str), "format must be str"
    
    # Проверяем, что у агентов параметры имеют правильный тип (если они заданы)
    if "temperature" in cfg.refiner.options:
        assert isinstance(cfg.refiner.options["temperature"], float), "refiner temperature must be float"
    if "num_predict" in cfg.figma.options:
        assert isinstance(cfg.figma.options["num_predict"], int), "figma num_predict must be int"
        
# ---------- Ошибки ----------

def test_empty_models_raises(tmp_path):
    path = _write_toml(tmp_path, MINIMAL_TOML)

    with pytest.raises(ValueError, match="MODELS is empty"):
        load_config(toml_path=path, env={})


def test_whitespace_only_models_raises(tmp_path):
    path = _write_toml(tmp_path, MINIMAL_TOML)

    with pytest.raises(ValueError, match="MODELS is empty"):
        load_config(toml_path=path, env={"MODELS": " , , "})


def test_missing_toml_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(
            toml_path=str(tmp_path / "nope.toml"),
            env={"MODELS": "m1"},
        )


def test_broken_toml_raises(tmp_path):
    path = _write_toml(tmp_path, "this is = not [ valid toml")

    with pytest.raises(tomllib.TOMLDecodeError):
        load_config(toml_path=path, env={"MODELS": "m1"})