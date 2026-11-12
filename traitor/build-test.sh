#!/bin/bash
# Собирает ТЕСТОВЫЙ пак: текущий общий пак сети (network/hypetrain-pack.zip, как он есть) + предметы
# «Предателя» из этой папки (нож, шприц). Общий пак и его sha1 на серверах не меняются - тестовый zip
# раздаётся с мака локально (serve-test.sh) и подключается только локальным lobby и traitor через их
# server.local.properties (в git не попадают).
#
# Когда всё готово к проду: добавить `cp -R "$ROOT/traitor/assets" "$STAGE/"` в network/build.sh и
# обновить общий пак по его README (sha1 во всех шести server.properties).
cd "$(dirname "$0")"
set -e

NETWORK_ZIP=../network/hypetrain-pack.zip
OUT_DIR=test-build
OUT=$OUT_DIR/hypetrain-test-pack.zip
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

python3 -I build_models.py
unzip -q "$NETWORK_ZIP" -d "$STAGE"
cp -R assets "$STAGE/"

mkdir -p "$OUT_DIR"
rm -f "$OUT"
find "$STAGE" -exec touch -h -t 202001010000 {} +
(cd "$STAGE" && find pack.mcmeta assets -type f ! -name '.DS_Store' ! -name '.gitkeep' | LC_ALL=C sort \
    | zip -q -X -D "$OLDPWD/$OUT" -@)

SHA1=$(shasum -a 1 "$OUT" | cut -d' ' -f1)
echo "Готово: $(pwd)/$OUT"
echo "sha1:   $SHA1"
