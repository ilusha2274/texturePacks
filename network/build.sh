#!/bin/bash
# Собирает общий пак сети hypetrain-pack.zip из паков режимов и печатает sha1 для server.properties
# ВСЕХ Paper-серверов (lobby, speedrun, spy, hideandseek, traitor, maniac).
#
# Зачем один пак: красный экран Mojang - это перезагрузка ресурсов клиента, она бывает при каждой
# смене набора паков. Пока у каждого режима был свой пак, экран вылезал на каждом переходе. С одним
# паком Velocity видит, что пак с этим sha1 у игрока уже стоит, и не пересылает его клиенту -
# перезагрузка только один раз, при входе в сеть.
#
# Исходники по-прежнему в папках режимов (lobby/, maniac/, hideandseek/) - править текстуры там,
# потом запускать этот скрипт. Своё у network/ - только шрифт затемнения переходов (hypetrain:fade,
# его показывает GameOrchestratorPlugin) и pack.mcmeta.
cd "$(dirname "$0")"
set -e

ROOT=..
OUT=hypetrain-pack.zip
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

# Маньяк генерирует JSON предметов под наличие текстур - прогоняем его сборку, чтобы они были свежие.
echo "Маньяк:"
"$ROOT/maniac/build.sh" --items-only > /dev/null
echo "  предметы обновлены"

cp pack.mcmeta "$STAGE/"
cp -R assets "$STAGE/"
cp -R "$ROOT/lobby/assets" "$STAGE/"
cp -R "$ROOT/maniac/assets" "$STAGE/"
# Оружие дуэлей лобби (кремнёвый пистолет, hypetrain:flintlock_red|blue). Исходник модели —
# weapons/flintlock.bbmodel, assets из него генерирует weapons/bbmodel_to_java.py.
cp -R "$ROOT/weapons/assets" "$STAGE/"
# Предметы «Предателя»: нож (traitorgame:traitor_knife) и шприц (traitorgame:poison_syringe, в
# инвентаре плоская иконка). Исходники - traitor/knife.bbmodel и traitor/syringe.bbmodel, assets из
# них генерирует traitor/build_models.py (запускаем, чтобы были свежие).
python3 -I "$ROOT/traitor/build_models.py" > /dev/null
cp -R "$ROOT/traitor/assets" "$STAGE/"

# Шкала голода: маньяк прятал её всю, а в общем паке это задело бы все режимы (в Спидране голод
# важен). Оставляем прозрачными только спрайты *_hunger - плагин маньяка вешает игрокам скрытый
# эффект Голода, и клиент рисует шкалу именно ими.
HUD="$STAGE/assets/minecraft/textures/gui/sprites/hud"
rm -f "$HUD/food_empty.png" "$HUD/food_half.png" "$HUD/food_full.png"

# Прятки: прозрачный вихрь riptide у замаскированного хайдера. Путь текстуры менялся между
# версиями - кладём в оба места, как и было в паке пряток.
mkdir -p "$STAGE/assets/minecraft/textures/entity/trident"
cp "$ROOT/hideandseek/trident_riptide.png" "$STAGE/assets/minecraft/textures/entity/trident/trident_riptide.png"
cp "$ROOT/hideandseek/trident_riptide.png" "$STAGE/assets/minecraft/textures/entity/trident_riptide.png"

rm -f "$OUT"
# Детерминированный zip: одинаковое время у всех файлов, файлы в отсортированном порядке, без
# записей каталогов (-D) и атрибутов macOS (-X). Тогда пересборка без правок даёт тот же zip и тот
# же sha1 - не нужно трогать server.properties и коммитить «изменившийся» бинарник.
# .gitkeep и .DS_Store в пак не идут.
find "$STAGE" -exec touch -h -t 202001010000 {} +
(cd "$STAGE" && find pack.mcmeta assets -type f ! -name '.DS_Store' ! -name '.gitkeep' | LC_ALL=C sort \
    | zip -q -X -D "$OLDPWD/$OUT" -@)

echo
echo "Готово: $(pwd)/$OUT"
SHA1=$(shasum -a 1 "$OUT" | cut -d' ' -f1)
echo "sha1:   $SHA1"
echo
echo "В server.properties всех шести серверов (после git push):"
echo "resource-pack=https\\://raw.githubusercontent.com/ilusha2274/texturePacks/main/network/$OUT?v\\=${SHA1:0:7}"
echo "resource-pack-sha1=$SHA1"
