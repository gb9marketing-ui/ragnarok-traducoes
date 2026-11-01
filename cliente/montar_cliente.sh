#!/bin/bash
# Baixa o cliente base e o patch do NNGO, monta o zip do Ragnaruto e publica em http://<ip>/
set -e
W=/root/cliente-build; mkdir -p "$W"; cd "$W"
SRC=/root/nngo-repo
git -C "$SRC" fetch -q --depth 1 origin nngo && git -C "$SRC" reset -q --hard FETCH_HEAD
export DEBIAN_FRONTEND=noninteractive
command -v nginx >/dev/null || { apt-get update -qq; apt-get install -y -qq nginx >/dev/null; }
baixar() { # <id do Google Drive> <arquivo> <tamanho minimo em bytes>
  if [ "$(stat -c%s "$2" 2>/dev/null || echo 0)" -lt "$3" ]; then
    curl -sL -c ck.txt -o "$2" "https://drive.usercontent.google.com/download?id=$1&export=download&confirm=t"
    if [ "$(stat -c%s "$2")" -lt "$3" ]; then  # pagina de aviso do Google: pega o uuid e tenta de novo
      U=$(grep -o 'name="uuid" value="[^"]*"' "$2" | cut -d'"' -f4)
      curl -sL -b ck.txt -o "$2" "https://drive.usercontent.google.com/download?id=$1&export=download&confirm=t&uuid=$U"
    fi
  fi
  echo "$2: $(stat -c%s "$2") bytes"
}
baixar 1dfmsuERbqi5v42OfUO1yxzGS7xvxIYAw cliente_base.zip 4000000000
baixar 1a2FtohcraUVjsP0fTId_Zx_CIViJkuW9 patch_nngo.zip 1500000000
IP=$(curl -s -4 https://ifconfig.me)
python3 -I "$SRC/cliente/montar_cliente.py" cliente_base.zip patch_nngo.zip /opt/nngo/db/nngo/item_db.yml "$IP" /var/www/html/Ragnaruto.zip
cp "$SRC/cliente/index.html" /var/www/html/index.html
sed -i "s/__IP__/$IP/g" /var/www/html/index.html
systemctl enable -q --now nginx
echo "Download: http://$IP/Ragnaruto.zip"
