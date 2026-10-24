import json

import requests


def generate_vue_component(ollama_url, model_name, system_prompt, logger, 
                           payload_options, payload_stream, payload_format, keep_alive,
                           user_request, architect_nodes) -> str:
    if not architect_nodes:
        return "// Ошибка: Исходный каркас Архитектора пуст."

    logger.log("agents", "code_generator.start", agent_name="Агент 3 (Vue-кодер)")

    user_payload = {
        "original_user_request": user_request,
        "target_architect_nodes_structure": architect_nodes
    }

    readable_system_prompt = json.dumps(system_prompt, ensure_ascii=False, indent=2)
    readable_user_payload = json.dumps(user_payload, ensure_ascii=False, indent=2)

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": readable_system_prompt},
            {"role": "user", "content": f"Figma structure to translate:\n{readable_user_payload}"}
        ],
        "stream": payload_stream,
        "format": payload_format,
        "options": payload_options,
        "keep_alive": keep_alive
    }

    try:
        response = requests.post(ollama_url, json=payload, headers={"Content-Type": "application/json"}, timeout=(5, 180))
        if response.status_code != 200:
            logger.log("agents", "code_generator.error", agent_name="Агент 3 (Vue-кодер)", error=f"HTTP {response.status_code}")
            return ""

        ai_response = response.json().get("message", {}).get("content", "")
        if isinstance(ai_response, dict):
            # Если Ollama сразу вернула JSON-объект
            result_json = ai_response
        else:
            # Если это строка (стандартный случай)
            ai_response = ai_response.strip()
            start_idx, end_idx = ai_response.find("{"), ai_response.rfind("}")
            raw_str = ai_response[start_idx : end_idx + 1] if start_idx != -1 else ai_response
            result_json = json.loads(raw_str)
        start_idx, end_idx = ai_response.find("{"), ai_response.rfind("}")
        result_json = json.loads(ai_response[start_idx : end_idx + 1] if start_idx != -1 else ai_response)
        
        logger.log("agents", "code_generator.success", agent_name="Агент 3 (Vue-кодер)")

        code = result_json.get("vue_code_raw", "")
        # Если это строка с экранированными \n, заменяем их на реальные переносы
        if isinstance(code, str):
            code = code.replace('\\n', '\n').replace('\\"', '"')
        return code
    except Exception as e:
        logger.log("agents", "code_generator.error", agent_name="Агент 3 (Vue-кодер)", error=str(e))
        return ""