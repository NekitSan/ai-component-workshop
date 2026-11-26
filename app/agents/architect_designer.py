import json

import requests


def design_architect_nodes(
    ollama_url,
    model_name,
    system_prompt,
    templates,
    logger,
    payload_options,
    payload_stream,
    payload_format,
    keep_alive,
    user_request,
    context_providers: dict = None,
) -> dict:

    logger.log("agents", "json_designer.start", agent_name="Агент 2 (Проектировщик)")

    user_payload = {
        "TASK_INSTRUCTION": f"Generate a UI component structure based on this specification:\n{user_request}"
    }

    if context_providers:
            for provider_name, data in context_providers.items():
                if data:
                    user_payload[provider_name] = data

                    
    if templates:
        user_payload["REFERENCE_TEMPLATES_TO_CLONE_PROPERTIES_FROM"] = templates

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": json.dumps(system_prompt, ensure_ascii=False)},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "stream": payload_stream,
        "format": payload_format,
        "options": payload_options,
        "keep_alive": keep_alive
    }

    try:
        response = requests.post(ollama_url, json=payload, headers={"Content-Type": "application/json"}, timeout=(5, 300))
        if response.status_code != 200:
            logger.log("agents", "json_designer.error", agent_name="Агент 2 (Проектировщик)", error=f"HTTP {response.status_code}")
            return {}

        ai_response = response.json().get("message", {}).get("content", "")
        
        if isinstance(ai_response, dict):
            result_json = ai_response
        elif isinstance(ai_response, str):
            ai_response = ai_response.strip()
            start_idx, end_idx = ai_response.find("{"), ai_response.rfind("}")
            raw_str = ai_response[start_idx : end_idx + 1] if start_idx != -1 else ai_response
            result_json = json.loads(raw_str)
        else:
            logger.log("agents", "json_designer.error", agent_name="Агент 2 (Проектировщик)", error=f"Неизвестный тип: {type(ai_response)}")
            return {}
        
        logger.log("agents", "json_designer.success", agent_name="Агент 2 (Проектировщик)")
        return result_json
    except Exception as e:
        logger.log("agents", "json_designer.error", agent_name="Агент 2 (Проектировщик)", error=str(e))
        return {}
