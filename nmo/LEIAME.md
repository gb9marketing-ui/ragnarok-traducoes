# Naruto Maniacs Online (emulador Cronus original)

Scripts para colocar o NMO no ar numa VPS Ubuntu 24.04, usando o emulador e o patch originais (dez/2020).
Nao contem senhas nem arquivos do jogo: o kit e baixado do Google Drive do dono.

- `instalar_nmo.sh` arquiva o servidor anterior (Ragnaruto), compila o Cronus, cria o banco vazio e liga os servicos `nmo@login`, `nmo@char`, `nmo@map`.
- `gerar_confs.sh` escreve os `conf/import/*.txt` do Cronus (banco, conta do servidor, IP).

Portas: login 8524, char 2771, map 4816. Senhas geradas ficam so na VPS, em `/root/nmo-credenciais.txt`.

Na VPS, como root:

    curl -sLo /root/instalar_nmo.sh https://raw.githubusercontent.com/gb9marketing-ui/ragnarok-traducoes/nmo/nmo/instalar_nmo.sh
    nohup bash /root/instalar_nmo.sh > /root/nmo-install.log 2>&1 &

Progresso: `http://IP/status/nmo.txt`.
