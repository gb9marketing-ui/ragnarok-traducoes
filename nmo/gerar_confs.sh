#!/bin/bash
# Gera conf/import do Cronus (Naruto Maniacs). Uso: gerar_confs.sh <dir_emulador> <db_user> <db_pass> <db_nome> <s1_user> <s1_pass> <ip_publico>
D=$1; DBU=$2; DBP=$3; DBN=$4; SU=$5; SP=$6; IP=$7
I="$D/conf/import"
{
for p in sql ipban.sql account.sql; do
  printf '%s.db_hostname: 127.0.0.1\n%s.db_port: 3306\n%s.db_username: %s\n%s.db_password: %s\n%s.db_database: %s\n' $p $p $p "$DBU" $p "$DBP" $p "$DBN"
done
printf 'ipban.sql.codepage:\nipban.sql.ipban_table: ipbanlist\naccount.sql.codepage:\naccount.sql.case_sensitive: no\naccount.sql.account_db: login\naccount.sql.accreg_db: global_reg_value\n'
for p in char_server map_server; do
  printf '%s_ip: 127.0.0.1\n%s_port: 3306\n%s_id: %s\n%s_pw: %s\n%s_db: %s\n' $p $p $p "$DBU" $p "$DBP" $p "$DBN"
done
printf 'log_db_ip: 127.0.0.1\nlog_db_port: 3306\nlog_db_id: %s\nlog_db_pw: %s\nlog_db_db: %s\nlog_login_db: %s\n' "$DBU" "$DBP" "$DBN" "$DBN"
printf 'db_ip: 127.0.0.1\ndb_port: 3306\ndb_id: %s\ndb_pw: %s\ndb_name: %s\n' "$DBU" "$DBP" "$DBN"
printf 'brAdb_ip: 127.0.0.1\nbrAdb_port: 3306\nbrAdb_id: %s\nbrAdb_pw: %s\nbrAdb_name: %s\n' "$DBU" "$DBP" "$DBN"
} > "$I/inter_conf.txt"
printf 'userid: %s\npasswd: %s\nserver_name: Naruto Maniacs\nlogin_ip: 127.0.0.1\nlogin_port: 8524\nchar_ip: %s\nchar_port: 2771\nmax_connect_user: 250\ngm_allow_group: -1\n' "$SU" "$SP" "$IP" > "$I/char_conf.txt"
printf 'login_port: 8524\nnew_account: yes\n' > "$I/login_conf.txt"
printf 'userid: %s\npasswd: %s\nchar_ip: 127.0.0.1\nchar_port: 2771\nmap_ip: %s\nmap_port: 4816\n' "$SU" "$SP" "$IP" > "$I/map_conf.txt"
printf '' > "$I/packet_conf.txt"
chmod 600 "$I"/*.txt
