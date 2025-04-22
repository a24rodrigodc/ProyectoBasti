# ProyectoBasti
Proyecto para la asignatura de bastionado en redes sobre un IPS
Este proyecto se basa en un sistema de detección y prevención de intrusos como es Snort.
Lo que hace este código python básicamente es leer el fichero de logs donde se registran los intrusos y enviar a nuestros dispositivos, a través de un bot de telegram, las alertas pertinentes
Con su función de IPS podemos realizar, primeramente, un WHOIS de la IP que nos envia esas extrañas peticiones si quisieramos y además bloquearla usando Iptables con solo un comando.
