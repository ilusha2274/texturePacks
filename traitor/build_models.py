#!/usr/bin/env python3
"""Предметы «Предателя»: Java-модели из .bbmodel (формат Java Block/Item) + иконка шприца.

Запуск: python3 -I build_models.py  (из папки traitor/, без аргументов - пути ниже).

- knife.bbmodel   -> traitorgame:traitor_knife  (клинок предателя, NETHERITE_SWORD в плагине)
- syringe.bbmodel -> traitorgame:poison_syringe (шприц с ядом, BLAZE_ROD в плагине)

Модели уже в формате Java (model_format java_block): координаты и UV переносятся как есть, у
каждого куба своя мини-текстура 16x16 - каждая пишется отдельным PNG и подставляется как #N.
Положения в руке/GUI (display) - те, что настроил автор модели в Blockbench.

У шприца в инвентаре плоская иконка: шприц адреналина Маньяка (maniac/.../adrenaline.png) с
жидкостью, перекрашенной из розовой в зелёную (яд). В руке, на земле и т.п. - 3D-модель:
items/poison_syringe.json выбирает модель по контексту отображения (minecraft:display_context).
"""
import base64
import json
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets", "traitorgame")
NAMESPACE = "traitorgame"
MODELS = {"traitor_knife": "knife.bbmodel", "poison_syringe": "syringe.bbmodel"}
SYRINGE_ICON_SOURCE = os.path.join(HERE, "..", "maniac", "assets", "hypetrain", "textures", "item", "maniac",
                                   "adrenaline.png")
# Розовая жидкость адреналина -> зелёная той же яркости (светлый блик, середина, тень).
POISON_RECOLOR = {
    (255, 179, 239): (186, 255, 170),
    (255, 95, 210): (92, 220, 72),
    (194, 50, 156): (38, 140, 40),
}
# Ключи элемента/грани Blockbench, которые есть в Java-модели.
FACE_KEYS = ("uv", "rotation", "cullface", "tintindex")


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def convert(name, source):
    with open(os.path.join(HERE, source), encoding="utf-8") as file:
        model = json.load(file)
    if model["meta"].get("model_format") != "java_block":
        raise SystemExit(f"{source}: ожидалась модель в формате Java Block/Item")
    textures = {}
    for index, texture in enumerate(model["textures"]):
        png = base64.b64decode(texture["source"].split(",", 1)[1])
        if png[:8] != b"\x89PNG\r\n\x1a\n":
            raise SystemExit(f"{source}: текстура {index} не PNG")
        path = os.path.join(ASSETS, "textures", "item", name, f"{index}.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            file.write(png)
        textures[str(index)] = f"{NAMESPACE}:item/{name}/{index}"
    textures["particle"] = textures["0"]

    elements = []
    for element in model["elements"]:
        if element.get("type", "cube") != "cube" or not element.get("export", True):
            continue
        for value in element["from"] + element["to"]:
            if value < -16 or value > 32:
                raise SystemExit(f"{source}: элемент вылез за -16..32: {element['from']} {element['to']}")
        out = {"from": element["from"], "to": element["to"], "faces": {}}
        rotation = element.get("rotation")
        if rotation and any(rotation):
            axes = [i for i in range(3) if rotation[i]]
            if len(axes) > 1:
                raise SystemExit(f"{source}: поворот по нескольким осям не поддерживается Java")
            out["rotation"] = {"angle": rotation[axes[0]], "axis": "xyz"[axes[0]], "origin": element["origin"]}
        if element.get("light_emission"):
            out["light_emission"] = element["light_emission"]
        for face, data in element["faces"].items():
            if data.get("texture") is None:
                continue
            converted = {key: data[key] for key in FACE_KEYS if key in data}
            converted["texture"] = f"#{data['texture']}"
            out["faces"][face] = converted
        elements.append(out)

    write_json(os.path.join(ASSETS, "models", "item", f"{name}.json"),
               {"textures": textures, "elements": elements, "display": model.get("display", {})})
    print(f"{name}: {len(elements)} элементов, {len(model['textures'])} текстур")


def read_png(path):
    data = open(path, "rb").read()
    offset, idat = 8, b""
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if (depth, color, interlace) != (8, 6, 0):
                raise SystemExit(f"{path}: ожидался RGBA 8 бит без чересстрочности")
        elif kind == b"IDAT":
            idat += body
    raw, stride, rows, previous, pos = zlib.decompress(idat), width * 4, [], bytearray(width * 4), 0
    for _ in range(height):
        kind, line = raw[pos], bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for x in range(stride):
            left = line[x - 4] if x >= 4 else 0
            up, corner = previous[x], previous[x - 4] if x >= 4 else 0
            if kind == 1:
                line[x] = (line[x] + left) & 255
            elif kind == 2:
                line[x] = (line[x] + up) & 255
            elif kind == 3:
                line[x] = (line[x] + (left + up) // 2) & 255
            elif kind == 4:
                pa, pb, pc = abs(up - corner), abs(left - corner), abs(left + up - 2 * corner)
                line[x] = (line[x] + (left if pa <= pb and pa <= pc else up if pb <= pc else corner)) & 255
        rows.append([tuple(line[i:i + 4]) for i in range(0, stride, 4)])
        previous = line
    return width, height, rows


def write_png(path, width, height, rows):
    raw = b"".join(b"\x00" + bytes(channel for pixel in row for channel in pixel) for row in rows)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
                   + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def syringe_icon():
    width, height, rows = read_png(SYRINGE_ICON_SOURCE)
    recolored = [[POISON_RECOLOR.get(pixel[:3], pixel[:3]) + (pixel[3],) for pixel in row] for row in rows]
    write_png(os.path.join(ASSETS, "textures", "item", "poison_syringe_icon.png"), width, height, recolored)
    write_json(os.path.join(ASSETS, "models", "item", "poison_syringe_icon.json"),
               {"parent": "minecraft:item/handheld", "textures": {"layer0": f"{NAMESPACE}:item/poison_syringe_icon"}})


def items():
    write_json(os.path.join(ASSETS, "items", "traitor_knife.json"),
               {"model": {"type": "minecraft:model", "model": f"{NAMESPACE}:item/traitor_knife"}})
    # В инвентаре/хотбаре (gui) - плоская иконка, во всех остальных местах - 3D-модель.
    write_json(os.path.join(ASSETS, "items", "poison_syringe.json"), {"model": {
        "type": "minecraft:select",
        "property": "minecraft:display_context",
        "cases": [{"when": "gui", "model": {"type": "minecraft:model", "model": f"{NAMESPACE}:item/poison_syringe_icon"}}],
        "fallback": {"type": "minecraft:model", "model": f"{NAMESPACE}:item/poison_syringe"},
    }})


def main():
    for name, source in MODELS.items():
        convert(name, source)
    syringe_icon()
    items()
    print("Готово:", ASSETS)


if __name__ == "__main__":
    main()
