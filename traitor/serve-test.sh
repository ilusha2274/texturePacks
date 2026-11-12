#!/bin/bash
# Раздаёт тестовый пак с мака по локальной сети (порт 8765), чтобы клиенты в этой же сети его
# скачали. Держать запущенным, пока идёт тест: screen -dmS packtest ./serve-test.sh
cd "$(dirname "$0")/test-build"
exec python3 -I -m http.server 8765 --bind 0.0.0.0
