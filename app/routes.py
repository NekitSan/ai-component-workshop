import copy
import json

import requests
from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    send_from_directory,
    stream_with_context,
)

from app.agents import (
    design_architect_nodes,
    generate_vue_component,
    refine_user_prompt,
)
from app.services import fetch_figma_node
from app.utils import clean_nodes_for_coder, clean_original_figma_json

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET'])
def index():
    return send_from_directory(current_app.template_folder, 'index.html')

@bp.route('/favicon.ico')
def favicon():
    return '', 204

@bp.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json() or {}
    user_prompt = data.get("prompt", "")
    svg_ref = data.get("svg", None)
    node_id_ref = data.get("node_id", None)
    
    if not user_prompt:
        return jsonify({"error": "Missing prompt parameter"}), 400

    cfg = current_app.config['APP_CONFIG']
    llm_data = current_app.config['LLM_DATA']
    logger = current_app.config['LOGGER']

    def generate():
        nonlocal user_prompt
        optimized_node_structure = None

        # Хелпер для отправки событий (он уже есть в вашем коде)
        def sse_event(status_key: str, **kwargs):
            event_data = logger.get_event("pipeline", status_key, **kwargs)
            payload = {
                'type': 'progress',
                'percent': event_data['percent'],
                'status': event_data['text']
            }
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # 1. Старт
        yield sse_event("start")

        yield sse_event("context_init")

        # 2. Ветвление режимов
        if node_id_ref:
            # Режим: Figma API
            node_id_cleaned = node_id_ref.strip().replace("-", ":")
            yield sse_event("figma_request", node_id=node_id_cleaned)

            # Вызываем сервис
            result = fetch_figma_node(base_url=cfg.figma_base_url, file_key=cfg.figma_file_key, token=cfg.figma_token, node_id_ref=node_id_ref)

            if result["status"] == "success":
                optimized_node_structure = result["optimized_structure"]
                user_prompt += result["prompt_addition"]
                yield sse_event("figma_success")
                
            elif result["status"] == "not_found":
                yield sse_event("figma_not_found")
                
            elif result["status"] == "error":
                yield sse_event("figma_error", code=result["error_code"])

        elif svg_ref:
            # Режим: SVG Референс
            yield sse_event("svg_reference")
        else:
            # Режим: Только текст
            yield sse_event("no_context")


        # 3. Агент 0 (Рефайнер)
        yield sse_event("analysis")
        
        user_prompt = refine_user_prompt(
            ollama_url=cfg.ollama_api_url,
            model_name=cfg.models[1],
            system_prompt=llm_data['refiner_prompt'],
            logger=logger,
            payload_options=cfg.refiner.options,
            payload_stream=cfg.stream,
            payload_format=cfg.format,
            keep_alive=cfg.refiner.keep_alive,
            user_request=user_prompt,
            optimized_node=optimized_node_structure
        )

        # 4. Агент 1 (Figma)
        yield sse_event("figma_generation")
        
        design_architect = design_architect_nodes(
            ollama_url=cfg.ollama_api_url,
            model_name=cfg.models[0],
            system_prompt=llm_data['architect_prompt'],
            templates=llm_data['architect_examples'],
            logger=logger,
            payload_options=cfg.architect.options,
            payload_stream=cfg.stream,
            payload_format=cfg.format,
            keep_alive=cfg.architect.keep_alive,
            user_request=user_prompt,
            reference_svg=svg_ref
        )
        
        if not design_architect:
            yield f"data: {json.dumps({'type': 'error', 'text': 'Ошибка Figma-нод'}, ensure_ascii=False)}\n\n"
            return

        # 5. Очистка
        yield sse_event("figma_cleaned")
        light_design_architect = clean_nodes_for_coder(copy.deepcopy(design_architect))

        # 6. Агент 2 (Vue)
        yield sse_event("vue_generation")
        
        vue_code = generate_vue_component(
            ollama_url=cfg.ollama_api_url,
            model_name=cfg.models[1],
            system_prompt=llm_data['vue_prompt'],
            logger=logger,
            payload_options=cfg.vue.options,
            payload_stream=cfg.stream,
            payload_format=cfg.format,
            keep_alive=cfg.vue.keep_alive,
            user_request=user_prompt,
            architect_nodes=light_design_architect
        )

        # 7. Сборка
        yield sse_event("assembly")
        
        response_payload = {
            "figma_config": {"file_key": cfg.figma_file_key, "figma_token_header": "X-Figma-Token"},
            "nodes": {"figma_nodes": design_architect, "vue_code": vue_code}
        }
        
        # 8. Готово
        yield sse_event("done")
        yield f"data: {json.dumps({'type': 'done', 'result': response_payload}, ensure_ascii=False)}\n\n"

    response = Response(stream_with_context(generate()), content_type='text/event-stream')
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
