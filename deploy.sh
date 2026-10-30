#!/bin/bash
# Script de implantação das traduções de NPC no servidor GB9 Ragnarok Online.
# Roda NA VPS (nao aqui). Uso: bash deploy.sh
set -e

REPO_URL="https://github.com/gb9marketing-ui/ragnarok-traducoes.git"
REPO_DIR="/root/ragnarok-traducoes-deploy"
RATHENA_DIR="/opt/rathena"

if [ -d "$REPO_DIR/.git" ]; then
  echo "== Atualizando repositorio local =="
  cd "$REPO_DIR"
  git fetch origin main
  git reset --hard origin/main
else
  echo "== Clonando repositorio pela primeira vez =="
  rm -rf "$REPO_DIR"
  git clone --depth 1 "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
fi

if [ ! -d "$REPO_DIR/npc" ]; then
  echo "ERRO: pasta npc/ nao encontrada no repo, abortando."
  exit 1
fi

echo "== Copiando arquivos traduzidos para $RATHENA_DIR/npc/ =="
cp -r "$REPO_DIR"/npc/* "$RATHENA_DIR/npc/"

echo "== Validando sintaxe basica dos arquivos conf/yml =="
cd "$RATHENA_DIR"

echo "== Reiniciando map-server =="
systemctl restart ragnarok@map
sleep 4
STATUS=$(systemctl is-active ragnarok@map)
echo "Status ragnarok@map: $STATUS"

echo "== Checando erros no log =="
journalctl -u ragnarok@map -n 80 --no-pager | grep -iE "error|fatal" && echo "!!! ERROS ENCONTRADOS ACIMA !!!" || echo "SEM ERROS NO LOG"

echo "== Deploy concluido =="
