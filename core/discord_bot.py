import discord
import asyncio
import threading
from typing import Optional, Dict, List, Any
import aiohttp # Importar aiohttp

# Importar LocalizationManager para type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .localization import LocalizationManager

# Límite de caracteres/bytes para el valor de un campo de Embed (usaremos bytes)
FIELD_VALUE_LIMIT_BYTES = 1024
TRUNCATION_SUFFIX = "\n..."
# Calcular longitud en bytes del sufijo una vez
TRUNCATION_SUFFIX_BYTES = len(TRUNCATION_SUFFIX.encode('utf-8'))
# SEPARATOR_LINE = "--------------------\n" # Ya no se usa
# SEPARATOR_LINE_BYTES = len(SEPARATOR_LINE.encode('utf-8')) # Ya no se usa

# --- DEBUGGING FLAG ---
DEBUG_EMBED_LENGTH = False # Poner a True para imprimir logs de longitud

class DiscordBot(discord.Client):
    """Maneja la conexión a Discord y el envío de mensajes formateados."""

    def __init__(self, token: str, target_channel_id: int, *args, **kwargs):
        # ... (inicialización sin cambios) ...
        intents = discord.Intents.default(); intents.guilds = True
        super().__init__(intents=intents, *args, **kwargs)
        self.token = token; self.target_channel_id = target_channel_id
        self.target_channel: Optional[discord.TextChannel] = None
        self.ready_event = threading.Event()
        self._bot_loop: Optional[asyncio.AbstractEventLoop] = None

    async def on_ready(self):
        """Se ejecuta cuando el bot se conecta y está listo."""
        # ... (sin cambios) ...
        print(f'Bot conectado como {self.user}')
        self.target_channel = self.get_channel(self.target_channel_id)
        if self.target_channel: print(f'Canal objetivo encontrado: #{self.target_channel.name} ({self.target_channel.id})')
        else:
            print(f'ADVERTENCIA: No se pudo encontrar el canal con ID {self.target_channel_id}.')
            found = False
            for guild in self.guilds:
                channel = guild.get_channel(self.target_channel_id)
                if isinstance(channel, discord.TextChannel):
                    self.target_channel = channel; print(f'Canal objetivo encontrado en guild {guild.name}: #{self.target_channel.name} ({self.target_channel.id})'); found = True; break
            if not found: print(f'ADVERTENCIA FINAL: No se pudo encontrar el canal de texto con ID {self.target_channel_id}.')
        self.ready_event.set()

    async def send_embed_message(self, embed: discord.Embed):
        """Envía un mensaje embed al canal objetivo."""
        # ... (sin cambios) ...
        if not self.is_ready(): print("Error: send_embed_message llamado pero el bot no está listo."); return False
        if not self.target_channel: print(f"Error: No se puede enviar mensaje, canal objetivo (ID: {self.target_channel_id}) no encontrado."); return False
        try: await self.target_channel.send(embed=embed); print(f"Mensaje embed enviado a #{self.target_channel.name}"); return True
        except discord.Forbidden: print(f"Error: Permisos insuficientes para enviar mensajes a #{self.target_channel.name}."); return False
        except discord.HTTPException as e: print(f"Error HTTP al enviar mensaje: {e}"); return False
        except Exception as e: print(f"Error inesperado al enviar mensaje: {e}"); return False

    async def close_bot(self):
        """Cierra la conexión del bot y la sesión http de forma segura."""
        # ... (sin cambios) ...
        print("Cerrando conexión del bot...")
        try:
            http_client = getattr(self, 'http', None)
            if http_client:
                 session = getattr(http_client, '_session', None)
                 if session and not session.closed: print("Cerrando sesión aiohttp interna..."); await session.close(); print("Sesión aiohttp cerrada.")
            if not self.is_closed(): await self.close(); print("Conexión del bot cerrada.")
            else: print("Conexión del bot ya estaba cerrada.")
        except Exception as e: print(f"Error durante el cierre del bot/sesión http: {e}")

    def run_bot_in_thread(self):
        """Ejecuta el bot en un hilo separado."""
        # ... (sin cambios) ...
        def run_it():
            loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop); self._bot_loop = loop
            try: print("Iniciando bot con self.start() en nuevo loop..."); loop.run_until_complete(self.start(self.token))
            except discord.LoginFailure: print("Error Crítico: Token de Discord inválido."); self.ready_event.set()
            except Exception as e: print(f"Error crítico en el hilo del bot durante run_until_complete: {e}"); self.ready_event.set()
            finally:
                 print("Saliendo de run_until_complete en el hilo del bot.")
                 try:
                     print("Deteniendo y cerrando loop del hilo del bot...")
                     if loop.is_running(): loop.stop()
                     tasks = asyncio.all_tasks(loop)
                     if tasks: print(f"Cancelando {len(tasks)} tareas pendientes..."); [task.cancel() for task in tasks]; loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True)); print("Tareas canceladas.")
                     loop.run_until_complete(loop.shutdown_asyncgens()); print("Asyncgens cerrados.")
                 except Exception as e: print(f"Error durante la limpieza del loop del hilo (cancel/shutdown): {e}")
                 finally:
                    if not loop.is_closed(): loop.close(); print("Loop del hilo del bot cerrado.")
                    else: print("Loop del hilo del bot ya estaba cerrado.")
        thread = threading.Thread(target=run_it, name="DiscordBotThread", daemon=True); thread.start(); print("Hilo del bot iniciado."); return thread

    # --- Métodos de ayuda para formatear ---

    def _add_field_safely(self, embed: discord.Embed, name: str, value_lines: List[str]):
        """Añade un campo al embed, truncando el valor si es necesario."""
        # ... (sin cambios en esta función auxiliar) ...
        field_value = ""; current_bytes = 0; truncated = False
        for line in value_lines:
            line_bytes = len(line.encode('utf-8'))
            if current_bytes + line_bytes + TRUNCATION_SUFFIX_BYTES >= FIELD_VALUE_LIMIT_BYTES: truncated = True; break
            field_value += line; current_bytes += line_bytes
        if truncated: field_value += TRUNCATION_SUFFIX; print(f"Advertencia: Valor del campo '{name}' truncado.")
        if field_value:
             final_bytes = len(field_value.encode('utf-8'))
             if final_bytes > FIELD_VALUE_LIMIT_BYTES:
                 print(f"ERROR CRÍTICO: Campo {name} EXCEDIDO ({final_bytes} bytes)!"); encoded_value = field_value.encode('utf-8'); safe_value = encoded_value[:FIELD_VALUE_LIMIT_BYTES - TRUNCATION_SUFFIX_BYTES]; field_value = safe_value.decode('utf-8', errors='ignore') + TRUNCATION_SUFFIX
             embed.add_field(name=name, value=field_value, inline=False); return True
        return False


    def format_embed(self, upload_results: Dict[str, Dict[str, List[Dict]]], failures: List[Dict], loc_manager: 'LocalizationManager', title_prefix: Optional[str] = None) -> Optional[discord.Embed]:
        """
        Formatea los resultados de la subida en un discord.Embed agrupando por ala/escala,
        con un campo por ala/escala y sin campo de fallos separado.
        Formato: [Emoji] **[NombreBoss](URL)** `(Duración)`
        """
        if not self.is_ready():
             print("Advertencia: Intentando formatear embed pero el bot no está listo (emojis podrían faltar).")

        final_title = title_prefix if title_prefix else loc_manager.get_string("embed_title_default")

        embed = discord.Embed(
            title=f"{final_title} [{discord.utils.utcnow().strftime('%Y-%m-%d')}]", # Quitar hora del título principal
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="zenLogBOT by LeShock | LeShock.5261")

        has_success = False

        # Iterar sobre tipos de encuentro y luego alas/escalas
        all_wing_keys = []
        for etype in ["raids", "fractals", "strikes"]: # Orden deseado
            if etype in upload_results:
                sorted_keys = sorted(upload_results[etype].keys())
                all_wing_keys.extend([(etype, key) for key in sorted_keys])

        for encounter_type, wing_key in all_wing_keys:
            results_in_wing = upload_results[encounter_type][wing_key]
            if not results_in_wing: continue

            wing_has_success = any(r.get("success") for r in results_in_wing)
            if not wing_has_success: continue

            field_lines = []
            # Iterar sobre los resultados exitosos en esta ala/escala
            for result in results_in_wing:
                if not result.get("success"): continue
                has_success = True

                boss_name = result.get("boss_name", loc_manager.get_string("history_entry_unknown_boss"))
                link = result.get("link", "")
                duration = result.get("duration")

                emoji_str = ""
                if self.is_ready():
                    emoji_name = boss_name.replace(" ", "_").replace(":", "")
                    emoji = discord.utils.get(self.emojis, name=emoji_name)
                    if emoji: emoji_str = f"{emoji} "

                display_link = link
                if link and link.startswith("https://dps.report/"):
                     display_link = link.replace("https://dps.report/", "https://b.dps.report/", 1)

                # --- NUEVO FORMATO DE LÍNEA ---
                duration_str = f" `({duration})`" if duration else ""
                line = ""
                if display_link:
                    # Nombre en negrita es el enlace
                    line = f"{emoji_str}[**{boss_name}**]({display_link}){duration_str}\n"
                else: # Éxito sin enlace? Mostrar solo nombre en negrita (sin enlace)
                    line = f"{emoji_str}**{boss_name}**{duration_str} | Success (no link)\n" # O localizar
                # --- FIN NUEVO FORMATO ---

                field_lines.append(line)

            # Añadir campo para esta ala/escala si tiene líneas
            if field_lines:
                # Usar wing_key como nombre del campo
                self._add_field_safely(embed, wing_key, field_lines)


        # Si no hubo éxitos, poner mensaje en descripción
        if not has_success:
             embed.description = loc_manager.get_string("history_status_no_history") # O un mensaje específico

        # NO añadir campo de fallos separado

        # Limitar número total de campos
        if len(embed.fields) > 25:
            print("Advertencia: Demasiados campos para el embed.")
            embed.fields = embed.fields[:25]

        return embed

if __name__ == '__main__':
    print("Este script no debe ejecutarse directamente. Es para la clase DiscordBot.")