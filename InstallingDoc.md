# CONSIDERACIONES PREVIAS
Necesario tener instalado Snort o Suricata, ambos son validos yo lo hago con Snort.
También es necesario crear un Bot en nuestro Telegram que será el encargado de transmitirnos las alertas
Yo lo cree usando BotFather con /newbot, es fácil solo seguir los pasos, después hay que añadir los comandos
del bot tal cual asi:

alertas - Mostrar las últimas IPs que han generado alertas
bloquear - Bloquear una IP específica (uso: /bloquear 192.168.1.1)
whois - Mostrar información WHOIS de la IP pública del servidor
help - Mostrar ayuda sobre los comandos disponibles
status - Mostrar estado del sistema de monitoreo

Asi evitamos errores con los handlers a la hora de escribirle.

Editar el script y cambiar los valores de TOKEN del bot, CHAT_ID del chat con el bot y LOG del IPS por los datos que tenga cada uno

[Opcionalmente se puede usar systemd para que el script se ejecute al iniciar el sistema
(
- sudo nano /etc/systemd/system/miscript.service

...
[Unit]
Description=Script Python como root
After=network.target

[Service]
ExecStart=/usr/bin/python3 /ruta/completa/al/script.py
Restart=on-failure
WorkingDirectory=/ruta/completa/al/
StandardOutput=journal
StandardError=journal

#Al no especificar User=, se ejecuta como root

[Install]
WantedBy=multi-user.target
...

- sudo chmod +x /ruta/completa/al/script.py

- sudo systemctl enable miscript.service
)]

# USO DEL SCRIPT

Una vez tengamos todo listo, iniciamos el script ./script.py con sudo 
para que al bloquear una ip con IPtables no tengamos problemas ya que este usa permisos de root.

# PRUEBA DE FUNCIONAMIENTO

Si está todo bien configurado y el script se inicia correctamente, podemos probar desde otra ip externa al propio sistema mandando un ping
y debería llegar una alerta tanto a telegram como en la terminal que estemos ejecutando el script.
