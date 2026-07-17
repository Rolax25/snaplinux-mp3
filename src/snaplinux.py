#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import sys
import os
import re
import io
import json
import html
import colorsys
import urllib.request
import urllib.parse
import urllib.error
import multiprocessing
from datetime import datetime
from pathlib import Path

BG = "#1e1e2e"
SURFACE0 = "#292a3d"
SURFACE1 = "#313244"
SURFACE2 = "#3b3d54"
TEXT = "#cdd6f4"
SUBTEXT = "#a6adc8"
MAUVE = "#8839ef"
MAUVE_HOVER = "#9d4eff"
TEAL = "#14b8a6"
TEAL_HOVER = "#2dd4bf"
YELLOW = "#f9e2af"
YELLOW_TEXT = "#1e1e2e"
RED = "#f38ba8"

PATRONES_LIMPIEZA = [
    r"\(\s*official\s+lyric\s+video\s*\)",
    r"\(\s*official\s+music\s+video\s*\)",
    r"\(\s*official\s+video\s*\)",
    r"\(\s*official\s+audio\s*\)",
    r"\(\s*lyric\s+video\s*\)",
    r"\(\s*lyrics?\s*\)",
    r"\(\s*letra\s*\)",
    r"\(\s*audio\s*\)",
    r"\(\s*visualizer\s*\)",
    r"\(\s*hd\s*\)",
    r"\(\s*4k\s*\)",
    r"\[\s*official\s+lyric\s+video\s*\]",
    r"\[\s*official\s+music\s+video\s*\]",
    r"\[\s*official\s+video\s*\]",
    r"\[\s*lyrics?\s*\]",
    r"\[\s*letra\s*\]",
    r"\[\s*hd\s*\]",
    r"\[\s*4k\s*\]",
    r"Letra\s+de\s+:",
    r"Video\s+Oficial",
    r"En\s+Vivo",
    r"Live\s+Session"
]

MB_USER_AGENT = "SnapLinuxMP3/3.0 ( https://github.com/Rolax25/snaplinux-mp3 )"
HEADERS_NAVEGADOR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

class LoggerYtDlp:
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        if msg.startswith('[debug] '): return
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
        self.root.title("SnapLinux MP3 v3.0")
        self.root.configure(bg=BG)
        self._configurar_pantalla_completa()

        ruta_icono = "/usr/share/icons/hicolor/256x256/apps/snaplinux-logo.png"
        if os.path.exists(ruta_icono):
            try:
                self.icono_img = tk.PhotoImage(file=ruta_icono)
                self.root.iconphoto(False, self.icono_img)
            except Exception: pass

        self.carpeta_default = Path.home() / "Música" / "SnapLinux"
        self.carpeta_default.mkdir(parents=True, exist_ok=True)

        self.url_var = tk.StringVar()
        self.carpeta_var = tk.StringVar(value=str(self.carpeta_default))
        self.titulo_var = tk.StringVar()
        self.artista_var = tk.StringVar()
        self.album_var = tk.StringVar()
        self.anio_var = tk.StringVar()
        self.duracion_segundos = 0

        self.formato_var = tk.StringVar(value="MP3")
        self.estado_status_var = tk.StringVar(value="Estado: Listo • Esperando URL de YouTube")

        self.descargando = False
        self.actualizando = False
        self.analizando = False
        self.consola_visible = False
        
        # RGB Activo por defecto en el inicio del programa
        self.rgb_activo = True
        self._rgb_job = None
        self._rgb_hue = 0.0

        self.portada_bytes = None
        self.portada_thumb = None
        self.letra_texto = None
        self.portada_encontrada = False
        self.letra_encontrada = False

        self.placeholder_url = "Pega el link de YouTube aquí..."

        self.configurar_estilos()
        self.crear_interfaz()
        
        self._actualizar_texto_calidad()
        
        # Iniciar animación RGB de inmediato
        self._animar_rgb()
        
        threading.Thread(target=self.verificar_dependencias_inicio, daemon=True).start()
        
        # Lanzar la ventana de tutorial automáticamente al iniciar la app
        self.root.after(300, lambda: self.mostrar_tutorial(auto=True))

    def _configurar_pantalla_completa(self):
        try:
            self.root.attributes("-zoomed", True)
        except tk.TclError:
            self.root.update_idletasks()
            ancho = self.root.winfo_screenwidth()
            alto = self.root.winfo_screenheight()
            self.root.geometry(f"{ancho}x{alto}+0+0")
        self.root.resizable(True, True)

    def configurar_estilos(self):
        self.estilos = ttk.Style()
        self.estilos.theme_use("clam")
        self.estilos.configure(".", background=BG, foreground=TEXT, font=("sans-serif", 10))
        self.estilos.configure("TFrame", background=BG)
        self.estilos.configure("TLabel", background=BG, foreground=TEXT)
        self.estilos.configure("Sub.TLabel", background=BG, foreground=SUBTEXT, font=("sans-serif", 9))
        self.estilos.configure("Titulo.TLabel", background=BG, foreground=TEXT, font=("sans-serif", 18, "bold"))
        self.estilos.configure("TEntry", fieldbackground=SURFACE1, foreground=TEXT, insertcolor=TEXT, borderwidth=0)

        self.estilos.configure("Mauve.TButton", background=MAUVE, foreground="white", font=("sans-serif", 11, "bold"), borderwidth=0, padding=10)
        self.estilos.map("Mauve.TButton", background=[("active", MAUVE_HOVER), ("disabled", SURFACE2)])

        self.estilos.configure("Teal.TButton", background=TEAL, foreground="#052e2b", font=("sans-serif", 11, "bold"), borderwidth=0, padding=10)
        self.estilos.map("Teal.TButton", background=[("active", TEAL_HOVER), ("disabled", SURFACE2)])

        self.estilos.configure("Outline.TButton", background=BG, foreground=MAUVE, font=("sans-serif", 11, "bold"), borderwidth=1, padding=10)
        self.estilos.map("Outline.TButton", background=[("active", SURFACE0)])

        self.estilos.configure("Secundario.TButton", background=SURFACE2, foreground=TEXT, font=("sans-serif", 9), borderwidth=0, padding=5)
        self.estilos.map("Secundario.TButton", background=[("active", "#4b4d6b")])

        self.estilos.configure("Amarillo.TButton", background=YELLOW, foreground=YELLOW_TEXT, font=("sans-serif", 9, "bold"), borderwidth=0, padding=6)
        self.estilos.map("Amarillo.TButton", background=[("active", "#fff3c4")])

        self.estilos.configure("TProgressbar", thickness=16, troughcolor=SURFACE1, background=TEAL, borderwidth=0)
        self.estilos.configure("TCombobox", fieldbackground=SURFACE1, background=SURFACE1, foreground=TEXT, arrowcolor=TEXT)
        self.estilos.configure("Vertical.TScrollbar", background=SURFACE2, troughcolor=BG, bordercolor=BG, arrowcolor=TEXT)

    def crear_interfaz(self):
        self.borde_canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0, bd=0)
        self.borde_canvas.pack(fill=tk.BOTH, expand=True)
        self.contenedor = tk.Frame(self.borde_canvas, bg=BG)
        self._ventana_contenedor = self.borde_canvas.create_window(4, 4, window=self.contenedor, anchor="nw")
        self.borde_canvas.bind("<Configure>", self._ajustar_contenedor)

        self.scroll_canvas = tk.Canvas(self.contenedor, bg=BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.contenedor, orient="vertical", command=self.scroll_canvas.yview, style="Vertical.TScrollbar")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.main_frame = ttk.Frame(self.scroll_canvas, padding="24")
        self._ventana_main = self.scroll_canvas.create_window(0, 0, window=self.main_frame, anchor="nw")

        self.main_frame.bind("<Configure>", self._actualizar_scrollregion)
        self.scroll_canvas.bind("<Configure>", self._ajustar_ancho_main)

        self._crear_header()
        self._crear_fila_url()
        self._crear_tarjetas()
        self._crear_progreso()
        self._crear_panel_calidad()
        self._crear_panel_fallback()
        self._crear_botones_inferiores()
        self._crear_consola()

        ttk.Label(self.main_frame, textvariable=self.estado_status_var, style="Sub.TLabel").pack(anchor=tk.W, pady=(10, 0))

    def _ajustar_contenedor(self, event):
        self.borde_canvas.itemconfig(self._ventana_contenedor, width=event.width - 8, height=event.height - 8)

    def _actualizar_scrollregion(self, event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _ajustar_ancho_main(self, event):
        self.scroll_canvas.itemconfig(self._ventana_main, width=event.width)

    def _crear_header(self):
        fila = tk.Frame(self.main_frame, bg=BG)
        fila.pack(fill=tk.X, pady=(0, 16))
        ttk.Label(fila, text="🎵 SnapLinux MP3 v3.0", style="Titulo.TLabel").pack(side=tk.LEFT)

        self.btn_ayuda = tk.Button(fila, text="❓", bg=BG, fg=TEAL, bd=0, font=("sans-serif", 15), activebackground=BG, activeforeground=TEAL_HOVER, command=self.mostrar_tutorial)
        self.btn_ayuda.pack(side=tk.RIGHT, padx=(6, 0))
        self.btn_config = tk.Button(fila, text="⚙", bg=BG, fg=TEAL, bd=0, font=("sans-serif", 15), activebackground=BG, activeforeground=TEAL_HOVER, command=self._abrir_configuracion)
        self.btn_config.pack(side=tk.RIGHT, padx=(6, 0))
        self.btn_creditos = tk.Button(fila, text="🏆", bg=BG, fg=TEAL, bd=0, font=("sans-serif", 15), activebackground=BG, activeforeground=TEAL_HOVER, command=self._abrir_creditos)
        self.btn_creditos.pack(side=tk.RIGHT, padx=(6, 0))
        btn_carpeta = tk.Button(fila, text="📁", bg=BG, fg=TEAL, bd=0, font=("sans-serif", 15), activebackground=BG, activeforeground=TEAL_HOVER, command=self._abrir_carpeta_descargas)
        btn_carpeta.pack(side=tk.RIGHT)

    def mostrar_tutorial(self, auto=False):
        ventana = tk.Toplevel(self.root)
        ventana.title("Guía de Uso Rápido")
        ventana.configure(bg=SURFACE0)
        ventana.geometry("520x450")
        ventana.transient(self.root)
        ventana.grab_set()

        interior = tk.Frame(ventana, bg=SURFACE0)
        interior.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        titulo_txt = "👋 ¡Bienvenido a SnapLinux MP3!" if auto else "💡 Guía de Uso de la Aplicación"
        tk.Label(interior, text=titulo_txt, bg=SURFACE0, fg=TEAL, font=("sans-serif", 14, "bold")).pack(anchor=tk.W, pady=(0, 12))

        texto_tutorial = (
            "Sigue estos sencillos pasos para descargar tu música favorita con la mejor calidad:\n\n"
            "1⃣  **Pega la URL:** Copia un enlace de YouTube y presiona el botón '📋 Pegar' o escríbelo directamente.\n\n"
            "2⃣  **Analiza la pista:** Presiona '🔎 Analizar'. El motor buscará de forma automatizada el título, "
            "artista, álbum, año, la carátula oficial y la letra de la canción.\n\n"
            "3⃣  **⚠ Sobre la Portada (Muy Importante):** Debido a limitaciones temporales o de red con la API de iTunes, "
            "es posible que no cargue la carátula al primer intento. Si esto sucede, **vuelve a presionar el botón "
            "'🔎 Analizar' de nuevo** para forzar al motor a reconectar y descargar la carátula con éxito.\n\n"
            "4⃣  **Personaliza (Opcional):** Puedes corregir los campos manualmente, añadir una portada personalizada "
            "desde tu PC o inyectar una letra que tengas guardada.\n\n"
            "5⃣  **¡Descarga!:** Elige tu formato predilecto (MP3 por defecto a 320 Kbps) y haz clic en '⬇ Descargar'. "
            "El archivo se guardará en tu carpeta de música con todos sus metadatos integrados."
        )

        txt_widget = tk.Text(interior, bg=SURFACE0, fg=TEXT, font=("sans-serif", 10), wrap="word", bd=0, highlightthickness=0)
        txt_widget.insert("1.0", texto_tutorial)
        txt_widget.config(state="disabled")
        txt_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        btn_entendido = ttk.Button(interior, text="¡Entendido, vamos a probar!", style="Teal.TButton", command=ventana.destroy)
        btn_entendido.pack(anchor=tk.E)

    def _abrir_configuracion(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Configuración")
        ventana.configure(bg=SURFACE0)
        ventana.geometry("320x140")
        interior = tk.Frame(ventana, bg=SURFACE0)
        interior.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        tk.Label(interior, text="Configuración", bg=SURFACE0, fg=TEXT, font=("sans-serif", 12, "bold")).pack(anchor=tk.W, pady=(0, 12))
        rgb_var = tk.BooleanVar(value=self.rgb_activo)

        def alternar():
            self._alternar_rgb()
            rgb_var.set(self.rgb_activo)

        chk = tk.Checkbutton(interior, text="✨ Luz RGB en el borde", variable=rgb_var, command=alternar, bg=SURFACE0, fg=TEXT, selectcolor=SURFACE1, activebackground=SURFACE0)
        chk.pack(anchor=tk.W)

    def _abrir_creditos(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Créditos y Especificaciones Técnicas")
        ventana.configure(bg=SURFACE0)
        ventana.geometry("540x480")
        ventana.transient(self.root)
        ventana.grab_set()

        # Añadimos un scroll por si la información es extensa
        canvas_cred = tk.Canvas(ventana, bg=SURFACE0, highlightthickness=0)
        scroll_cred = ttk.Scrollbar(ventana, orient="vertical", command=canvas_cred.yview, style="Vertical.TScrollbar")
        canvas_cred.configure(yscrollcommand=scroll_cred.set)

        scroll_cred.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_cred.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        interior = tk.Frame(canvas_cred, bg=SURFACE0)
        ventana_interior = canvas_cred.create_window(0, 0, window=interior, anchor="nw")

        def _ajustar_ancho_cred(event):
            canvas_cred.itemconfig(ventana_interior, width=event.width)
        canvas_cred.bind("<Configure>", _ajustar_ancho_cred)
        interior.bind("<Configure>", lambda e: canvas_cred.configure(scrollregion=canvas_cred.bbox("all")))

        # CORRECCIÓN: Cambiado tk.Frame por ttk.Frame para que soporte padding de manera correcta
        pad_frame = ttk.Frame(interior, padding="20")
        pad_frame.pack(fill=tk.BOTH, expand=True)

        # Encabezado
        tk.Label(pad_frame, text="🏆 SnapLinux MP3 v3.0", bg=SURFACE0, fg=MAUVE, font=("sans-serif", 16, "bold")).pack(anchor=tk.W)
        tk.Label(pad_frame, text="Gestor avanzado de descargas y metadatos multimedia.", bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 9, "italic")).pack(anchor=tk.W, pady=(0, 12))
        
        tk.Frame(pad_frame, bg=SURFACE2, height=1).pack(fill=tk.X, pady=(0, 12))

        # Sección de Creadores
        tk.Label(pad_frame, text="👥 EQUIPO DE DESARROLLO", bg=SURFACE0, fg=TEAL, font=("sans-serif", 11, "bold")).pack(anchor=tk.W, pady=(0, 6))
        
        creadores = [
            ("👑 Rolan_Dot", "Líder de Proyecto & Desarrollador Principal"),
            ("🚀 Nova", "Arquitectura de Software & Optimización"),
            ("❤ Gema", "Correción de  Código "),
            ("✨ Kyra", "Diseño de Interfaz & Control de Calidad")
        ]

        for creador, rol in creadores:
            f_c = tk.Frame(pad_frame, bg=SURFACE0)
            f_c.pack(fill=tk.X, pady=2)
            tk.Label(f_c, text=creador, bg=SURFACE0, fg=TEXT, font=("sans-serif", 10, "bold")).pack(side=tk.LEFT)
            tk.Label(f_c, text=f" - {rol}", bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 10)).pack(side=tk.LEFT)

        tk.Frame(pad_frame, bg=SURFACE2, height=1).pack(fill=tk.X, pady=14)

        # Sección de Tecnologías y APIs
        tk.Label(pad_frame, text="🛠 APIS & MOTOR DE BÚSQUEDA", bg=SURFACE0, fg=TEAL, font=("sans-serif", 11, "bold")).pack(anchor=tk.W, pady=(0, 6))
        
        apis = [
            ("🎵 iTunes Search API", "Búsqueda automatizada de carátulas en alta resolución (600x600bb)."),
            ("🧠 MusicBrainz API", "Validación cruzada de metadatos, álbumes y años de lanzamiento."),
            ("🎤 Lyrics.ovh API", "Obtención directa de letras de canciones mediante peticiones JSON."),
            ("🕸 Letras.com Web Scraper", "Motor de respaldo implementado para raspado web de letras difíciles.")
        ]

        for api, desc in apis:
            f_a = tk.Frame(pad_frame, bg=SURFACE0)
            f_a.pack(fill=tk.X, pady=3)
            tk.Label(f_a, text=f"• {api}:", bg=SURFACE0, fg=TEXT, font=("sans-serif", 10, "bold")).pack(anchor=tk.W)
            tk.Label(f_a, text=desc, bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 9), justify="left", wraplength=480).pack(anchor=tk.W, padx=(12, 0))

        tk.Frame(pad_frame, bg=SURFACE2, height=1).pack(fill=tk.X, pady=14)

        # Librerías del Núcleo
        tk.Label(pad_frame, text="📦 LIBRERÍAS DEL NÚCLEO", bg=SURFACE0, fg=TEAL, font=("sans-serif", 11, "bold")).pack(anchor=tk.W, pady=(0, 6))
        
        libs = "yt-dlp  •  FFmpeg  •  Mutagen (ID3/MP4/FLAC)  •  Pillow (PIL)  •  Tkinter"
        tk.Label(pad_frame, text=libs, bg=SURFACE0, fg=TEXT, font=("sans-serif", 10), wraplength=480, justify="left").pack(anchor=tk.W, padx=4)

        # Botón cerrar
        ttk.Button(pad_frame, text="Cerrar", style="Secundario.TButton", command=ventana.destroy).pack(anchor=tk.E, pady=(16, 0))

    def _abrir_carpeta_descargas(self):
        try: subprocess.Popen(["xdg-open", self.carpeta_var.get()])
        except Exception as e: messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}")

    def _crear_fila_url(self):
        fila = tk.Frame(self.main_frame, bg=BG)
        fila.pack(fill=tk.X, pady=(0, 16))
        self.url_entry = tk.Entry(fila, textvariable=self.url_var, font=("sans-serif", 11), bg=SURFACE1, fg=SUBTEXT, bd=0, highlightthickness=1, highlightbackground=SURFACE2)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))
        self._activar_placeholder()
        self.url_entry.bind("<FocusIn>", self._limpiar_placeholder)
        self.url_entry.bind("<FocusOut>", self._restaurar_placeholder)

        self.btn_pegar = ttk.Button(fila, text="📋 Pegar", style="Mauve.TButton", command=self._pegar_portapapeles)
        self.btn_pegar.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_analizar = ttk.Button(fila, text="🔎 Analizar", style="Teal.TButton", command=self.iniciar_analisis)
        self.btn_analizar.pack(side=tk.LEFT)

    def _activar_placeholder(self):
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, self.placeholder_url)
        self.url_entry.config(fg=SUBTEXT)

    def _limpiar_placeholder(self, event=None):
        if self.url_entry.get() == self.placeholder_url:
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg=TEXT)

    def _restaurar_placeholder(self, event=None):
        if not self.url_entry.get().strip():
            self._activar_placeholder()

    def _pegar_portapapeles(self):
        try:
            contenido = self.root.clipboard_get().strip()
            self._limpiar_placeholder()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, contenido)
            self.url_entry.config(fg=TEXT)
        except Exception: messagebox.showwarning("Atención", "El portapapeles está vacío.")

    def _obtener_url_real(self):
        valor = self.url_entry.get().strip()
        if valor == self.placeholder_url: return ""
        return valor

    def _crear_tarjetas(self):
        fila = tk.Frame(self.main_frame, bg=BG)
        fila.pack(fill=tk.X, pady=(0, 16))
        datos = [
            ("⚡", "Máxima Calidad", "Audio optimizado al límite", MAUVE),
            ("🛡", "Seguro", "Validación completa de URL", TEAL),
            ("📋", "Metadatos", "Etiquetas ID3 incrustadas", MAUVE),
        ]
        for icono, titulo, sub, color in datos:
            tarjeta = tk.Frame(fila, bg=SURFACE0, highlightthickness=1, highlightbackground=SURFACE2)
            tarjeta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            interior = tk.Frame(tarjeta, bg=SURFACE0)
            interior.pack(fill=tk.BOTH, padx=16, pady=14)
            cab = tk.Frame(interior, bg=SURFACE0)
            cab.pack(fill=tk.X)
            tk.Label(cab, text=icono, bg=SURFACE0, fg=color, font=("sans-serif", 16)).pack(side=tk.LEFT)
            tk.Label(cab, text=titulo, bg=SURFACE0, fg=TEXT, font=("sans-serif", 13, "bold")).pack(side=tk.LEFT, padx=(8, 0))

    def _crear_progreso(self):
        self.progreso_frame = tk.Frame(self.main_frame, bg=BG)
        self.progreso_frame.pack(fill=tk.X, pady=(0, 16))
        fila_txt = tk.Frame(self.progreso_frame, bg=BG)
        fila_txt.pack(fill=tk.X)
        tk.Label(fila_txt, text="Progreso", bg=BG, fg=TEXT, font=("sans-serif", 11, "bold")).pack(side=tk.LEFT)
        self.lbl_progreso_detalle = tk.Label(fila_txt, text="0%", bg=BG, fg=TEAL, font=("sans-serif", 11, "bold"))
        self.lbl_progreso_detalle.pack(side=tk.RIGHT)
        self.progress_bar = ttk.Progressbar(self.progreso_frame, orient="horizontal", mode="determinate", style="TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(8, 0))

    def _crear_panel_calidad(self):
        panel = tk.Frame(self.main_frame, bg=SURFACE0, highlightthickness=1, highlightbackground=SURFACE2)
        panel.pack(fill=tk.X, pady=(0, 12))
        interior = tk.Frame(panel, bg=SURFACE0)
        interior.pack(fill=tk.X, padx=18, pady=16)

        tk.Label(interior, text="🎚 Configuración de Formato y Metadatos", bg=SURFACE0, fg=TEXT, font=("sans-serif", 13, "bold")).pack(anchor=tk.W, pady=(0, 12))

        cuerpo = tk.Frame(interior, bg=SURFACE0)
        cuerpo.pack(fill=tk.X)

        izquierda = tk.Frame(cuerpo, bg=SURFACE0)
        izquierda.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        fila_selects = tk.Frame(izquierda, bg=SURFACE0)
        fila_selects.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(fila_selects, text="Formato de salida:", bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 10)).pack(side=tk.LEFT, padx=(0, 8))
        combo_fmt = ttk.Combobox(fila_selects, textvariable=self.formato_var, values=["MP3", "M4A", "FLAC", "OPUS", "WAV"], state="readonly", font=("sans-serif", 10), width=12)
        combo_fmt.pack(side=tk.LEFT)
        combo_fmt.bind("<<ComboboxSelected>>", self._actualizar_texto_calidad)

        self.lbl_hint_calidad = tk.Label(izquierda, text="", bg=SURFACE0, fg=YELLOW, font=("sans-serif", 10, "italic"))
        self.lbl_hint_calidad.pack(anchor=tk.W, pady=(6, 8))

        grid_meta = tk.Frame(izquierda, bg=SURFACE0)
        grid_meta.pack(fill=tk.X, pady=5)
        grid_meta.columnconfigure(1, weight=1)
        grid_meta.columnconfigure(3, weight=0)

        tk.Label(grid_meta, text="Title:", bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        tk.Entry(grid_meta, textvariable=self.titulo_var, bg=SURFACE1, fg=TEXT, bd=0, insertbackground=TEXT, font=("sans-serif", 11)).grid(row=0, column=1, columnspan=3, sticky="ew", ipady=6, pady=4)

        tk.Label(grid_meta, text="Artist:", bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        tk.Entry(grid_meta, textvariable=self.artista_var, bg=SURFACE1, fg=TEXT, bd=0, insertbackground=TEXT, font=("sans-serif", 11)).grid(row=1, column=1, columnspan=3, sticky="ew", ipady=6, pady=4)

        tk.Label(grid_meta, text="Album:", bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 10, "bold")).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        tk.Entry(grid_meta, textvariable=self.album_var, bg=SURFACE1, fg=TEXT, bd=0, insertbackground=TEXT, font=("sans-serif", 11)).grid(row=2, column=1, sticky="ew", ipady=6, pady=4)

        tk.Label(grid_meta, text="Year:", bg=SURFACE0, fg=SUBTEXT, font=("sans-serif", 10, "bold")).grid(row=2, column=2, sticky="w", padx=(14, 8), pady=4)
        tk.Entry(grid_meta, textvariable=self.anio_var, bg=SURFACE1, fg=TEXT, bd=0, insertbackground=TEXT, font=("sans-serif", 11), width=8, justify="center").grid(row=2, column=3, sticky="w", ipady=6, pady=4)

        fila_manuales = tk.Frame(izquierda, bg=SURFACE0)
        fila_manuales.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(fila_manuales, text="🖼 Portada Manual", style="Secundario.TButton", command=self.seleccionar_portada_manual).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(fila_manuales, text="📝 Letra Local (.txt/.lrc)", style="Secundario.TButton", command=self.cargar_letra_archivo).pack(side=tk.LEFT, padx=(0, 6))
        
        self.btn_ver_letra_pantalla = ttk.Button(fila_manuales, text="🔍 Ver Letra Descargada", style="Amarillo.TButton", command=self.desplegar_pantalla_letra)
        self.btn_ver_letra_pantalla.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_forzar_scraper = ttk.Button(fila_manuales, text="🔍 Forzar Raspado de Letra (Web Scraper)", style="Mauve.TButton", command=self.forzar_motor_scraper_manual)
        self.btn_forzar_scraper.pack(side=tk.LEFT)

        derecha = tk.Frame(cuerpo, bg=SURFACE0)
        derecha.pack(side=tk.LEFT, padx=(20, 0), anchor="n")
        self.cover_container = tk.Frame(derecha, bg=SURFACE0, width=170, height=170, highlightthickness=1, highlightbackground=MAUVE)
        self.cover_container.pack_propagate(False)
        self.cover_container.pack()
        self.lbl_cover = tk.Label(self.cover_container, text="Cover Art\nJPG/PNG", bg=SURFACE0, fg=SUBTEXT, justify="center")
        self.lbl_cover.pack(expand=True)

    def _actualizar_texto_calidad(self, event=None):
        fmt = self.formato_var.get()
        if fmt == "MP3":
            self.lbl_hint_calidad.config(text="✨ Calidad Automática: MP3 (320 Kbps constante - 44100 Hz)")
        elif fmt == "M4A":
            self.lbl_hint_calidad.config(text="✨ Calidad Automática: M4A AAC (Máximo nativo - 48000 Hz)")
        elif fmt in ("FLAC", "WAV"):
            self.lbl_hint_calidad.config(text=f"✨ Calidad Automática: {fmt} (Audio sin pérdida original - 48000 Hz)")
        elif fmt == "OPUS":
            self.lbl_hint_calidad.config(text="✨ Calidad Automática: OPUS (Excelente fidelidad optimizada - 48000 Hz)")

    def desplegar_pantalla_letra(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Letra de la Canción")
        ventana.geometry("460x540")
        ventana.configure(bg=BG)

        interior = tk.Frame(ventana, bg=BG)
        interior.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        tk.Label(interior, text=f"🗚 Letra: {self.titulo_var.get() or 'Pista'}", bg=BG, fg=TEAL, font=("sans-serif", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        txt_frame = tk.Frame(interior, bg="#11111b")
        txt_frame.pack(fill=tk.BOTH, expand=True)

        txt_area = tk.Text(txt_frame, wrap="word", bg="#11111b", fg=TEXT, font=("sans-serif", 11), bd=0, padx=10, pady=10)
        scr = ttk.Scrollbar(txt_frame, orient="vertical", command=txt_area.yview)
        txt_area.configure(yscrollcommand=scr.set)
        
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        txt_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if self.letra_texto:
            txt_area.insert("1.0", self.letra_texto)
        else:
            txt_area.insert("1.0", "[No hay letra disponible o cargada para esta pista.]")
        txt_area.config(state="disabled")

    def _crear_panel_fallback(self):
        self.fallback_frame = tk.Frame(self.main_frame, bg=YELLOW)
        interior = tk.Frame(self.fallback_frame, bg=YELLOW)
        interior.pack(fill=tk.X, padx=14, pady=10)
        tk.Label(interior, text="Aviso: Completar portada o letras de forma manual si falta algún dato.", bg=YELLOW, fg=YELLOW_TEXT, font=("sans-serif", 10, "bold")).pack(anchor=tk.W)
        ttk.Button(interior, text="Pegar Letra Manualmente", style="Amarillo.TButton", command=self.pegar_letra_manual).pack(pady=(6, 0))

    def _actualizar_panel_fallback(self):
        if (not self.portada_encontrada) or (not self.letra_encontrada):
            self.fallback_frame.pack(fill=tk.X, pady=(0, 12), before=self.botones_frame)
        else:
            self.fallback_frame.pack_forget()
        self._actualizar_scrollregion()

    def _crear_botones_inferiores(self):
        self.botones_frame = tk.Frame(self.main_frame, bg=BG)
        self.botones_frame.pack(fill=tk.X, pady=(0, 6))

        self.btn_consola_toggle = ttk.Button(self.botones_frame, text="🗂 Ver Consola", style="Outline.TButton", command=self.alternar_consola)
        self.btn_consola_toggle.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.btn_actualizar = ttk.Button(self.botones_frame, text="🔄 Actualizar Librerías", style="Teal.TButton", command=self.iniciar_actualizacion)
        self.btn_actualizar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        fila_descarga = tk.Frame(self.main_frame, bg=BG)
        fila_descarga.pack(fill=tk.X, pady=(8, 0))
        self.btn_descargar = ttk.Button(fila_descarga, text="⬇ Descargar", style="Mauve.TButton", command=self.iniciar_descarga)
        self.btn_descargar.pack(fill=tk.X)

        ruta_frame = tk.Frame(self.main_frame, bg=BG)
        ruta_frame.pack(fill=tk.X, pady=(10, 0))
        self.ruta_entry = tk.Entry(ruta_frame, textvariable=self.carpeta_var, state="readonly", bg=SURFACE1, fg=TEXT, bd=0)
        self.ruta_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        ttk.Button(ruta_frame, text="Buscar...", style="Secundario.TButton", command=self.seleccionar_carpeta).pack(side=tk.RIGHT, padx=(6,0))

    def _crear_consola(self):
        self.consola_container = tk.Canvas(self.main_frame, bg=BG, highlightthickness=0)
        self.txt_consola = tk.Text(self.consola_container, bd=0, background="#11111b", foreground="#a6e3a1", font=("Courier", 10), state="disabled", wrap="word")
        self.consola_container.bind("<Configure>", self._dibujar_consola_redondeada)
        self.fila_botones_consola = None

    def _dibujar_consola_redondeada(self, event=None):
        self.consola_container.delete("all")
        w = self.consola_container.winfo_width()
        h = self.consola_container.winfo_height()
        if w < 20 or h < 20: return
        self.consola_container.create_polygon(10, 0, w-10, 0, w, 10, w, h-10, w-10, h, 10, h, 0, h-10, 0, 10, fill="#11111b")
        self.consola_container.create_window(8, 8, window=self.txt_consola, anchor="nw", width=w-16, height=h-40)

    def alternar_consola(self):
        if not self.consola_visible:
            self.progreso_frame.pack_forget()
            self.consola_container.config(height=250)
            self.consola_container.pack(fill=tk.BOTH, expand=False, pady=5, before=self.botones_frame)
            if self.fila_botones_consola is None:
                self.fila_botones_consola = tk.Frame(self.main_frame, bg=BG)
                ttk.Button(self.fila_botones_consola, text="📋 Copiar", style="Secundario.TButton", command=self.copiar_consola).pack(side=tk.LEFT)
            self.fila_botones_consola.pack(pady=2, before=self.botones_frame)
            self.btn_consola_toggle.config(text="❌ Ocultar Consola")
            self.consola_visible = True
        else:
            self.consola_container.pack_forget()
            if self.fila_botones_consola: self.fila_botones_consola.pack_forget()
            self.btn_consola_toggle.config(text="🗂 Ver Consola")
            self.consola_visible = False
        self._actualizar_scrollregion()

    def copiar_consola(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.txt_consola.get("1.0", tk.END))

    def _alternar_rgb(self):
        self.rgb_activo = not self.rgb_activo
        if self.rgb_activo: self._animar_rgb()
        else: self.borde_canvas.config(bg=BG)

    def _animar_rgb(self):
        if not self.rgb_activo: return
        self._rgb_hue = (self._rgb_hue + 0.01) % 1.0
        r, g, b = colorsys.hsv_to_rgb(self._rgb_hue, 0.65, 0.9)
        self.borde_canvas.config(bg=f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}")
        self.root.after(40, self._animar_rgb)

    def seleccionar_carpeta(self):
        c = filedialog.askdirectory(initialdir=self.carpeta_var.get())
        if c: self.carpeta_var.set(c)

    def timestamp(self): return datetime.now().strftime("%H:%M:%S")

    def log_consola(self, texto):
        self.txt_consola.config(state="normal")
        self.txt_consola.insert(tk.END, texto)
        self.txt_consola.see(tk.END)
        self.txt_consola.config(state="disabled")

    def actualizar_estado(self, texto): self.estado_status_var.set(f"Estado: {texto}")

    def alternar_controles(self, estado):
        for b in [self.btn_descargar, self.btn_actualizar, self.btn_analizar, self.btn_pegar]: b.config(state=estado)

    def _validar_url(self, url): return re.search(r"(youtube\.com/|youtu\.be/)", url) is not None

    def _limpiar_titulo_video(self, texto):
        res = texto
        for p in PATRONES_LIMPIEZA: res = re.sub(p, "", res, flags=re.IGNORECASE)
        return re.sub(r"\s{2,}", " ", res).strip(" -|–—")

    def _nombre_archivo_seguro(self, texto): return re.sub(r'[\\/*?:"<>|]', "", (texto or "").strip()).replace("%", "%%")

    def verificar_dependencias_inicio(self):
        try:
            subprocess.run([sys.executable, "-c", "import yt_dlp, mutagen, PIL"], check=True, timeout=5)
            self.root.after(0, self.log_consola, f"[{self.timestamp()}] Dependencias correctas.\n")
        except Exception: self.root.after(0, self.log_consola, f"[{self.timestamp()}] Faltan dependencias externas.\n")

    def iniciar_actualizacion(self):
        self.actualizando = True
        self.alternar_controles("disabled")
        threading.Thread(target=self.actualizar_librerias, daemon=True).start()

    def actualizar_librerias(self):
        try:
            p = subprocess.Popen([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "mutagen", "pillow", "--user"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for l in p.stdout: self.root.after(0, self.log_consola, l)
            p.communicate()
            self.root.after(0, lambda: messagebox.showinfo("SnapLinux", "Librerías listas. Reiniciando..."))
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e: self.root.after(0, self.log_consola, f"Error actualizando: {e}\n")

    def iniciar_analisis(self):
        u = self._obtener_url_real()
        if not u or not self._validar_url(u): return
        self.analizando = True
        self.btn_analizar.config(state="disabled")
        threading.Thread(target=self._analizar_video, args=(u,), daemon=True).start()

    def _analizar_video(self, url):
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            t_comp = self._limpiar_titulo_video(info.get('title', ''))
            up = info.get('uploader') or info.get('channel') or ''
            dur = info.get('duration') or 0
            alb = info.get('album') or ''
            anio = str(info.get('release_year') or info.get('upload_date', '')[:4] or '')
            art, tit = self._separar_artista_titulo(t_comp, up)

            res_mb = self._consultar_musicbrainz(art, tit)
            if res_mb:
                art, tit, alb_mb, anio_mb = res_mb
                if alb_mb: alb = alb_mb
                if anio_mb: anio = anio_mb

            self.root.after(0, self._aplicar_resultado_analisis, art, tit, alb, anio, dur)
        except Exception as e:
            self.root.after(0, self.log_consola, f"Error analizando: {e}\n")
            self.root.after(0, self._finalizar_analisis)

    def _consultar_musicbrainz(self, artista, titulo):
        try:
            titulo_limpio = re.sub(r"\(.*?\)|\[.*?\]", "", titulo).strip()
            artista_limpio = re.sub(r"\(.*?\)|\[.*?\]", "", artista).strip()
            c = f'recording:"{titulo_limpio}" AND artist:"{artista_limpio}"'
            url = "https://musicbrainz.org/ws/2/recording/?query=" + urllib.parse.quote(c) + "&fmt=json&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": MB_USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as r:
                d = json.loads(r.read().decode("utf-8"))
            recs = d.get("recordings", [])
            if not recs or recs[0].get("score", 0) < 70: return None
            top = recs[0]
            rel = top.get("releases", [])
            return (top.get("artist-credit", [{}])[0].get("name", ""), top.get("title", ""), rel[0].get("title", "") if rel else "", (rel[0].get("date", "") if rel else "")[:4])
        except Exception: return None

    def _separar_artista_titulo(self, t, up):
        for s in [" - ", " – ", " — "]:
            if s in t:
                p = t.split(s, 1)
                return p[0].strip(), p[1].strip()
        return up.strip(), t.strip()

    def _aplicar_resultado_analisis(self, art, tit, alb, anio, dur):
        self.artista_var.set(art)
        self.titulo_var.set(tit)
        self.album_var.set(alb)
        self.anio_var.set(anio)
        self.duracion_segundos = int(dur)
        self._finalizar_analisis()
        self.portada_encontrada = False
        self.letra_encontrada = False
        self.letra_texto = None
        threading.Thread(target=self._buscar_portada, args=(art, tit), daemon=True).start()
        threading.Thread(target=self._buscar_letra, args=(art, tit), daemon=True).start()

    def _finalizar_analisis(self):
        self.analizando = False
        self.btn_analizar.config(state="normal")

    def _buscar_portada(self, art, tit):
        a = re.sub(r'\(.*?\)|\[.*?\]', '', art).strip()
        t = re.sub(r'\(.*?\)|\[.*?\]', '', tit).strip()
        img = self._portada_itunes(a, t)
        if img: self.root.after(0, self._resultado_portada, img)
        else: self.root.after(0, self._resultado_portada, None)

    def _portada_itunes(self, art, tit):
        try:
            u = f"https://itunes.apple.com/search?term={urllib.parse.quote(f'{art} {tit}')}&media=music&limit=1"
            with urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS_NAVEGADOR), timeout=8) as r:
                res = json.loads(r.read().decode("utf-8")).get("results", [])
            if res:
                img_url = res[0]["artworkUrl100"].replace("100x100bb", "600x600bb")
                with urllib.request.urlopen(urllib.request.Request(img_url, headers=HEADERS_NAVEGADOR), timeout=8) as img_r:
                    return img_r.read()
        except Exception as e:
            return None

    def _resultado_portada(self, img_bytes):
        self.portada_encontrada = img_bytes is not None
        if img_bytes:
            self.portada_bytes = img_bytes
            try:
                from PIL import Image, ImageTk
                i = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((166, 166))
                self.portada_thumb = ImageTk.PhotoImage(i)
                self.lbl_cover.config(image=self.portada_thumb, text="")
            except Exception: pass
        else:
            self.lbl_cover.config(image="", text="Cover Art\nNo Encontrada")
        self._actualizar_panel_fallback()

    def seleccionar_portada_manual(self):
        r = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if r:
            try:
                from PIL import Image
                img = Image.open(r).convert("RGB")
                b = io.BytesIO()
                img.save(b, format="JPEG")
                self._resultado_portada(b.getvalue())
            except Exception: pass

    def forzar_motor_scraper_manual(self):
        art = self.artista_var.get()
        tit = self.titulo_var.get()
        if not art or not tit:
            messagebox.showwarning("Atención", "Primero debes ingresar o analizar un artista y título.")
            return
        self.log_consola(f"[{self.timestamp()}] 🚀 Ejecutando raspado web de letras explícito...\n")
        threading.Thread(target=self._ejecutar_scraper_puro, args=(art, tit), daemon=True).start()

    def _buscar_letra(self, art, tit):
        a_limpio = re.sub(r'\(.*?\)|\[.*?\]', '', art).strip()
        t_limpio = re.sub(r'\(.*?\)|\[.*?\]', '', tit).strip()
        
        try:
            u = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(a_limpio)}/{urllib.parse.quote(t_limpio)}"
            req = urllib.request.Request(u, headers=HEADERS_NAVEGADOR)
            with urllib.request.urlopen(req, timeout=5) as r:
                texto = json.loads(r.read().decode("utf-8")).get("lyrics", "").strip()
                if texto:
                    self.root.after(0, self._resultado_letra, texto, "Lyrics.ovh API")
                    return
        except Exception: pass

        self._ejecutar_scraper_puro(a_limpio, t_limpio)

    def _ejecutar_scraper_puro(self, art, tit):
        a_limpio = re.sub(r'\(.*?\)|\[.*?\]', '', art).strip()
        t_limpio = re.sub(r'\(.*?\)|\[.*?\]', '', tit).strip()
        
        for p in PATRONES_LIMPIEZA:
            t_limpio = re.sub(p, "", t_limpio, flags=re.IGNORECASE)
        t_limpio = t_limpio.strip()

        try:
            query_busqueda = f"{a_limpio} {t_limpio} letras.com"
            u_busqueda = "https://www.bing.com/search?q=" + urllib.parse.quote(query_busqueda)
            req = urllib.request.Request(u_busqueda, headers=HEADERS_NAVEGADOR)
            
            with urllib.request.urlopen(req, timeout=8) as r:
                html_res = r.read().decode("utf-8", errors="ignore")
            
            enlaces = re.findall(r'href="(https://www\.letras\.com/[a-zA-Z0-9\-]+/[a-zA-Z0-9\-]+/)"', html_res)
            if not enlaces:
                enlaces = re.findall(r'href="(https://www\.letras\.com/[^"]+)"', html_res)
            
            if enlaces:
                target_url = html.unescape(enlaces[0])
                req_letra = urllib.request.Request(target_url, headers=HEADERS_NAVEGADOR)
                with urllib.request.urlopen(req_letra, timeout=8) as r2:
                    lyric_html = r2.read().decode("utf-8", errors="ignore")
                
                bloque = re.search(r'<div class="lyric-original">(.*?)</div>\s*</article>', lyric_html, re.DOTALL)
                if bloque:
                    texto_limpio = re.sub(r'<p>|<br\s*/?>', '\n', bloque.group(1))
                    texto_limpio = re.sub(r'<[^>]+>', '', texto_limpio)
                    texto_limpio = html.unescape(texto_limpio).strip()
                    if texto_limpio:
                        self.root.after(0, self._resultado_letra, texto_limpio, "Motor Web Scraper (Letras.com)")
                        return
        except Exception as e:
            pass
        self.root.after(0, self._resultado_letra, None, None)

    def _resultado_letra(self, letra, fuente):
        self.letra_encontrada = letra is not None
        if letra:
            self.letra_texto = letra
            self.log_consola(f"[{self.timestamp()}] Letra inyectada correctamente desde [{fuente}].\n")
        else:
            if fuente is not None:
                self.log_consola(f"[{self.timestamp()}] No se localizó la letra de forma automática.\n")
        self._actualizar_panel_fallback()

    def pegar_letra_manual(self):
        v = tk.Toplevel(self.root)
        v.title("Letra Manual")
        v.geometry("400x400")
        t = tk.Text(v, bg=SURFACE1, fg=TEXT)
        t.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        def s():
            ctx = t.get("1.0", tk.END).strip()
            if ctx: self._resultado_letra(ctx, "Manual")
            v.destroy()
        ttk.Button(v, text="Guardar", command=s).pack(pady=4)

    def cargar_letra_archivo(self):
        r = filedialog.askopenfilename(filetypes=[("Letras", "*.txt *.lrc")])
        if r:
            try:
                with open(r, "r", encoding="utf-8", errors="ignore") as f:
                    ctx = f.read()
                ctx = re.sub(r"\[\d{2}:\d{2}(\.\d{2})?\]", "", ctx).strip()
                self._resultado_letra(ctx, "Archivo Local")
            except Exception: pass

    def iniciar_descarga(self):
        u = self._obtener_url_real()
        if not u: return
        self.descargando = True
        self.alternar_controles("disabled")
        if not self.consola_visible: self.progreso_frame.pack(fill=tk.X, pady=(0, 16))
        self.progress_bar['value'] = 0
        threading.Thread(target=self.ejecutar_descarga, args=(u,), daemon=True).start()

    def _hook_progreso(self, d):
        if d.get('status') == 'downloading':
            t = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            p = (d.get('downloaded_bytes', 0) / t) * 100
            self.root.after(0, lambda: self.progress_bar.config(value=p))
            self.root.after(0, lambda: self.lbl_progreso_detalle.config(text=f"{p:.0f}%"))

    def ejecutar_descarga(self, url):
        import yt_dlp
        f_ext = self.formato_var.get().lower()
        dest = self.carpeta_var.get()

        a_file = self._nombre_archivo_seguro(self.artista_var.get())
        t_file = self._nombre_archivo_seguro(self.titulo_var.get())
        n_base = f"{a_file} - {t_file}" if (a_file and t_file) else "%(title)s"
        out_tmpl = os.path.join(dest, f"{n_base}.%(ext)s")

        if f_ext == "mp3":
            pref_quality = "320"
            s_rate = "44100"
        elif f_ext == "m4a":
            pref_quality = "0"  
            s_rate = "48000"    
        else:
            pref_quality = "0"  
            s_rate = "48000"

        opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_tmpl,
            'noplaylist': True,
            'progress_hooks': [self._hook_progreso],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': f_ext,
                'preferredquality': pref_quality
            }],
            'postprocessor_args': {
                'FFmpegExtractAudio': ['-ar', str(s_rate)]
            },
            'quiet': True,
            'logger': LoggerYtDlp(self)
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            r_final = os.path.join(dest, f"{n_base}.{f_ext}") if (a_file and t_file) else os.path.splitext(ydl.prepare_filename(info))[0] + "." + f_ext
            
            if os.path.exists(r_final):
                self._incrustar_metadatos(r_final, f_ext)
            self.root.after(0, self.finalizar_descarga, True, "Procesamiento completado con éxito.")
        except Exception as e:
            self.root.after(0, self.finalizar_descarga, False, f"Error:\n{e}")

    def _incrustar_metadatos(self, path, ext):
        t = self.titulo_var.get().strip()
        a = self.artista_var.get().strip()
        al = self.album_var.get().strip()
        yr = self.anio_var.get().strip()
        try:
            if ext == "mp3":
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC, USLT
                audio = MP3(path, ID3=ID3)
                try: audio.add_tags()
                except Exception: pass
                if t: audio.tags.add(TIT2(encoding=3, text=t))
                if a: audio.tags.add(TPE1(encoding=3, text=a))
                if al: audio.tags.add(TALB(encoding=3, text=al))
                if yr: audio.tags.add(TDRC(encoding=3, text=yr))
                if self.portada_bytes: audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=self.portada_bytes))
                if self.letra_texto: audio.tags.add(USLT(encoding=3, lang='spa', desc='', text=self.letra_texto))
                audio.save()
            elif ext in ("m4a", "alac"):
                from mutagen.mp4 import MP4, MP4Cover
                audio = MP4(path)
                if t: audio["©nam"] = [t]
                if a: audio["©ART"] = [a]
                if al: audio["©alb"] = [al]
                if yr: audio["©day"] = [yr]
                if self.letra_texto: audio["©lyr"] = [self.letra_texto]
                if self.portada_bytes: audio["covr"] = [MP4Cover(self.portada_bytes, imageformat=MP4Cover.FORMAT_JPEG)]
                audio.save()
            elif ext == "flac":
                from mutagen.flac import FLAC, Picture
                audio = FLAC(path)
                if t: audio["title"] = t
                if a: audio["artist"] = a
                if al: audio["album"] = al
                if yr: audio["date"] = yr
                if self.letra_texto: audio["lyrics"] = self.letra_texto
                if self.portada_bytes:
                    p = Picture()
                    p.data = self.portada_bytes
                    p.type = 3
                    p.mime = "image/jpeg"
                    audio.add_picture(p)
                audio.save()
        except Exception: pass

    def finalizar_descarga(self, exito, mensaje):
        if not self.consola_visible: self.progreso_frame.pack_forget()
        if exito: messagebox.showinfo("SnapLinux", mensaje)
        else: messagebox.showerror("SnapLinux", mensaje)
        self.alternar_controles("normal")
        self.descargando = False

if __name__ == '__main__':
    # Esta línea es la que detiene las ventanas infinitas en Windows compilado:
    multiprocessing.freeze_support()
    
    root = tk.Tk()
    app = SnapLinuxApp(root)
    root.mainloop()
