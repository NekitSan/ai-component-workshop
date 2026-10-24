import json
import os

from flask import Flask

from app.config import load_config
from app.utils import StatusLogger


def create_app():
    app = Flask(__name__)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        cfg = load_config()
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        raise

    llm_dir = os.path.join(app.root_path, "llm")
    
    def _load_json(name):
        with open(os.path.join(llm_dir, name), "r", encoding="utf-8-sig") as f:
            return json.load(f)

    # Статусы вынесены в отдельный логгер
    logger = StatusLogger(os.path.join(llm_dir, "statuses.json"))

    llm_data = {
        "architect_prompt": _load_json("prompts/architect_system_prompt.json"),
        "refiner_prompt": _load_json("prompts/refiner_system_prompt.json"),
        "vue_prompt": _load_json("prompts/vue_system_prompt.json"),
        "architect_examples": _load_json("examples/architect_examples.json"),
    }

    app.config['APP_CONFIG'] = cfg
    app.config['LLM_DATA'] = llm_data
    app.config['LOGGER'] = logger

    from app.routes import bp
    app.register_blueprint(bp)

    return app