import json

import pytest

from app.utils.status_logger import StatusLogger


@pytest.fixture
def sample_statuses(tmp_path):
    """Создает временный statuses.json для тестов."""
    data = {
        "pipeline": {
            "start": "🚀 Запуск...",
            "figma_request": "📡 Запрос: {node_id}",
            "nested": {
                "deep": {
                    "value": "Глубокое значение"
                }
            }
        },
        "agents": {
            "refiner": {
                "start": "📑 [{agent_name}] Старт",
                "error": "❌ Ошибка: {error}"
            }
        }
    }
    p = tmp_path / "statuses.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(p)

def test_get_simple_key(sample_statuses):
    logger = StatusLogger(sample_statuses, use_timestamps=False)
    assert logger.get("pipeline", "start") == "🚀 Запуск..."

def test_get_nested_key(sample_statuses):
    logger = StatusLogger(sample_statuses, use_timestamps=False)
    # Проверяем вложенность pipeline.nested.deep.value
    assert logger.get("pipeline.nested.deep", "value") == "Глубокое значение"

def test_get_with_placeholder(sample_statuses):
    logger = StatusLogger(sample_statuses, use_timestamps=False)
    text = logger.get("pipeline", "figma_request", node_id="1496:2450")
    assert text == "📡 Запрос: 1496:2450"

def test_get_missing_placeholder(sample_statuses):
    logger = StatusLogger(sample_statuses, use_timestamps=False)
    # Передаем неверный ключ плейсхолдера, чтобы проверить обработку KeyError
    text = logger.get("pipeline", "figma_request", wrong_key="123")
    assert "missing placeholder: 'node_id'" in text

def test_get_missing_key(sample_statuses):
    logger = StatusLogger(sample_statuses, use_timestamps=False)
    # Такого ключа нет в JSON
    text = logger.get("pipeline", "non_existent")
    assert text == "[missing status: pipeline.non_existent]"

def test_log_with_timestamps(sample_statuses, capsys):
    logger = StatusLogger(sample_statuses, use_timestamps=True)
    result = logger.log("agents", "refiner.start", agent_name="Агент 0")
    
    # Проверяем, что в выводе есть время в формате [HH:MM:SS]
    captured = capsys.readouterr()
    assert "📑 [Агент 0] Старт" in captured.out
    assert "[" in captured.out and "]" in captured.out  # Временная метка

def test_log_without_timestamps(sample_statuses, capsys):
    logger = StatusLogger(sample_statuses, use_timestamps=False)
    result = logger.log("agents", "refiner.error", error="Timeout")
    
    captured = capsys.readouterr()
    assert captured.out.strip() == "❌ Ошибка: Timeout"
    assert result == "❌ Ошибка: Timeout"