import copy


def clean_original_figma_json(raw_node: dict) -> dict:
    """
    Агрессивно удаляет технический шум Figma API, но сохраняет 
    абсолютные координаты, размеры и логический смысл иконок.
    """
    if not isinstance(raw_node, dict):
        return raw_node

    node_type = raw_node.get("type", "")
    
    # Вместо удаления векторов, превращаем их в компактную текстовую метку для ИИ
    if node_type in ["VECTOR", "BOOLEAN_OPERATION"]:
        return {
            "type": "ICON",
            "name": raw_node.get("name", "icon")
        }
        
    if node_type == "GROUP":
        # Группы часто содержат полезных детей, пропускаем их очистку дальше, не удаляя
        pass

    cleaned = {}
    
    # Расширяем список ключей, добавляя размеры и абсолютные координаты
    allowed_keys = [
        "type", "name", "layoutMode", "itemSpacing", "characters",
        "paddingLeft", "paddingRight", "paddingTop", "paddingBottom",
        "primaryAxisSizingMode", "counterAxisSizingMode", "children",
        "fills", "style", "cornerRadius",
        "width", "height", "x", "y", "absolutePositioning" # <-- ДОБАВЛЕНО
    ]

    for k, v in raw_node.items():
        if k in allowed_keys:
            if k == "children" and isinstance(v, list):
                cleaned_children = [clean_original_figma_json(child) for child in v]
                cleaned[k] = [child for child in cleaned_children if child is not None]
            elif k == "fills" and isinstance(v, list):
                compact_fills = []
                for fill in v:
                    if fill.get("visible", True) is not False and "color" in fill:
                        c = fill["color"]
                        compact_fills.append({
                            "type": fill.get("type"),
                            "rgb": f"r:{round(c.get('r',0),2)} g:{round(c.get('g',0),2)} b:{round(c.get('b',0),2)}"
                        })
                if compact_fills:
                    cleaned[k] = compact_fills
            elif k == "style" and isinstance(v, dict):
                cleaned[k] = {
                    "fontSize": v.get("fontSize"),
                    "fontWeight": v.get("fontWeight"),
                    "fontFamily": v.get("fontFamily")
                }
            else:
                cleaned[k] = v

    return cleaned


def clean_nodes_for_coder(figma_structure: dict) -> dict:
    """Рекурсивно удаляет тяжелые графические данные из Figma API, разгружая контекст кодера"""
    if not isinstance(figma_structure, dict):
        return figma_structure
    cleaned = {}
    important_keys = ["type", "layoutMode", "itemSpacing", "characters", "children", "style", "fills", "cornerRadius"]
    for k, v in figma_structure.items():
        if k in important_keys:
            if k == "children" and isinstance(v, list):
                cleaned[k] = [clean_nodes_for_coder(child) for child in v]
            else:
                cleaned[k] = v
    return cleaned