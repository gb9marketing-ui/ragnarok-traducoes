#!/bin/bash
# Naruto Maniacs Online (emulador Cronus original, dez/2020) numa VPS Ubuntu 24.04.
# 1) Arquiva o Ragnaruto (backup do banco + configs, desliga os servicos, tira o download do ar)
# 2) Baixa o kit do NMO do Google Drive, compila o Cronus, cria o banco vazio e liga tudo.
# Roda NA VPS como root:  nohup bash instalar_nmo.sh > /root/nmo-install.log 2>&1 &
# Progresso (sem senhas): http://IP/status/nmo.txt
# Pode rodar de novo: nao recria o banco nem as senhas (ficam em /root/nmo-credenciais.txt).
set -e

KIT_ID="1gfi69kPrO2F6s4P4aN6xVxN5I-7Ot9RY"      # GAME - NARUTO MANICS.zip (Drive)
KIT_SIZE=730797366
REPO_URL="https://github.com/gb9marketing-ui/ragnarok-traducoes.git"
REPO_BRANCH="nmo"
DIR="/opt/nmo"
KIT="/root/nmo-kit"
SRC="/root/nmo-repo"
CRED="/root/nmo-credenciais.txt"
WWW="/var/www/html"
STATUS="$WWW/status/nmo.txt"

mkdir -p "$WWW/status"
st() { echo "$(date +%H:%M:%S) $*" | tee -a "$STATUS"; }
trap 'st "ERRO na linha $LINENO (veja /root/nmo-install.log)"' ERR
: > "$STATUS"
st "== Inicio da instalacao do Naruto Maniacs =="

# ---------------------------------------------------------------- 1. Arquivar Ragnaruto
if [ -d /opt/nngo ] && ! ls -d /root/backups/ragnaruto-* >/dev/null 2>&1; then
  st "1/7 Arquivando o Ragnaruto (backup + desligar)"
  B="/root/backups/ragnaruto-$(date +%Y%m%d-%H%M)"
  mkdir -p "$B/www"
  mysqldump --single-transaction --routines nngo | gzip > "$B/nngo-banco.sql.gz"
  tar czf "$B/nngo-config.tgz" -C /opt/nngo conf/import db/import 2>/dev/null || true
  cp -a /root/nngo-credenciais.txt "$B/" 2>/dev/null || true
  for s in map char login; do systemctl disable -q --now "nngo@$s" 2>/dev/null || true; done
  for f in Ragnaruto.zip index.html; do [ -e "$WWW/$f" ] && mv "$WWW/$f" "$B/www/"; done
  chmod -R go-rwx /root/backups
  st "   backup salvo em $B ($(du -sh "$B" | cut -f1)); servicos nngo desligados"
else
  st "1/7 Ragnaruto ja arquivado (ou inexistente) - pulando"
fi
cat > "$WWW/index.html" <<'EOF'
<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Naruto Maniacs Online</title>
<body style="margin:0;min-height:100vh;display:grid;place-items:center;background:#120c08;color:#f4e9dc;font-family:system-ui,sans-serif;text-align:center">
<div><h1 style="color:#ff8a1f;margin:0 0 8px">Naruto Maniacs Online</h1><p>O servidor esta voltando. Download do jogo em breve.</p></div></body></html>
EOF

# ---------------------------------------------------------------- 2. Pacotes
st "2/7 Instalando pacotes do sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git build-essential zlib1g-dev libmariadb-dev libmariadb-dev-compat \
  mariadb-server mariadb-client curl openssl unzip p7zip-full >/dev/null
MC=$(command -v mariadb_config || command -v mysql_config)

# ---------------------------------------------------------------- 3. Kit do Drive
st "3/7 Baixando o kit do Naruto Maniacs (730 MB)"
mkdir -p "$KIT"
if [ "$(stat -c %s "$KIT/kit.zip" 2>/dev/null)" != "$KIT_SIZE" ]; then
  U="https://drive.usercontent.google.com/download?id=$KIT_ID&export=download&confirm=t"
  curl -sSL -c "$KIT/ck" -b "$KIT/ck" -o "$KIT/kit.zip" "$U"
  if head -c 200 "$KIT/kit.zip" | grep -qi "<html\|<!doctype"; then
    UUID=$(grep -o 'name="uuid" value="[^"]*"' "$KIT/kit.zip" | cut -d'"' -f4)
    curl -sSL -b "$KIT/ck" -o "$KIT/kit.zip" "$U&uuid=$UUID"
  fi
fi
SZ=$(stat -c %s "$KIT/kit.zip")
[ "$SZ" = "$KIT_SIZE" ] || { st "ERRO: download veio com $SZ bytes (esperado $KIT_SIZE). O arquivo no Drive precisa estar como 'qualquer pessoa com o link'."; exit 1; }
rm -rf "$KIT/x" && mkdir -p "$KIT/x" && { unzip -q -o "$KIT/kit.zip" -d "$KIT/x" || [ $? -eq 1 ]; }
EZ=$(find "$KIT/x" -iname 'emulador.zip' | head -1)
SQL=$(find "$KIT/x" -iname '*ragnarok*.sql' | head -1)
[ -n "$EZ" ] && [ -n "$SQL" ] || { st "ERRO: emulador.zip ou .sql nao encontrados no kit"; exit 1; }
st "   kit ok"

# ---------------------------------------------------------------- 4. Codigo de instalacao (este repo)
if [ -d "$SRC/.git" ]; then
  git -C "$SRC" fetch -q --depth 1 origin "$REPO_BRANCH" && git -C "$SRC" reset -q --hard FETCH_HEAD
else
  git clone -q --depth 1 -b "$REPO_BRANCH" "$REPO_URL" "$SRC"
fi

# ---------------------------------------------------------------- 5. Compilar o Cronus
if [ ! -x "$DIR/map-server_sql" ] || [ "${RECOMPILAR:-0}" = 1 ]; then
  st "4/7 Compilando o emulador Cronus (uns 5-10 minutos)"
  for s in map char login; do systemctl stop "nmo@$s" 2>/dev/null || true; done
  rm -rf "$KIT/emu" && mkdir -p "$KIT/emu" && { unzip -q -o "$EZ" -d "$KIT/emu" || [ $? -eq 1 ]; }
  E=$(dirname "$(find "$KIT/emu" -maxdepth 3 -name configure | head -1)")
  rm -rf "$DIR" && mv "$E" "$DIR"
  cd "$DIR"
  find . -name '*.o' -delete
  rm -f core.* login-server_sql char-server_sql map-server_sql
  chmod +x configure
  ./configure --enable-64bit --with-mysql="$MC" CFLAGS="-O2 -fcommon -g" > /root/nmo-configure.log 2>&1
  make sql > /root/nmo-build.log 2>&1 || { tail -30 /root/nmo-build.log; st "ERRO NA COMPILACAO"; exit 1; }
  [ -x map-server_sql ] && [ -x char-server_sql ] && [ -x login-server_sql ] || { st "ERRO: binarios nao gerados"; exit 1; }
  st "   compilado"
else
  st "4/7 Emulador ja compilado - pulando (RECOMPILAR=1 para forcar)"
fi

# ---------------------------------------------------------------- 6. Banco de dados (vazio, sem jogadores)
st "5/7 Banco de dados"
cat > /etc/mysql/mariadb.conf.d/90-nmo.cnf <<'EOF'
[mysqld]
sql_mode = NO_ENGINE_SUBSTITUTION
EOF
systemctl enable -q mariadb; systemctl restart mariadb
if [ ! -f "$CRED" ]; then
  DBPASS=$(openssl rand -hex 16)
  S1USER="nmo_$(openssl rand -hex 3)"
  S1PASS=$(openssl rand -hex 8)
  printf "DB_USER=nmo\nDB_PASS=%s\nS1_USER=%s\nS1_PASS=%s\n" "$DBPASS" "$S1USER" "$S1PASS" > "$CRED"
  chmod 600 "$CRED"
  mysql -e "CREATE DATABASE IF NOT EXISTS nmo CHARACTER SET latin1; CREATE USER IF NOT EXISTS 'nmo'@'localhost' IDENTIFIED BY '$DBPASS'; GRANT ALL ON nmo.* TO 'nmo'@'localhost'; FLUSH PRIVILEGES;"
  mysql nmo < "$SQL"
  # tira as contas/personagens antigos do kit; conta 1 = conta interna do servidor, com senha nova
  mysql nmo -e "DELETE FROM login WHERE account_id<>1; DELETE FROM \`char\`; DELETE FROM inventory; DELETE FROM skill; DELETE FROM charlog; DELETE FROM global_reg_value;
    UPDATE login SET userid='$S1USER', user_pass='$S1PASS', sex='S', level=0, logincount=0, last_ip='' WHERE account_id=1;"
  st "   banco 'nmo' criado do zero"
else
  st "   banco ja existe - mantido"
fi
. "$CRED"

# ---------------------------------------------------------------- 7. Configuracao + servicos
st "6/7 Configurando IP, portas e servicos"
IP=$(curl -s -4 https://ifconfig.me || hostname -I | awk '{print $1}')
bash "$SRC/nmo/gerar_confs.sh" "$DIR" "$DB_USER" "$DB_PASS" nmo "$S1_USER" "$S1_PASS" "$IP"
cat > /etc/systemd/system/nmo@.service <<EOF
[Unit]
Description=Naruto Maniacs %i-server
After=network.target mariadb.service

[Service]
WorkingDirectory=$DIR
ExecStart=$DIR/%i-server_sql
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
for s in login char map; do systemctl enable -q "nmo@$s"; systemctl restart "nmo@$s"; sleep 3; done
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow 8524/tcp; ufw allow 2771/tcp; ufw allow 4816/tcp
fi

st "7/7 Conferindo"
sleep 40
for s in login char map; do st "   nmo@$s: $(systemctl is-active nmo@$s)"; done
journalctl -u nmo@map -u nmo@char --no-pager -n 400 | grep -iE "NPC|maps|conect|connect|erro|error" | grep -viE "pass|senha|_pw" | tail -8 | sed 's/^/   /' >> "$STATUS"
st "   IP do servidor: $IP  (login 8524, char 2771, map 4816)"

# inventario para montar o cliente (so nomes e tamanhos de arquivos)
{ echo; echo "== conteudo do kit =="; unzip -l "$KIT/kit.zip" | awk 'NR>3 && $4!="" {print $1, substr($0, index($0,$4))}' | head -80
  find "$KIT/x" -iname '*.exe' -size +20M -print0 | while IFS= read -r -d '' x; do echo "== dentro de $(basename "$x") =="; 7z l "$x" 2>/dev/null | grep -E "^[0-9]{4}-" | cut -c27-220 | head -80; done
  echo "== /root/cliente-build =="; ls -la /root/cliente-build 2>/dev/null | head -20
  for z in /root/cliente-build/*.zip; do [ -f "$z" ] && { echo "-- $(basename "$z")"; unzip -l "$z" | grep -iE "\.(dll|asi|m3d|flt|grf|exe|ini)$" | head -40; }; done
  echo "== disco =="; df -h / | tail -1; } >> "$STATUS" 2>&1
st "== PRONTO =="
