#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path


class LoggerYtDlp:
    """Captura los mensajes internos de yt-dlp y los envía a la consola de la app."""
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        if msg.startswith('[debug] '):
            return
        self.app.root.after(0, self.app.log_consola, f"{msg}\n")

    def info(self, msg):
        self.app.root.after(0, self.app.log_consola, f"{msg}\n")

    def warning(self, msg):
        self.app.root.after(0, self.app.log_consola, f"AVISO: {msg}\n")

    def error(self, msg):
        self.app.root.after(0, self.app.log_consola, f"ERROR: {msg}\n")


class SnapLinuxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SnapLinux MP3 v2.3")
        self.root.geometry("700x260")
        self.root.resizable(False, False)

        ruta_icono = "/usr/share/icons/hicolor/256x256/apps/snaplinux-logo.png"
        if os.path.exists(ruta_icono):
            try:
                self.icono_img = tk.PhotoImage(file=ruta_icono)
                self.root.iconphoto(False, self.icono_img)
            except Exception:
                pass

        self.url_var = tk.StringVar()
        self.carpeta_var = tk.StringVar(value=str(Path.home() / "Música"))
        self.descargando = False
        self.actualizando = False
        self.consola_visible = False

        self.configurar_estilos()
        self.crear_interfaz()
        threading.Thread(target=self.verificar_dependencias_inicio, daemon=True).start()

    def configurar_estilos(self):
        self.estilos = ttk.Style()
        self.estilos.theme_use("clam")
        self.estilos.configure("TProgressbar", thickness=12, troughcolor="#e0e0e0", background="#4CAF50", borderwidth=0)

    def crear_interfaz(self):
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        titulo = ttk.Label(self.main_frame, text="🎵 SnapLinux MP3", font=("Arial", 16, "bold"))
        titulo.pack(pady=(0, 10))

        ttk.Label(self.main_frame, text="URL de YouTube:").pack(anchor=tk.W)
        url_frame = ttk.Frame(self.main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))

        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Arial", 11))
        self.url_entry.pack(fill=tk.X, expand=True)

        ttk.Label(self.main_frame, text="Guardar en:").pack(anchor=tk.W)
        ruta_frame = ttk.Frame(self.main_frame)
        ruta_frame.pack(fill=tk.X, pady=(0, 10))

        self.ruta_entry = ttk.Entry(ruta_frame, textvariable=self.carpeta_var, state="readonly", font=("Arial", 10))
        self.ruta_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_buscar = ttk.Button(ruta_frame, text="Buscar...", command=self.seleccionar_carpeta)
        self.btn_buscar.pack(side=tk.RIGHT)

        self.acciones_frame = ttk.Frame(self.main_frame)
        self.acciones_frame.pack(fill=tk.X, pady=(5, 10))

        self.btn_descargar = ttk.Button(self.acciones_frame, text="Descargar MP3", command=self.iniciar_descarga)
        self.btn_descargar.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.btn_actualizar = ttk.Button(self.acciones_frame, text="Actualizar Librerías", command=self.iniciar_actualizacion)
        self.btn_actualizar.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.btn_consola_toggle = ttk.Button(self.acciones_frame, text="Ver Consola 🛠️", command=self.alternar_consola)
        self.btn_consola_toggle.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.lbl_estado = ttk.Label(self.main_frame, text="", font=("Arial", 10, "italic"))
        self.lbl_estado.pack(pady=(5, 2))

        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate", style="TProgressbar")

        self.consola_container = tk.Canvas(self.main_frame, bg=self.root.cget("bg"), highlightthickness=0)
        self.txt_consola = tk.Text(self.consola_container, bd=0, background="#1e1e1e", foreground="#ffffff", font=("Courier", 9), state="disabled", wrap="word")
        self.consola_container.bind("<Configure>", self.dibujar_consola_redondeada)

        # Botón para copiar todo el contenido de la consola al portapapeles
        self.btn_copiar_consola = None

    def dibujar_consola_redondeada(self, event=None):
        self.consola_container.delete("all")
        w = self.consola_container.winfo_width()
        h = self.consola_container.winfo_height()
        r = 16
        self.consola_container.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill="#1e1e1e", outline="#1e1e1e")
        self.consola_container.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill="#1e1e1e", outline="#1e1e1e")
        self.consola_container.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill="#1e1e1e", outline="#1e1e1e")
        self.consola_container.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill="#1e1e1e", outline="#1e1e1e")
        self.consola_container.create_polygon(r, 0, w-r, 0, w, r, w, h-r, w-r, h, r, h, 0, h-r, 0, r, fill="#1e1e1e", outline="#1e1e1e")
        self.consola_container.create_window(8, 8, window=self.txt_consola, anchor="nw", width=w-16, height=h-40)

    def alternar_consola(self):
        if not self.consola_visible:
            self.root.geometry("700x560")
            self.consola_container.pack(fill=tk.BOTH, expand=True, pady=(10, 5))
            if self.btn_copiar_consola is None:
                self.btn_copiar_consola = ttk.Button(self.main_frame, text="📋 Copiar consola", command=self.copiar_consola)
            self.btn_copiar_consola.pack(pady=(0, 5))
            self.btn_consola_toggle.config(text="Ocultar Consola ❌")
            self.consola_visible = True
        else:
            self.consola_container.pack_forget()
            if self.btn_copiar_consola is not None:
                self.btn_copiar_consola.pack_forget()
            self.root.geometry("700x260")
            self.btn_consola_toggle.config(text="Ver Consola 🛠️")
            self.consola_visible = False

    def copiar_consola(self):
        contenido = self.txt_consola.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(contenido)
        messagebox.showinfo("SnapLinux MP3", "Contenido de la consola copiado al portapapeles.\nPuedes pegarlo para pedir soporte.")

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(initialdir=self.carpeta_var.get(), title="Seleccionar Carpeta")
        if carpeta:
            self.carpeta_var.set(carpeta)

    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def verificar_dependencias_inicio(self):
        try:
            subprocess.run([sys.executable, "-c", "import yt_dlp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=5)
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] Sistema listo. Dependencias correctas.\n")
        except Exception:
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] Aviso: 'yt-dlp' no detectado. Presiona 'Actualizar Librerías'.\n")

    def log_consola(self, texto):
        self.txt_consola.config(state="normal")
        self.txt_consola.insert(tk.END, texto)
        self.txt_consola.see(tk.END)
        self.txt_consola.config(state="disabled")

    def alternar_controles(self, estado):
        self.btn_descargar.config(state=estado)
        self.btn_buscar.config(state=estado)
        self.btn_actualizar.config(state=estado)
        self.url_entry.config(state=estado)

    def iniciar_actualizacion(self):
        if self.descargando or self.actualizando:
            return
        self.actualizando = True
        self.alternar_controles("disabled")
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        self.progress_bar['value'] = 0
        self.lbl_estado.config(text="Actualizando yt-dlp... 0%")
        self.log_consola(f"[{self.timestamp()}] Iniciando actualización de yt-dlp...\n")
        hilo_actualizacion = threading.Thread(target=self.actualizar_librerias)
        hilo_actualizacion.daemon = True
        hilo_actualizacion.start()

    def actualizar_librerias(self):
        import socket
        try:
            socket.create_connection(("pypi.org", 80), timeout=3)
        except OSError:
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] ERROR: Sin conexión a internet.\n")
            self.root.after(0, self.finalizar_actualizacion_error, "Error: Sin conexión a internet.")
            return

        comando = [sys.executable, "-m", "pip", "install", "-U", "yt-dlp", "--user"]
        self.root.after(0, self.actualizar_progreso_ui, 20, "Actualizando yt-dlp... 20%")

        try:
            proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            self.root.after(0, self.actualizar_progreso_ui, 60, "Descargando e instalando... 60%")

            for linea in proceso.stdout:
                self.root.after(0, self.log_consola, linea)

            proceso.communicate()
            if proceso.returncode == 0:
                self.root.after(0, self.actualizar_progreso_ui, 100, "Actualización completa.")
                self.root.after(0, self.log_consola, f"[{self.timestamp()}] Actualización completada con éxito.\n")
                self.root.after(0, self.finalizar_actualizacion_exito)
            else:
                self.root.after(0, self.log_consola, f"[{self.timestamp()}] ERROR: pip terminó con código {proceso.returncode}.\n")
                self.root.after(0, self.finalizar_actualizacion_error, "Error en pip.")
        except Exception as e:
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] ERROR: {str(e)}\n{traceback.format_exc()}\n")
            self.root.after(0, self.finalizar_actualizacion_error, f"Error: {str(e)}")

    def actualizar_progreso_ui(self, porcentaje, texto_estado):
        self.progress_bar['value'] = porcentaje
        self.lbl_estado.config(text=texto_estado)

    def finalizar_actualizacion_exito(self):
        messagebox.showinfo("SnapLinux MP3", "Librerías actualizadas.\nReiniciando...")
        self.root.after(1500, self.reiniciar_programa)

    def finalizar_actualizacion_error(self, mensaje_error):
        messagebox.showerror("Error", mensaje_error)
        self.progress_bar.pack_forget()
        self.alternar_controles("normal")
        self.actualizando = False

    def reiniciar_programa(self):
        try:
            args = [sys.executable] + sys.argv
            os.execv(sys.executable, args)
        except Exception:
            self.progress_bar.pack_forget()
            self.alternar_controles("normal")
            self.actualizando = False

    def iniciar_descarga(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Atención", "Introduce una URL válida.")
            return
        self.descargando = True
        self.alternar_controles("disabled")
        self.lbl_estado.config(text="Descargando audio... 0%")
        self.progress_bar.config(mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        self.progress_bar['value'] = 0
        self.log_consola(f"[{self.timestamp()}] Iniciando descarga: {url}\n")

        hilo_descarga = threading.Thread(target=self.ejecutar_descarga, args=(url,))
        hilo_descarga.daemon = True
        hilo_descarga.start()

    def _hook_progreso(self, d):
        if d.get('status') == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            descargado = d.get('downloaded_bytes', 0)
            if total:
                porcentaje = descargado / total * 100
                self.root.after(0, self.actualizar_progreso_ui, porcentaje,
                                 f"Descargando audio... {porcentaje:.0f}%")
        elif d.get('status') == 'finished':
            self.root.after(0, self.actualizar_progreso_ui, 100, "Convirtiendo a MP3...")
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] Descarga de video completa, convirtiendo a MP3...\n")

    def ejecutar_descarga(self, url, intento=1, max_intentos=2):
        try:
            import yt_dlp
        except ImportError:
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] ERROR: yt-dlp no está instalado.\n")
            self.root.after(0, self.finalizar_descarga, False,
                             "Error: 'yt-dlp' no está instalado.\nPresiona 'Actualizar Librerías'.")
            return

        carpeta_destino = self.carpeta_var.get()
        output_template = os.path.join(carpeta_destino, "%(title)s.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'noplaylist': True,
            'progress_hooks': [self._hook_progreso],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }],
            'quiet': True,
            'no_warnings': False,
            'logger': LoggerYtDlp(self),
        }

        self.root.after(0, self.log_consola, f"[{self.timestamp()}] Intento {intento}/{max_intentos}...\n")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] Descarga completada con éxito.\n")
            self.root.after(0, self.finalizar_descarga, True, "Descarga completada con éxito.")
        except Exception as e:
            detalle = f"[{self.timestamp()}] ERROR en intento {intento}: {str(e)}\n"
            self.root.after(0, self.log_consola, detalle)

            if intento < max_intentos:
                self.root.after(0, self.log_consola, f"[{self.timestamp()}] Reintentando descarga automáticamente...\n")
                self.root.after(0, self.actualizar_progreso_ui, 0, f"Reintentando... (intento {intento + 1}/{max_intentos})")
                self.ejecutar_descarga(url, intento=intento + 1, max_intentos=max_intentos)
            else:
                self.root.after(0, self.log_consola,
                                 f"[{self.timestamp()}] Se agotaron los {max_intentos} intentos. "
                                 f"Copia el contenido de esta consola con el botón 'Copiar consola' "
                                 f"si necesitas ayuda para diagnosticar el error.\n")
                self.root.after(0, self.finalizar_descarga, False, f"Error tras {max_intentos} intentos:\n{str(e)}")

    def finalizar_descarga(self, exito, mensaje):
        self.progress_bar.pack_forget()
        self.progress_bar['value'] = 0
        if exito:
            messagebox.showinfo("SnapLinux MP3", mensaje)
            self.lbl_estado.config(text="Descarga finalizada.")
            self.url_var.set("")
        else:
            messagebox.showerror("Error", mensaje)
            self.lbl_estado.config(text="Descarga interrumpida.")
        self.alternar_controles("normal")
        self.descargando = False


if __name__ == "__main__":
    root = tk.Tk()
    app = SnapLinuxApp(root)
    root.mainloop()
