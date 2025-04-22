# ProyectoBasti
Proyecto para la asignatura de bastionado en redes sobre un IPS
Este proyecto se basa en un sistema de detección y prevención de intrusos como es Snort ya instalado y funcionando.
Lo que hace este código python básicamente es leer el fichero de logs donde se registran los intrusos y enviar por mensaje de telegram a un bot a nuestro gusto las alertas pertinentes, con su función de IPS
podemos además realizar un WHOIS de la IP que nos envia esas extrañas peticiones y además bloquearla con Iptables con solo un botón si fuese necesario.
