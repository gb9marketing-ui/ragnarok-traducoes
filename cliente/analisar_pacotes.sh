#!/bin/bash
# Baixa pacotes .rar/.zip com GRFs, extrai so as .grf e gera a lista de cada GRF (listar_grf.py) em <saida>.
# Uso: bash analisar_pacotes.sh <saida> "nome|url" ["nome|url" ...]
OUT=$1; shift; W=/root/analise; mkdir -p "$W" "$OUT"; cd "$W"
REPO=/root/nngo-repo
log() { echo "$(date +%T) $*" >> "$OUT/status.txt"; }
export DEBIAN_FRONTEND=noninteractive
command -v unrar >/dev/null || apt-get install -y -qq unrar >/dev/null 2>&1 || true
command -v 7zz >/dev/null || command -v 7z >/dev/null || apt-get install -y -qq 7zip >/dev/null 2>&1 || true
for item in "$@"; do
  n=${item%%|*}; u=${item#*|}
  log "baixando $n"
  curl -sL -c ck.txt -o "$n" "$u"
  if [ "$(stat -c%s "$n")" -lt 1000000 ] && grep -q 'name="uuid"' "$n"; then
    U=$(grep -o 'name="uuid" value="[^"]*"' "$n" | cut -d'"' -f4)
    curl -sL -b ck.txt -o "$n" "$u&uuid=$U"
  fi
  log "$n: $(stat -c%s "$n") bytes"
  (unrar lb "$n" 2>/dev/null || 7zz l -ba "$n" 2>/dev/null || 7z l -ba "$n") > "$OUT/${n}__conteudo.txt" 2>&1
  mkdir -p "x_$n"
  unrar x -o+ -inul "$n" "x_$n/" >/dev/null 2>&1 || 7zz x -y "-ox_$n" "$n" >/dev/null 2>&1 || 7z x -y "-ox_$n" "$n" >/dev/null 2>&1
  log "extraido $n: $(find "x_$n" -type f | wc -l) arquivos"
  find "x_$n" -iname '*.grf' -print0 | while IFS= read -r -d '' g; do
    b=$(basename "$g"); log "listando $b ($(stat -c%s "$g") bytes)"
    python3 -I "$REPO/cliente/listar_grf.py" "$g" "$OUT/${n}__${b}.txt.gz" >> "$OUT/status.txt" 2>&1
    head -c 46 "$g" | od -A d -t x1 | head -3 >> "$OUT/status.txt"
  done
  find "x_$n" -type f -iname '*.info' -o -type f -iname 'cps.dll' -o -type f -iname '*.ini' | head -20 >> "$OUT/status.txt"
done
log "FIM"
