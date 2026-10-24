import json

import requests

from app.utils import clean_original_figma_json


def fetch_figma_node(base_url: str, file_key: str, token: str, node_id_ref: str) -> dict:
    """
    Запрашивает структуру ноды из Figma API.
    Возвращает словарь с результатом:
    {
        "status": "success" | "not_found" | "error",
        "optimized_structure": dict | None,
        "prompt_addition": str | None,
        "error_code": int | str | None
    }
    """
    node_id_cleaned = node_id_ref.strip().replace("-", ":")
    
    try:
        figma_url = f"{cfg.figma_base_url}{cfg.figma_file_key}/nodes?ids={node_id_cleaned}"
        figma_headers = {"X-Figma-Token": cfg.figma_token}
        figma_res = requests.get(figma_url, headers=figma_headers, timeout=10)
        
        if figma_res.status_code == 200:
            figma_data = figma_res.json()
            raw_node = figma_data.get("nodes", {}).get(node_id_cleaned, {}).get("document", {})
            
            if raw_node:
                optimized = clean_original_figma_json(raw_node)
                prompt_add = f"\n\n[Figma Context]:\n{json.dumps(optimized, ensure_ascii=False)}"
                return {
                    "status": "success",
                    "optimized_structure": optimized,
                    "prompt_addition": prompt_add,
                    "error_code": None
                }
            else:
                return {"status": "not_found", "optimized_structure": None, "prompt_addition": None, "error_code": None}
        else:
            return {
                "status": "error", 
                "optimized_structure": None, 
                "prompt_addition": None, 
                "error_code": figma_res.status_code
            }
            
    except Exception:
        return {
            "status": "error", 
            "optimized_structure": None, 
            "prompt_addition": None, 
            "error_code": "Exception"
        }