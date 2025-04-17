#!/usr/bin/env python3
import re
import asyncio
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.error import TelegramError

TOKEN = "8055320051:AAE8nJ8rkgqXfFl0qfD_qwTf6iwmVAPZ15E"
CHAT_ID = "2051675396"
LOG_FILE = "/var/log/snort/snort.alert.fast"

class IPSMonitor:
    def __init__(self):
        self.last_position = 0
        self.app = None
        self.public_ip_cache = None
        self.public_ip_time = 0
        self.alerted_ips = {}
        self.start_time = time.time()
        print("IPSMonitor inicializado")

    async def get_public_ip(self):
        """Obtiene y cachea la IP pública con timeout de 5 minutos"""
        current_time = time.time()
        if self.public_ip_cache and (current_time - self.public_ip_time) < 300:
            return self.public_ip_cache
            
        try:
            proc = await asyncio.create_subprocess_exec(
                'curl', '-s', 'https://api.ipify.org',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                self.public_ip_cache = stdout.decode().strip()
                self.public_ip_time = current_time
                return self.public_ip_cache
            return "No disponible"
        except Exception as e:
            print(f"Error obteniendo IP pública: {str(e)}")
            return "Error al obtener"

    async def get_whois(self, ip):
        """Obtiene información WHOIS"""
        try:
            # Ejecutar el comando whois para obtener la información cruda
            proc = await asyncio.create_subprocess_exec(
                'whois', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
    
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return f"❌ Error al obtener información WHOIS: {stderr.decode()}"

            # Devolver la salida cruda
            return stdout.decode()

        except Exception as e:
            return f"❌ Error al consultar WHOIS: {str(e)}"

    async def block_ip(self, ip):
        """Bloqueado de IP"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return f"✅ IP {ip} bloqueada exitosamente"
            return f"❌ Error al bloquear (código {proc.returncode}): {stderr.decode()}"
        except Exception as e:
            return f"❌ Error bloqueando IP: {str(e)}"

    async def send_alert(self, ip, attack_type):
        """Envía alerta personalizada"""
        try:
            message = (
                f"🚨 **Alerta Snort**\n"
                f"• **Que está pasando?** {attack_type}\n"
                f"• **IP Origen:** `{ip}`\n"
                f"• **Hora:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Comandos disponibles:\n"
                f"/bloquear\n"
                f"/whois\n"
                f"/alertas"
            )

            await self.app.bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error enviando alerta: {str(e)}")

    async def handle_bloquear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /bloquear"""
        print(f"Comando bloquear recibido: {update.message.text}")
        try:
            if not context.args:
                await update.message.reply_text("ℹ️ Uso correcto: /bloquear <IP>")
                return

            ip = context.args[0]
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                await update.message.reply_text("❌ Formato de IP inválido")
                return

            await update.message.reply_text(f"⏳ Bloqueando {ip}...")
            result = await self.block_ip(ip)
            await update.message.reply_text(result)
            print(f"Bloqueo completado: {result}")

        except Exception as e:
            error_msg = f"⚠️ Error al bloquear: {str(e)}"
            await update.message.reply_text(error_msg)
            print(error_msg)

    async def handle_whois(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /whois <IP>"""
        print(f"Comando whois recibido: {update.message.text}")
        try:
            if not context.args:
                await update.message.reply_text("ℹ️ Uso correcto: /whois <IP>")
                return

            ip = context.args[0]
    
            if not re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip):
                await update.message.reply_text("❌ Formato de IP inválido")
                return

            await update.message.reply_text(f"🔍 Buscando WHOIS para {ip}...")
        
            # Llamar a la función get_whois
            whois_info = await self.get_whois(ip)

            # Mostrar la salida directamente
            await update.message.reply_text(
                f"🌍 IP: {ip}\n\n🔍 WHOIS:\n{whois_info}",
                parse_mode="Markdown"
            )

        except Exception as e:
            error_msg = f"❌ Error en WHOIS: {str(e)}"
            await update.message.reply_text(error_msg)
            print(error_msg)

    async def handle_alertas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /alertas"""
        if not self.alerted_ips:
            await update.message.reply_text("No hay IPs alertadas recientemente")
            return

        message = "📝 IPs alertadas recientemente:\n\n"
        for ip, timestamp in sorted(self.alerted_ips.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)[:10]:  # Mostrar solo las 10 más recientes
            message += f"• `{ip}` - {time.ctime(timestamp)}\n"

        message += "\nPara bloquear: /bloquear <IP>"
        await update.message.reply_text(message, parse_mode="Markdown")

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /help"""
        help_text = (
            "🛡️ *Comandos disponibles:*\n\n"
            "/alertas - Mostrar IPs recientes\n"
            "/bloquear <IP> - Bloquear una IP específica\n"
            "/whois - Información de la IP pública\n"
            "/status - Estado del sistema\n"
            "/help - Muestra esta ayuda"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /status"""
        uptime = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)

        status_text = (
            f"📊 *Estado del sistema*\n\n"
            f"• Tiempo activo: {hours}h {minutes}m {seconds}s\n"
            f"• IP pública del servidor: {await self.get_public_ip()}\n"
            f"• Ips registradas: {len(self.alerted_ips)}, /alertas para ver\n"
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def monitor_logs(self):
        """Monitorea solo cambios nuevos en las últimas líneas del log"""
        print(f"Monitorizando {LOG_FILE}...")
        ultimas_lineas_vistas = set()

        while True:
            try:
                with open(LOG_FILE, 'r') as f:
                    lines = f.readlines()[-3:]  # solo las 3 últimas
                    nuevas_lineas = []

                    for line in lines:
                        line_id = hash(line.strip())  # usamos hash para identificarla
                        if line_id not in ultimas_lineas_vistas:
                            nuevas_lineas.append((line_id, line.strip()))

                    for line_id, line in nuevas_lineas:
                        # ICMP
                        if "ICMP Ping Detectado" in line:
                            if ip_match := re.search(r'\d{1,3}(?:\.\d{1,3}){3}', line):
                                ip = ip_match.group()
                                print(f"Nueva alerta ICMP: {ip}")
                                self.alerted_ips[ip] = time.time()
                                await self.send_alert(ip, "ICMP Ping")

                        # SYN Flood
                        if re.search(r'SYN Flood.*detectado', line, re.IGNORECASE):
                            if ip_match := re.search(r'\d{1,3}(?:\.\d{1,3}){3}', line):
                                ip = ip_match.group()
                                print(f"Nueva alerta SYN Flood: {ip}")
                                self.alerted_ips[ip] = time.time()
                                await self.send_alert(ip, "Posible ataque SYN Flood en curso")

                        ultimas_lineas_vistas.add(line_id)

                    # Mantener solo un historial corto
                    if len(ultimas_lineas_vistas) > 50:
                        ultimas_lineas_vistas = set(list(ultimas_lineas_vistas)[-10:])

            except Exception as e:
                print(f"Error en monitor_logs: {str(e)}")

            await asyncio.sleep(2)


async def main():
    print("Iniciando aplicación...")
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )
    
    monitor = IPSMonitor()
    monitor.app = application

    application.add_handler(CommandHandler("bloquear", monitor.handle_bloquear))
    application.add_handler(CommandHandler("whois", monitor.handle_whois))
    application.add_handler(CommandHandler("alertas", monitor.handle_alertas))
    application.add_handler(CommandHandler("help", monitor.handle_help))
    application.add_handler(CommandHandler("status", monitor.handle_status))

    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Comando no reconocido. Usa /help para ayuda.")

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    print("Iniciando bot...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    try:
        await monitor.monitor_logs()
    except asyncio.CancelledError:
        print("Monitor cancelado")
    except KeyboardInterrupt:
        print("\n🔴 Interrupción detectada. Deteniendo bot...")
    finally:
        print("Deteniendo bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        print("✅ Bot detenido correctamente.")

if __name__ == "__main__":
    print("Iniciando servicio...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔴 Bot detenido manualmente.")