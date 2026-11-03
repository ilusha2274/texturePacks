#!/bin/bash
# Собирает maniac-pack.zip и печатает sha1 для server/maniac/server.properties.
#
# Предметы плагина ссылаются на модели hypetrain:maniac/<id>. Для каждого скрипт смотрит, лежит ли
# своя текстура в assets/hypetrain/textures/item/maniac/<id>.png: есть - предмет рисуется ею, нет -
# пак временно отдаёт ванильную модель (чтобы в игре не было фиолетово-чёрных кубов).
# Нарисовал PNG - положи его туда и перезапусти скрипт, править JSON руками не нужно.
cd "$(dirname "$0")"
set -e

TEXTURES=assets/hypetrain/textures/item/maniac
ITEMS=assets/hypetrain/items/maniac
mkdir -p "$ITEMS"

# id предмета -> ванильная модель-заглушка
simple_item() {
    local id=$1 fallback=$2 model
    if [ -f "$TEXTURES/$id.png" ]; then
        model="hypetrain:item/maniac/$id"
        echo "  $id: своя текстура"
    else
        model="$fallback"
        echo "  $id: заглушка $fallback (нет $TEXTURES/$id.png)"
    fi
    cat > "$ITEMS/$id.json" <<EOF
{
  "model": {
    "type": "minecraft:model",
    "model": "$model"
  }
}
EOF
}

simple_item medkit     minecraft:item/golden_apple
simple_item adrenaline minecraft:item/dragon_breath
simple_item fuel       minecraft:item/lava_bucket
simple_item gas_wrench minecraft:item/iron_hoe
simple_item sword      minecraft:item/stone_sword
simple_item defibrillator minecraft:item/heart_of_the_sea
simple_item maniac_hook minecraft:item/fishing_rod

# Арбалет выдаётся уже заряженным и пропадает после выстрела, поэтому важны два вида: заряжен
# (crossbow_arrow.png) и пустой (crossbow_standby.png). Натяжение не рисуем - его не бывает.
if [ -f "$TEXTURES/crossbow_arrow.png" ]; then
    arrow=hypetrain:item/maniac/crossbow_arrow
    echo "  crossbow (заряжен): своя текстура"
else
    arrow=minecraft:item/crossbow_arrow
    echo "  crossbow (заряжен): заглушка (нет $TEXTURES/crossbow_arrow.png)"
fi
if [ -f "$TEXTURES/crossbow_standby.png" ]; then
    standby=hypetrain:item/maniac/crossbow_standby
    echo "  crossbow (пустой): своя текстура"
else
    standby=minecraft:item/crossbow
    echo "  crossbow (пустой): заглушка (нет $TEXTURES/crossbow_standby.png)"
fi
cat > "$ITEMS/crossbow.json" <<EOF
{
  "model": {
    "type": "minecraft:select",
    "property": "minecraft:charge_type",
    "cases": [
      {
        "when": "arrow",
        "model": { "type": "minecraft:model", "model": "$arrow" }
      }
    ],
    "fallback": { "type": "minecraft:model", "model": "$standby" }
  }
}
EOF

# Динамит - блок (дисплей в мире, «дышит» и горит из кода). Своя модель включается, когда есть
# dynamite_side.png; верх/низ берутся из dynamite_top.png/dynamite_bottom.png, а если их нет - от
# ванильного TNT. Анимация: кадры 16x16 столбиком (PNG 16 x 16*N), скорость - frametime в
# dynamite_side.png.mcmeta / dynamite_top.png.mcmeta (тиков на кадр).
MODELS=assets/hypetrain/models/item/maniac
if [ -f "$TEXTURES/dynamite_side.png" ]; then
    top=minecraft:block/tnt_top
    bottom=minecraft:block/tnt_bottom
    [ -f "$TEXTURES/dynamite_top.png" ] && top=hypetrain:item/maniac/dynamite_top
    [ -f "$TEXTURES/dynamite_bottom.png" ] && bottom=hypetrain:item/maniac/dynamite_bottom
    cat > "$MODELS/dynamite_block.json" <<EOF
{
  "parent": "minecraft:block/cube_bottom_top",
  "textures": {
    "side": "hypetrain:item/maniac/dynamite_side",
    "top": "$top",
    "bottom": "$bottom"
  }
}
EOF
    model=hypetrain:item/maniac/dynamite_block
    echo "  dynamite_block: своя текстура (верх: $top, низ: $bottom)"
else
    rm -f "$MODELS/dynamite_block.json"
    model=minecraft:block/tnt
    echo "  dynamite_block: заглушка minecraft:block/tnt (нет $TEXTURES/dynamite_side.png)"
fi
cat > "$ITEMS/dynamite_block.json" <<EOF
{
  "model": {
    "type": "minecraft:model",
    "model": "$model"
  }
}
EOF

rm -f maniac-pack.zip
# -X без лишних атрибутов macOS; README, скрипт и .gitkeep в пак не идут.
zip -q -X -r maniac-pack.zip pack.mcmeta assets -x '*.DS_Store' -x '*/.gitkeep'
echo
echo "Готово: $(pwd)/maniac-pack.zip"
echo "sha1:   $(shasum -a 1 maniac-pack.zip | cut -d' ' -f1)"
