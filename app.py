# -*- coding: utf-8 -*-
"""
WorldBot — Arquitectura correcta según el profesor:
1. Usuario escribe pregunta
2. Pregunta enviada a Ollama via API local
3. Ollama genera el SQL
4. App ejecuta SQL en MySQL
5. Resultado devuelto en lenguaje natural
"""
import customtkinter as ctk
from PIL import Image, ImageDraw
import threading
import mysql.connector
import requests
import re
import os
import json
import tkinter as tk
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "admin"),
    "database": os.getenv("DB_NAME", "world")
}

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL      = os.getenv("MODELO_IA", "qwen2.5:3b")
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ICON_PATH  = os.path.join(BASE_DIR, "imagenes", "ollama.png")

# ══════════════════════════════════════════
# PROMPT PRINCIPAL — Ollama genera SQL
# Optimizado con valores exactos de la BD
# ══════════════════════════════════════════
PROMPT_SQL = """MySQL SQL only. No explanation. No markdown. No semicolon.

Tables:
country(Code,Name,Continent,Region,SurfaceArea,IndepYear,Population,LifeExpectancy,GNP,GovernmentForm,HeadOfState,Capital)
city(ID,Name,CountryCode,District,Population)
countrylanguage(CountryCode,Language,IsOfficial,Percentage)

Joins: city.CountryCode=country.Code | countrylanguage.CountryCode=country.Code

Continents: 'Asia'|'Europe'|'North America'|'Africa'|'Oceania'|'Antarctica'|'South America'
Regions: 'Central America'|'Caribbean'|'Western Europe'|'Eastern Europe'|'Southeast Asia'|'Middle East'|'Nordic Countries'|'Northern Africa'|'Western Africa'|'Eastern Africa'|'Southern Africa'|'South America'|'North America'|'Eastern Asia'|'Southern Europe'|'Southern and Central Asia'

Spanish→DB: europa→'Europe' | asia→'Asia' | africa→'Africa' | america del sur→'South America' | america del norte→'North America' | america central/centroamerica→Region='Central America' | caribe→Region='Caribbean' | america→Continent IN('North America','South America')

Countries: Brazil(not Brasil)|Colombia|Ecuador|Panama|Spain|Venezuela|Mexico|'United States'|'Russian Federation'|China|Japan|Germany|France|Argentina|Chile|Peru|Cuba|'Costa Rica'|Guatemala|Honduras|Nicaragua

Rules:
- JOINs: always prefix city.Name country.Name countrylanguage.Language
- Official languages: IsOfficial='T'
- Size: SurfaceArea
- "how many AND which": SELECT details not COUNT
- "only how many": COUNT(*) AS total
- Large results: add LIMIT 10
- Cannot answer: return NO_SQL

Examples:
"5 paises mas grandes"→SELECT Name,SurfaceArea FROM country ORDER BY SurfaceArea DESC LIMIT 5
"poblacion de Panama"→SELECT Name,Population FROM country WHERE Name='Panama'
"ciudades de Colombia"→SELECT city.Name,city.Population FROM city JOIN country ON city.CountryCode=country.Code WHERE country.Name='Colombia' ORDER BY city.Population DESC
"cuantas ciudades tiene Brazil"→SELECT COUNT(*) AS total FROM city JOIN country ON city.CountryCode=country.Code WHERE country.Name='Brazil'
"cuantas ciudades tiene Brazil y cuales son"→SELECT city.Name,city.Population FROM city JOIN country ON city.CountryCode=country.Code WHERE country.Name='Brazil' ORDER BY city.Population DESC
"idiomas oficiales de Mexico"→SELECT countrylanguage.Language,countrylanguage.Percentage FROM countrylanguage JOIN country ON countrylanguage.CountryCode=country.Code WHERE country.Name='Mexico' AND countrylanguage.IsOfficial='T' ORDER BY countrylanguage.Percentage DESC
"ciudades mas pobladas de Asia"→SELECT city.Name,country.Name,city.Population FROM city JOIN country ON city.CountryCode=country.Code WHERE country.Continent='Asia' ORDER BY city.Population DESC LIMIT 10
"idiomas de Europa"→SELECT country.Name,countrylanguage.Language,countrylanguage.Percentage FROM countrylanguage JOIN country ON countrylanguage.CountryCode=country.Code WHERE country.Continent='Europe' ORDER BY country.Name,countrylanguage.Percentage DESC LIMIT 20
"paises de america central"→SELECT Name,Population FROM country WHERE Region='Central America' ORDER BY Population DESC
"idiomas oficiales de Africa"→SELECT country.Name,countrylanguage.Language FROM countrylanguage JOIN country ON countrylanguage.CountryCode=country.Code WHERE countrylanguage.IsOfficial='T' AND country.Continent='Africa' ORDER BY country.Name
"ciudad mas poblada del mundo"→SELECT city.Name,country.Name,city.Population FROM city JOIN country ON city.CountryCode=country.Code ORDER BY city.Population DESC LIMIT 1
"promedio de poblacion de Asia"→SELECT AVG(Population) AS promedio FROM country WHERE Continent='Asia'
"cuantos paises hay en Europa"→SELECT COUNT(*) AS total FROM country WHERE Continent='Europe'
"esperanza de vida de Japan"→SELECT Name,LifeExpectancy FROM country WHERE Name='Japan'
"forma de gobierno de Colombia"→SELECT Name,GovernmentForm FROM country WHERE Name='Colombia'
"paises con mas de 100 millones"→SELECT Name,Population FROM country WHERE Population>100000000 ORDER BY Population DESC

QUESTION: {pregunta}
SQL:"""


# ══════════════════════════════════════════
# PASO 1: OLLAMA GENERA EL SQL
# ══════════════════════════════════════════
def ollama_genera_sql(pregunta):
    """Envía la pregunta a Ollama y obtiene el SQL."""
    # Normalizar nombres de países en español
    paises = {
        "mexico":"Mexico","méxico":"Mexico","panamá":"Panama","panama":"Panama",
        "colombia":"Colombia","brasil":"Brazil","brazil":"Brazil",
        "argentina":"Argentina","eeuu":"United States","estados unidos":"United States",
        "rusia":"Russian Federation","china":"China","canadá":"Canada","canada":"Canada",
        "alemania":"Germany","francia":"France","españa":"Spain","italia":"Italy",
        "japon":"Japan","japón":"Japan","peru":"Peru","perú":"Peru","chile":"Chile",
        "venezuela":"Venezuela","cuba":"Cuba","costa rica":"Costa Rica",
        "guatemala":"Guatemala","honduras":"Honduras","nicaragua":"Nicaragua",
        "el salvador":"El Salvador","republica dominicana":"Dominican Republic"
    }
    pq = pregunta
    for es, en in sorted(paises.items(), key=lambda x: -len(x[0])):
        if es in pregunta.lower():
            pq = re.sub(re.escape(es), en, pregunta, flags=re.IGNORECASE)
            break

    prompt = PROMPT_SQL.replace("{pregunta}", pq)

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "top_p": 0.1, "num_predict": 200}
        }, timeout=180)

        sql = r.json()["response"].strip()

        # Limpiar respuesta
        sql = sql.replace("```sql","").replace("```","").strip()
        sql = re.sub(r";\s*$", "", sql).strip()

        # Tomar solo la primera línea si hay texto extra después del SQL
        lineas = [l.strip() for l in sql.splitlines() if l.strip()]
        sql_limpio = []
        for linea in lineas:
            lu = linea.upper()
            if sql_limpio and not any(lu.startswith(k) for k in
               ["SELECT","FROM","WHERE","JOIN","ORDER","GROUP","HAVING","LIMIT","AND","OR","ON","LEFT","RIGHT","INNER"]):
                break
            sql_limpio.append(linea)
        sql = " ".join(sql_limpio).strip() if sql_limpio else sql

        if sql.upper() == "NO_SQL" or not sql.upper().startswith("SELECT"):
            return None, "no_sql"

        return sql, "ok"

    except Exception as e:
        err = str(e)
        if "timed out" in err:
            return None, "timeout"
        return None, f"error: {err}"


# ══════════════════════════════════════════
# PASO 2: EJECUTAR EN MYSQL
# ══════════════════════════════════════════
def ejecutar_sql(sql):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()
    cur.execute(sql)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    conn.close()
    return cols, rows


# ══════════════════════════════════════════
# PASO 3: PYTHON FORMATEA RESPUESTA NATURAL
# ══════════════════════════════════════════
def formatear_respuesta(cols, rows):
    """Convierte resultados de MySQL a texto conversacional."""
    if not rows:
        return "No encontré resultados para esa consulta en la base de datos."

    cols_lower = [c.lower() for c in cols]

    # COUNT
    if "total" in cols_lower:
        return f"Según la base de datos, hay un total de {rows[0][0]:,} registros."

    # Un solo resultado
    if len(rows) == 1:
        fila = rows[0]
        partes = []
        for j, v in enumerate(fila):
            if v is None: continue
            vs = f"{v:,.2f}" if isinstance(v,float) else f"{v:,}" if isinstance(v,int) and v>999 else str(v)
            partes.append(f"{cols[j]}: {vs}")
        return "Según la base de datos, " + " | ".join(partes) + "."

    # Múltiples resultados
    total   = len(rows)
    muestra = rows[:10]

    nombre_i = next((i for i,c in enumerate(cols) if c.lower()=="name"), None)
    valor_i  = next((i for i,c in enumerate(cols) if i!=nombre_i), None)

    items = []
    for row in muestra:
        if nombre_i is not None:
            nombre = str(row[nombre_i])
            if valor_i is not None and row[valor_i] is not None:
                v = row[valor_i]
                vs = f"{v:,.0f}" if isinstance(v,(float,int)) and v>999 else str(v)
                items.append(f"{nombre} ({cols[valor_i]}: {vs})")
            else:
                items.append(nombre)
        else:
            items.append(" | ".join(str(v) for v in row if v is not None))

    if len(items) <= 2:
        lista = " y ".join(items)
    else:
        lista = ", ".join(items[:-1]) + f", y {items[-1]}"

    resp = f"Según la base de datos, los resultados son: {lista}."
    if total > 10:
        resp += f" En total hay {total:,} registros."
    resp += "\n\n¿Quieres ver la sentencia SQL de esta consulta?"
    return resp


# ══════════════════════════════════════════
# SALUDOS Y RESPUESTAS CONVERSACIONALES
# ══════════════════════════════════════════
# Números escritos → dígitos
NUMEROS = {
    "uno":"1","dos":"2","tres":"3","cuatro":"4","cinco":"5",
    "seis":"6","siete":"7","ocho":"8","nueve":"9","diez":"10",
    "one":"1","two":"2","three":"3","four":"4","five":"5",
    "six":"6","seven":"7","eight":"8","nine":"9","ten":"10"
}

def normalizar_numeros(texto):
    """Convierte números escritos a dígitos en la pregunta."""
    t = texto
    for palabra, digito in NUMEROS.items():
        t = re.sub(r'\b' + palabra + r'\b', digito, t, flags=re.IGNORECASE)
    return t

def respuesta_saludo(texto):
    t = texto.lower().strip()
    saludo = ""

    if any(w in t for w in ["buenos días","buen día","buen dia","buenos dias","good morning"]):
        saludo = "¡Buenos días"
    elif any(w in t for w in ["buenas tardes","good afternoon"]):
        saludo = "¡Buenas tardes"
    elif any(w in t for w in ["buenas noches","good night","buenas noche"]):
        saludo = "¡Buenas noches"
    elif any(w in t for w in ["buen día","buenas","hola","hi","hello","hey","saludos","qué tal","que tal","como estas","cómo estás"]):
        saludo = "¡Hola"

    if saludo:
        return (f"{saludo}! Soy WorldBot, tu asistente de la base de datos world. "
                "Estoy aquí para ayudarte a consultar información real sobre "
                "países, ciudades e idiomas del mundo. ¿Qué quieres saber?")

    if any(w in t for w in ["quien eres","quién eres","que eres","qué eres","como te llamas"]):
        return ("Soy WorldBot, un asistente conectado a MySQL. "
                "Consulto la base de datos world que contiene información de "
                "239 países, miles de ciudades y los idiomas oficiales de cada país. "
                "¿En qué te puedo ayudar?")

    if any(w in t for w in ["gracias","thank","perfecto","genial","excelente","muy bien"]) and len(t.split())<=5:
        return "¡Con gusto! ¿Hay algo más que quieras consultar?"

    if any(w in t for w in ["adios","adiós","bye","hasta luego","chao","nos vemos"]):
        return "¡Hasta luego! Fue un placer ayudarte con tus consultas."

    if any(w in t for w in ["que puedes","qué puedes","ayuda","help","como funciona","qué haces"]):
        return ("Puedo consultarte información real de la base de datos world:\n\n"
                "• Países: superficie, población, gobierno, continente\n"
                "• Ciudades: población, distrito por país\n"
                "• Idiomas: oficiales y porcentaje por país\n\n"
                "Ejemplos: '5 paises mas grandes', 'ciudades de Panama', "
                "'idiomas de Mexico', 'cuantas ciudades tiene Brazil y cuales son'")

    return None


# ══════════════════════════════════════════
# INTERFAZ MODERNA
# ══════════════════════════════════════════
class App(ctk.CTk):
    BG      = "#f0f2f5"
    BG2     = "#ffffff"
    SURF    = "#ffffff"
    SURF2   = "#e8eaf0"
    BORDER  = "#d0d4e0"
    ACCENT  = "#6366f1"
    ACCENT2 = "#a855f7"
    TXT     = "#1e1e2e"
    TXT2    = "#5c6080"
    TXT3    = "#aaaacc"
    WHITE   = "#ffffff"
    GREEN   = "#10b981"
    RED     = "#ef4444"
    SQLBG   = "#1e2a3a"
    SQLTXT  = "#7dd3fc"

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("WorldBot — Consulta datos del mundo en lenguaje natural")
        self.geometry("950x700")
        self.minsize(750, 550)
        self.configure(fg_color=self.BG)
        self.ultimo_sql   = ""
        self.procesando   = False
        self.chat_row     = 0
        self.en_inicio    = True
        self.primera_vez  = True  # saluda automaticamente la primera vez
        self._build()
        self._pantalla_inicio()

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.main = ctk.CTkFrame(self, fg_color=self.BG, corner_radius=0)
        self.main.grid(row=0, column=0, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # Barra superior
        bar = ctk.CTkFrame(self.main, fg_color=self.BG2, height=52, corner_radius=0,
                           border_width=1, border_color=self.BORDER)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)

        tf = ctk.CTkFrame(bar, fg_color="transparent")
        tf.grid(row=0, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkLabel(tf, text="◆", font=ctk.CTkFont(size=18),
                     text_color=self.ACCENT).pack(side="left", padx=(0,8))
        ctk.CTkLabel(tf, text="WorldBot",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.TXT).pack(side="left")

        sf = ctk.CTkFrame(bar, fg_color="transparent")
        sf.grid(row=0, column=1, pady=8)
        ctk.CTkLabel(sf, text="●", font=ctk.CTkFont(size=10),
                     text_color=self.GREEN).pack(side="left", padx=(0,4))
        ctk.CTkLabel(sf, text=f"MySQL · {MODEL}",
                     font=ctk.CTkFont(size=11), text_color=self.TXT2).pack(side="left")

        ctk.CTkButton(bar, text="✎ Nuevo", width=80, height=32, corner_radius=16,
                      fg_color=self.SURF2, hover_color=self.BORDER,
                      text_color=self.TXT2, font=ctk.CTkFont(size=12),
                      command=self._nuevo_chat
                      ).grid(row=0, column=2, padx=16, pady=8, sticky="e")

        # Chat
        cf = ctk.CTkFrame(self.main, fg_color=self.BG, corner_radius=0)
        cf.grid(row=1, column=0, sticky="nsew")
        cf.grid_rowconfigure(0, weight=1)
        cf.grid_columnconfigure(0, weight=1)
        self.scroll = ctk.CTkScrollableFrame(
            cf, fg_color=self.BG, corner_radius=0,
            scrollbar_button_color=self.SURF2,
            scrollbar_button_hover_color=self.BORDER)
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        # Input
        ia = ctk.CTkFrame(self.main, fg_color=self.BG2, corner_radius=0,
                          border_width=1, border_color=self.BORDER)
        ia.grid(row=2, column=0, sticky="ew")
        ia.grid_columnconfigure(0, weight=1)

        inp = ctk.CTkFrame(ia, fg_color=self.BG, corner_radius=24,
                           border_width=1, border_color=self.BORDER)
        inp.grid(row=0, column=0, sticky="ew", padx=60, pady=12)
        inp.grid_columnconfigure(0, weight=1)

        self.entrada = ctk.CTkTextbox(
            inp, height=46, fg_color="transparent",
            text_color=self.TXT, font=ctk.CTkFont(size=14),
            corner_radius=0, border_width=0, wrap="word", activate_scrollbars=False)
        self.entrada.grid(row=0, column=0, sticky="ew", padx=18, pady=10)
        self.entrada.insert("0.0", "¿Qué quieres descubrir hoy?")
        self.entrada.configure(text_color=self.TXT3)
        self.entrada.bind("<FocusIn>", self._fi)
        self.entrada.bind("<FocusOut>", self._fo)
        self.entrada.bind("<Return>", self._enter)

        mf = ctk.CTkFrame(inp, fg_color=self.SURF2, corner_radius=14)
        mf.grid(row=0, column=1, padx=(0,6), pady=8)
        ctk.CTkLabel(mf, text=f"⚡ {MODEL}",
                     font=ctk.CTkFont(size=11), text_color=self.TXT2).pack(padx=10, pady=5)

        self.btn_send = ctk.CTkButton(
            inp, text="➤", width=38, height=38, corner_radius=19,
            fg_color=self.ACCENT, hover_color=self.ACCENT2,
            text_color=self.WHITE, font=ctk.CTkFont(size=15, weight="bold"),
            command=self._enviar)
        self.btn_send.grid(row=0, column=2, padx=(0,6), pady=8)

    def _pantalla_inicio(self):
        self.f_inicio = ctk.CTkFrame(self.scroll, fg_color=self.BG, corner_radius=0)
        self.f_inicio.grid(row=0, column=0, sticky="nsew")
        self.f_inicio.grid_columnconfigure(0, weight=1)
        self.chat_row = 1

        ctk.CTkLabel(self.f_inicio, text="", height=40, fg_color="transparent").grid(row=0, column=0)

        try:
            img = Image.open(ICON_PATH).resize((90,90), Image.LANCZOS)
            mask = Image.new("L",(90,90),0); ImageDraw.Draw(mask).ellipse((0,0,90,90),fill=255)
            img_r = img.convert("RGBA"); img_r.putalpha(mask)
            ci = ctk.CTkImage(light_image=img_r, dark_image=img_r, size=(90,90))
            ctk.CTkLabel(self.f_inicio, image=ci, text="").grid(row=1, column=0, pady=(0,10))
        except Exception:
            ctk.CTkLabel(self.f_inicio, text="◆",
                         font=ctk.CTkFont(size=50), text_color=self.ACCENT
                         ).grid(row=1, column=0, pady=(0,10))

        ctk.CTkLabel(self.f_inicio, text="Domina tus Datos",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=self.TXT).grid(row=2, column=0, pady=(0,4))
        ctk.CTkLabel(self.f_inicio,
                     text="Consulta la base de datos world con lenguaje natural · Powered by Ollama",
                     font=ctk.CTkFont(size=13), text_color=self.TXT2
                     ).grid(row=3, column=0, pady=(0,24))

        chips = ctk.CTkFrame(self.f_inicio, fg_color=self.BG, corner_radius=0)
        chips.grid(row=4, column=0)
        for emoji, texto in [
            ("🌍","5 paises mas grandes del mundo"),
            ("🏙️","ciudades mas pobladas de Asia"),
            ("🗣️","idiomas oficiales de Mexico"),
            ("👥","cuantas ciudades tiene Brazil y cuales son"),
            ("🌎","paises de America Central"),
            ("🌏","idiomas oficiales de Africa"),
        ]:
            ctk.CTkButton(chips, text=f"  {emoji}  {texto}",
                          fg_color=self.SURF, hover_color=self.SURF2,
                          text_color=self.TXT2, font=ctk.CTkFont(size=13),
                          corner_radius=20, border_width=1, border_color=self.BORDER,
                          height=38, width=360, anchor="w",
                          command=lambda x=texto: self._sugerencia(x)).pack(pady=3)

    def _msg_user(self, texto):
        f = ctk.CTkFrame(self.scroll, fg_color=self.BG, corner_radius=0)
        f.grid(row=self.chat_row, column=0, sticky="ew", padx=24, pady=(12,0))
        f.grid_columnconfigure(0, weight=1); self.chat_row += 1
        bub = ctk.CTkFrame(f, fg_color=self.ACCENT, corner_radius=16)
        bub.grid(row=0, column=0, sticky="e", padx=(150,0))
        ctk.CTkLabel(bub, text=texto, font=ctk.CTkFont(size=14),
                     text_color=self.WHITE, wraplength=450, justify="left"
                     ).pack(padx=16, pady=10)

    def _msg_bot(self, texto, es_sql=False, on_si=None, on_no=None):
        f = ctk.CTkFrame(self.scroll, fg_color=self.BG, corner_radius=0)
        f.grid(row=self.chat_row, column=0, sticky="ew", padx=24, pady=(12,0))
        f.grid_columnconfigure(0, weight=1); self.chat_row += 1
        wrap = max(450, self.winfo_width()-220)

        if es_sql:
            box = ctk.CTkFrame(f, fg_color=self.SQLBG, corner_radius=12,
                               border_width=1, border_color="#1e3a5f")
            box.grid(row=0, column=0, sticky="w", padx=(0,150))
            hdr = ctk.CTkFrame(box, fg_color="#152238", corner_radius=0)
            hdr.pack(fill="x", padx=1, pady=(1,0))
            ctk.CTkLabel(hdr, text="  SQL Query — generado por Ollama",
                         font=ctk.CTkFont(size=11), text_color="#5b9bd5"
                         ).pack(anchor="w", padx=10, pady=4)
            lineas = texto.count("\n")+1
            txt = tk.Text(box, font=("Consolas",12), bg=self.SQLBG, fg=self.SQLTXT,
                          relief="flat", bd=0, height=lineas+1, width=55,
                          cursor="xterm", selectbackground="#1e3a5f",
                          selectforeground="#ffffff")
            txt.insert("1.0", texto); txt.configure(state="disabled")
            txt.pack(padx=14, pady=(6,12))
        else:
            lineas = texto.count("\n")+1
            w = max(45, int(wrap/8))
            txt = tk.Text(f, font=("Segoe UI",13), bg=self.BG, fg=self.TXT,
                          relief="flat", bd=0, height=min(lineas+2,18),
                          wrap="word", cursor="xterm",
                          selectbackground="#c7d2fe", selectforeground="#1e1e2e",
                          width=w)
            txt.insert("1.0", texto); txt.configure(state="disabled")
            txt.grid(row=0, column=0, sticky="w", padx=(0,120))

        if on_si and on_no:
            bf = ctk.CTkFrame(f, fg_color="transparent", corner_radius=0)
            bf.grid(row=1, column=0, sticky="w", pady=(8,0))
            ctk.CTkLabel(bf, text="¿Ver sentencia SQL?",
                         font=ctk.CTkFont(size=12), text_color=self.TXT2
                         ).pack(side="left", padx=(0,10))
            ctk.CTkButton(bf, text="✓ Sí", width=60, height=28, corner_radius=14,
                          fg_color="#14532d", hover_color="#166534",
                          text_color=self.GREEN, font=ctk.CTkFont(size=12),
                          command=on_si).pack(side="left", padx=(0,6))
            ctk.CTkButton(bf, text="✕ No", width=60, height=28, corner_radius=14,
                          fg_color="#fee2e2", hover_color="#fecaca",
                          text_color=self.RED, font=ctk.CTkFont(size=12),
                          command=on_no).pack(side="left")

    def _dots(self, show=True):
        if show:
            f = ctk.CTkFrame(self.scroll, fg_color=self.BG, corner_radius=0)
            f.grid(row=self.chat_row, column=0, sticky="ew", padx=24, pady=(12,0))
            self.chat_row += 1; self._pf = f
            self._dl = ctk.CTkLabel(f, text="●  ○  ○",
                                    font=ctk.CTkFont(size=18), text_color=self.ACCENT)
            self._dl.pack(anchor="w"); self._da = True; self._anim(0)
        else:
            self._da = False
            try: self._pf.destroy(); self.chat_row -= 1
            except Exception: pass

    _da=False; _ds=["●  ○  ○","○  ●  ○","○  ○  ●"]
    def _anim(self,i):
        if self._da:
            try: self._dl.configure(text=self._ds[i%3]); self.after(350,self._anim,i+1)
            except Exception: pass

    def _scroll_dn(self): self.after(150, lambda: self.scroll._parent_canvas.yview_moveto(1.0))
    def _fi(self,e):
        if self.entrada.get("0.0","end").strip()=="¿Qué quieres descubrir hoy?":
            self.entrada.delete("0.0","end"); self.entrada.configure(text_color=self.TXT)
    def _fo(self,e):
        if not self.entrada.get("0.0","end").strip():
            self.entrada.insert("0.0","¿Qué quieres descubrir hoy?"); self.entrada.configure(text_color=self.TXT3)
    def _enter(self,e): self._enviar(); return "break"
    def _sugerencia(self,t):
        self.entrada.delete("0.0","end"); self.entrada.configure(text_color=self.TXT)
        self.entrada.insert("0.0",t); self._enviar()
    def _nuevo_chat(self):
        for w in self.scroll.winfo_children(): w.destroy()
        self.chat_row=0; self.ultimo_sql=""; self.en_inicio=True
        self.primera_vez=True  # resetear saludo en nuevo chat
        self._pantalla_inicio()

    def _enviar(self):
        if self.procesando: return
        p = self.entrada.get("0.0","end").strip()
        if not p or p=="¿Qué quieres descubrir hoy?": return
        self.entrada.delete("0.0","end")
        if self.en_inicio:
            try: self.f_inicio.destroy()
            except Exception: pass
            self.en_inicio=False; self.chat_row=0
        self._msg_user(p)

        # Detectar saludo en el mensaje
        saludo = respuesta_saludo(p)

        # Normalizar números escritos a dígitos
        p = normalizar_numeros(p)

        # Extraer la pregunta quitando el saludo del inicio
        p_sin_saludo = p
        saludos_lista = [
            "buenos días","buenas tardes","buenas noches","buen día",
            "buenos dias","buenas noche","hola","hi","hello","hey",
            "buenas","saludos","qué tal","que tal","como estas","cómo estás"
        ]
        for palabra in sorted(saludos_lista, key=len, reverse=True):
            if p.lower().strip().startswith(palabra):
                p_sin_saludo = p[len(palabra):].strip(" ,.-!¡¿?\n")
                break

        # Primera vez que escribe — saludar siempre
        if self.primera_vez:
            self.primera_vez = False
            if saludo and len(p_sin_saludo) < 5:
                # Solo saludo sin pregunta — responder y NO consultar BD
                self._msg_bot(saludo)
                self._scroll_dn(); return
            elif saludo and len(p_sin_saludo) >= 5:
                # Saludo + pregunta juntos
                self._msg_bot("¡Hola! Un momento, consultando la base de datos...")
                self._scroll_dn()
                p = p_sin_saludo
            else:
                # Primera vez sin saludo — bot saluda y consulta
                self._msg_bot("¡Hola! Soy WorldBot, tu asistente de la base de datos world. "
                              "Consultando tu pregunta...")
                self._scroll_dn()
        else:
            # No es la primera vez
            if saludo and len(p_sin_saludo) < 5:
                # Solo saludo sin pregunta — responder y NO consultar BD
                self._msg_bot(saludo); self._scroll_dn(); return
            elif saludo and len(p_sin_saludo) >= 5:
                # Saludo + pregunta juntos
                self._msg_bot("¡Buenas! Un momento, consultando la base de datos...")
                self._scroll_dn()
                p = p_sin_saludo

        self._dots(True); self._scroll_dn()
        self.procesando=True; self.btn_send.configure(state="disabled")
        threading.Thread(target=self._proc, args=(p,), daemon=True).start()

    def _proc(self, p):
        try:
            # PASO 1: Ollama genera el SQL
            sql, estado = ollama_genera_sql(p)

            if estado == "timeout":
                self.after(0, self._err,
                    "Ollama tardó demasiado. Intenta con una pregunta más corta.")
                return
            if estado == "no_sql" or sql is None:
                self.after(0, self._err,
                    "No pude generar una consulta para esa pregunta.\n"
                    "Prueba con: '5 paises mas grandes', 'ciudades de Panama', "
                    "'idiomas de Mexico'")
                return

            # PASO 2: Ejecutar en MySQL
            try:
                cols, rows = ejecutar_sql(sql)
                self.ultimo_sql = sql
            except mysql.connector.Error as e:
                self.after(0, self._err, f"Error MySQL: {e}\n\nSQL generado:\n{sql}")
                return

            # PASO 3: Formatear respuesta
            resp = formatear_respuesta(cols, rows)
            self.after(0, self._ok, resp, sql)

        except Exception as e:
            self.after(0, self._err, f"Error: {e}")

    def _ok(self, resp, sql):
        self._dots(False)
        self._msg_bot(resp,
            on_si=lambda: (self._msg_bot(sql, es_sql=True), self._scroll_dn()),
            on_no=lambda: (self._msg_bot("¡Perfecto! ¿Hay algo más que quieras consultar?"),
                           self._scroll_dn()))
        self._scroll_dn(); self.procesando=False; self.btn_send.configure(state="normal")

    def _err(self, msg):
        self._dots(False); self._msg_bot(msg)
        self._scroll_dn(); self.procesando=False; self.btn_send.configure(state="normal")


if __name__ == "__main__":
    app = App(); app.mainloop()
