import json

import requests


def refine_user_prompt(ollama_url, model_name, system_prompt, logger,
                       payload_options, payload_stream, payload_format, keep_alive,
                       user_request, optimized_node=None) -> str:
    
    logger.log("agents", "prompt_optimizer.start", agent_name="Агент 0 (Рефайнер)")

    analysis_payload = {"raw_user_request": user_request}
    if optimized_node:
        analysis_payload["detected_ui_layout_structure"] = optimized_node

    readable_system_prompt = json.dumps(system_prompt, ensure_ascii=False, indent=2)

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": readable_system_prompt},
            {"role": "user", "content": "Analyze this context and create a highly structured, professional engineering prompt/specification:\n" + json.dumps(analysis_payload, ensure_ascii=False, indent=2)}
        ],
        "stream": payload_stream,
        "format": payload_format,
        "options": payload_options,
        "keep_alive": keep_alive
    }

    try:
        response = requests.post(ollama_url, json=payload, headers={"Content-Type": "application/json"}, timeout=(5, 240))
        if response.status_code != 200:
            logger.log("agents", "prompt_optimizer.error", agent_name="Агент 0 (Рефайнер)", error=f"HTTP {response.status_code}")
            return user_request

        raw = response.json()
        content = raw.get("message", {}).get("content", "")

        # Проверяем, не вернула ли Ollama сразу готовый dict
        if isinstance(content, dict):
            refined_prompt = content.get("specification", "").strip()
            if refined_prompt:
                logger.log("agents", "prompt_optimizer.success", agent_name="Агент 0 (Рефайнер)")
                return refined_prompt
            # Если в dict нет ключа specification, превращаем в строку для логов
            content = json.dumps(content)

        # Если это строка, обрабатываем как раньше
        if isinstance(content, str):
            content = content.strip()
            if not content:
                logger.log("agents", "prompt_optimizer.error", agent_name="Агент 0 (Рефайнер)", error="Пустой ответ")
                return user_request

            try:
                parsed = json.loads(content)
                # Безопасно получаем значение, по умолчанию пустая строка
                raw_spec = parsed.get("specification", "")
                
                # Если specification внутри JSON оказалась словарем, переводим в строку или берем текст
                if isinstance(raw_spec, dict):
                    refined_prompt = json.dumps(raw_spec, ensure_ascii=False)
                elif isinstance(raw_spec, str):
                    refined_prompt = raw_spec.strip()
                else:
                    refined_prompt = str(raw_spec).strip() if raw_spec is not None else ""
                    
            except json.JSONDecodeError:
                refined_prompt = content
            
            if not refined_prompt or len(refined_prompt) < 5:
                logger.log("agents", "prompt_optimizer.error", agent_name="Агент 0 (Рефайнер)", error="Мусорный ответ")
                return user_request

            logger.log("agents", "prompt_optimizer.success", agent_name="Агент 0 (Рефайнер)")
            print(f"ТЗ: ${refined_prompt}")
            return refined_prompt

        # На всякий случай, если пришел вообще непонятный тип (int, list и т.д.)
        logger.log("agents", "prompt_optimizer.error", agent_name="Агент 0 (Рефайнер)", error=f"Неизвестный тип ответа: {type(content)}")
        return user_request

    except Exception as e:
        logger.log("agents", "prompt_optimizer.error", agent_name="Агент 0 (Рефайнер)", error=str(e))
        return user_request