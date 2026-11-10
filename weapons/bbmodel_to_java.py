#!/usr/bin/env python3
"""Конвертирует Bedrock-модель Blockbench (.bbmodel, box UV) в Java-модель предмета.

Запуск: python3 bbmodel_to_java.py  (из папки weapons/, без аргументов — пути ниже).

Что делает с моделью (у Java-моделей свои ограничения):
- координаты Blockbench сдвигаются в пространство Java (центр модели около 8,8,8) и должны
  уложиться в -16..32 — иначе клиент не загрузит модель;
- inflate (в Java его нет) — расширяем куб на эту величину во все стороны;
- поворот элемента в Java — только -45/-22.5/0/22.5/45 по одной оси: прочие углы округляются
  до ближайшего допустимого (-20 → -22.5, на глаз не отличить);
- UV в пикселях текстуры 128x128 переводятся в шкалу 0..16.

Пишет базовую модель с переменной текстуры #gun и по модели на каждый цвет стороны дуэли
(red — рубиновая текстура, blue — обычная), плюс файлы items/ для компонента item_model.
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "flintlock.bbmodel")
ASSETS = os.path.join(HERE, "assets", "hypetrain")
NAME = "flintlock"
# Сдвиг из пространства Blockbench в пространство Java (подобран, чтобы модель влезла в -16..32).
OFFSET = (4.0, 8.0, 8.0)
ALLOWED_ANGLES = (-45.0, -22.5, 0.0, 22.5, 45.0)
# Цвет стороны дуэли → имя текстуры внутри .bbmodel.
VARIANTS = {"red": "ruby_pistol_texture.png", "blue": "pistol_texture.png"}

# Положение в руке/GUI. Подобрано вслепую — подкручивать в Blockbench (вкладка Display) по
# сгенерированному models/item/flintlock.json и переносить цифры сюда.
DISPLAY = {
    "firstperson_righthand": {"rotation": [0, -90, 0], "translation": [1, 2, -2], "scale": [0.32, 0.32, 0.32]},
    "firstperson_lefthand": {"rotation": [0, 90, 0], "translation": [1, 2, -2], "scale": [0.32, 0.32, 0.32]},
    "thirdperson_righthand": {"rotation": [0, -90, 0], "translation": [0, 3, 1], "scale": [0.32, 0.32, 0.32]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [0, 3, 1], "scale": [0.32, 0.32, 0.32]},
    "gui": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.34, 0.34, 0.34]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.25, 0.25, 0.25]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
}


def snap(angle):
    return min(ALLOWED_ANGLES, key=lambda allowed: abs(allowed - angle))


def r(value):
    return round(value, 4)


def convert_element(element, uv_scale):
    inflate = element.get("inflate") or 0.0
    origin_from = [element["from"][i] - inflate + OFFSET[i] for i in range(3)]
    origin_to = [element["to"][i] + inflate + OFFSET[i] for i in range(3)]
    for value in origin_from + origin_to:
        if value < -16 or value > 32:
            raise SystemExit(f"Элемент вылез за -16..32: {element['from']} {element['to']} → {value}")
    out = {"from": [r(v) for v in origin_from], "to": [r(v) for v in origin_to], "faces": {}}

    rotation = element.get("rotation")
    if rotation and any(rotation):
        axes = [i for i in range(3) if rotation[i]]
        if len(axes) > 1:
            raise SystemExit(f"Поворот по нескольким осям не поддерживается Java: {rotation}")
        axis = axes[0]
        pivot = element.get("origin", [0, 0, 0])
        out["rotation"] = {
            "angle": snap(rotation[axis]),
            "axis": "xyz"[axis],
            "origin": [r(pivot[i] + OFFSET[i]) for i in range(3)],
        }

    for face, data in element["faces"].items():
        if data.get("texture") is None:
            continue
        out["faces"][face] = {"uv": [r(v * uv_scale) for v in data["uv"]], "texture": "#gun"}
    return out


def main():
    with open(SOURCE, encoding="utf-8") as file:
        model = json.load(file)
    width = model["resolution"]["width"]
    uv_scale = 16.0 / width

    textures_dir = os.path.join(ASSETS, "textures", "item")
    models_dir = os.path.join(ASSETS, "models", "item")
    items_dir = os.path.join(ASSETS, "items")
    for directory in (textures_dir, models_dir, items_dir):
        os.makedirs(directory, exist_ok=True)

    by_name = {texture["name"]: texture for texture in model["textures"]}
    for color, texture_name in VARIANTS.items():
        source = by_name[texture_name]["source"]
        with open(os.path.join(textures_dir, f"{NAME}_{color}.png"), "wb") as file:
            file.write(base64.b64decode(source.split(",", 1)[1]))

    base = {
        "textures": {"gun": f"hypetrain:item/{NAME}_red", "particle": f"hypetrain:item/{NAME}_red"},
        "elements": [convert_element(element, uv_scale) for element in model["elements"]],
        "display": DISPLAY,
    }
    with open(os.path.join(models_dir, f"{NAME}.json"), "w", encoding="utf-8") as file:
        json.dump(base, file, indent=2)

    for color in VARIANTS:
        variant = {
            "parent": f"hypetrain:item/{NAME}",
            "textures": {"gun": f"hypetrain:item/{NAME}_{color}", "particle": f"hypetrain:item/{NAME}_{color}"},
        }
        with open(os.path.join(models_dir, f"{NAME}_{color}.json"), "w", encoding="utf-8") as file:
            json.dump(variant, file, indent=2)
        item = {"model": {"type": "minecraft:model", "model": f"hypetrain:item/{NAME}_{color}"}}
        with open(os.path.join(items_dir, f"{NAME}_{color}.json"), "w", encoding="utf-8") as file:
            json.dump(item, file, indent=2)

    print(f"Готово: {len(base['elements'])} элементов, варианты {', '.join(VARIANTS)}")


if __name__ == "__main__":
    main()
