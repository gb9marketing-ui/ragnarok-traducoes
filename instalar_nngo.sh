#!/bin/bash
# Instala o servidor Ragnaruto (NNGO convertido para rAthena) numa VPS Ubuntu 24.04 limpa.
# Roda NA VPS como root:  bash instalar_nngo.sh
# Pode ser rodado de novo: atualiza os arquivos e recompila sem apagar o banco de dados.
set -e

RATHENA_COMMIT="d4b8e7b8f16061cc2496d377ac8f777ce72a4f39"
REPO_URL="https://github.com/gb9marketing-ui/ragnarok-traducoes.git"
REPO_BRANCH="nngo"
DIR="/opt/nngo"
SRC="/root/nngo-repo"
CRED="/root/nngo-credenciais.txt"
PACKETVER="20250604"

echo "== 1/7 Pacotes do sistema =="
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git build-essential cmake zlib1g-dev libpcre2-dev libmariadb-dev libmariadb-dev-compat \
  mariadb-server curl openssl rsync >/dev/null

echo "== 2/7 Codigo do rAthena (versao usada na conversao) =="
if [ ! -d "$DIR/.git" ]; then
  mkdir -p "$DIR" && cd "$DIR"
  git init -q
  git remote add origin https://github.com/rathena/rathena.git
fi
cd "$DIR"
git fetch -q --depth 1 origin "$RATHENA_COMMIT"
git checkout -q -f "$RATHENA_COMMIT"

echo "== 3/7 Arquivos do NNGO (jutsus, itens, NPCs, mapas) =="
if [ -d "$SRC/.git" ]; then
  git -C "$SRC" fetch -q --depth 1 origin "$REPO_BRANCH" && git -C "$SRC" reset -q --hard FETCH_HEAD
else
  git clone -q --depth 1 -b "$REPO_BRANCH" "$REPO_URL" "$SRC"
fi
rsync -a "$SRC/servidor/" "$DIR/"

echo "== 4/7 Banco de dados =="
systemctl enable -q --now mariadb
if [ ! -f "$CRED" ]; then
  DBPASS=$(openssl rand -hex 16)
  S1USER="nngo_$(openssl rand -hex 3)"
  S1PASS=$(openssl rand -hex 12)
  printf "DB_USER=nngo\nDB_PASS=%s\nS1_USER=%s\nS1_PASS=%s\n" "$DBPASS" "$S1USER" "$S1PASS" > "$CRED"
  chmod 600 "$CRED"
  mysql -e "CREATE DATABASE IF NOT EXISTS nngo; CREATE USER IF NOT EXISTS 'nngo'@'localhost' IDENTIFIED BY '$DBPASS'; GRANT ALL ON nngo.* TO 'nngo'@'localhost'; FLUSH PRIVILEGES;"
  mysql nngo < "$DIR/sql-files/main.sql"
  mysql nngo < "$DIR/sql-files/logs.sql"
  mysql nngo -e "UPDATE login SET userid='$S1USER', user_pass='$S1PASS' WHERE account_id=1;"
fi
. "$CRED"

echo "== 5/7 Configuracao =="
IP=$(curl -s -4 https://ifconfig.me || hostname -I | awk '{print $1}')
cat > "$DIR/conf/import/inter_conf.txt" <<EOF
login_server_ip: 127.0.0.1
login_server_id: $DB_USER
login_server_pw: $DB_PASS
login_server_db: nngo
ipban_db_ip: 127.0.0.1
ipban_db_id: $DB_USER
ipban_db_pw: $DB_PASS
ipban_db_db: nngo
char_server_ip: 127.0.0.1
char_server_id: $DB_USER
char_server_pw: $DB_PASS
char_server_db: nngo
map_server_ip: 127.0.0.1
map_server_id: $DB_USER
map_server_pw: $DB_PASS
map_server_db: nngo
web_server_ip: 127.0.0.1
web_server_id: $DB_USER
web_server_pw: $DB_PASS
web_server_db: nngo
log_db_ip: 127.0.0.1
log_db_id: $DB_USER
log_db_pw: $DB_PASS
log_db_db: nngo
EOF
grep -v "^userid:\|^passwd:\|^char_ip:\|^login_ip:" "$DIR/conf/import/char_conf.txt" > /tmp/char_conf.txt || true
cat /tmp/char_conf.txt > "$DIR/conf/import/char_conf.txt"
printf "userid: %s\npasswd: %s\nchar_ip: %s\nlogin_ip: 127.0.0.1\n" "$S1_USER" "$S1_PASS" "$IP" >> "$DIR/conf/import/char_conf.txt"
printf "userid: %s\npasswd: %s\nmap_ip: %s\nchar_ip: 127.0.0.1\n" "$S1_USER" "$S1_PASS" "$IP" > "$DIR/conf/import/map_conf.txt"
printf "new_account: yes\n" > "$DIR/conf/import/login_conf.txt"
chmod 600 "$DIR"/conf/import/*.txt

echo "== 6/7 Compilando (pode levar uns 20-30 minutos) =="
cd "$DIR"
./configure -q --enable-prere=yes --enable-packetver=$PACKETVER --enable-epoll=yes >/dev/null
make -s server -j"$(nproc)" >/root/nngo-build.log 2>&1 || { tail -30 /root/nngo-build.log; echo "ERRO NA COMPILACAO"; exit 1; }

echo "== 7/7 Servicos e portas =="
cat > /etc/systemd/system/nngo@.service <<EOF
[Unit]
Description=Ragnaruto (NNGO) %i-server
After=network.target mariadb.service

[Service]
WorkingDirectory=$DIR
ExecStart=$DIR/%i-server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
for s in login char map; do systemctl enable -q nngo@$s; systemctl restart nngo@$s; sleep 3; done
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow 6900/tcp; ufw allow 6121/tcp; ufw allow 5121/tcp
fi

sleep 20
echo
for s in login char map; do echo "nngo@$s: $(systemctl is-active nngo@$s)"; done
echo "IP do servidor: $IP"
journalctl -u nngo@map -n 200 --no-pager | grep -E "Successfully loaded|Done loading '[0-9]+' NPCs|online" | tail -3
echo "== PRONTO =="
