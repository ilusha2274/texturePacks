#!/bin/bash
# Собирает ТЕСТОВЫЙ пак: текущий общий пак сети (network/hypetrain-pack.zip, как он есть) + оружие
# из этой папки. Общий пак и его sha1 на серверах не меняются — тестовый zip раздаётся с мака
# локально (serve-test.sh) и подключается только локальному лобби через lobby/server.local.properties.
#
# Когда оружие будет готово к проду: перенести assets/ отсюда в сборку network/build.sh и обновить
# общий пак по его README (sha1 во всех шести server.properties).
cd "$(dirname "$0")"
set -e

NETWORK_ZIP=../network/hypetrain-pack.zip
OUT_DIR=test-build
OUT=$OUT_DIR/hypetrain-test-pack.zip
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

python3 -I bbmodel_to_java.py
unzip -q "$NETWORK_ZIP" -d "$STAGE"
cp -R assets "$STAGE/"

mkdir -p "$OUT_DIR"
rm -f "$OUT"
(cd "$STAGE" && zip -q -X -r "$OLDPWD/$OUT" pack.mcmeta assets -x '*.DS_Store' -x '*/.gitkeep')

SHA1=$(shasum -a 1 "$OUT" | cut -d' ' -f1)
echo "Готово: $(pwd)/$OUT"
echo "sha1:   $SHA1"
