"""
scraper_eventos.py  v4
======================
Extrae eventos culturales con imagen y descripción desde:
  - Ticketplus.cl  (Región de Antofagasta)
  - Ticketpro.cl   (filtrando ciudades del norte)
  - PuntoTicket.com (filtrando ciudades del norte)

Por cada evento visita su página individual y extrae:
  - nombre      → título limpio (artista / show)
  - venue       → lugar del evento
  - imagen_url  → meta og:image
  - descripcion → meta og:description
  - fecha_iso   → fecha en formato YYYY-MM-DD (para ordenar en Swift)
  - fecha_texto → fecha legible en español

Requisitos:
    pip install requests beautifulsoup4

Uso:
    python scraper_eventos.py
"""

import json
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ── Configuración ────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

CIUDADES_OBJETIVO = [
    "antofagasta", "calama", "iquique", "arica",
    "tocopilla", "mejillones", "taltal",
]

VENUES_CONOCIDOS = [
    "teatro municipal de antofagasta",
    "teatro municipal de calama",
    "teatro municipal de iquique",
    "teatro municipal",
    "rock and soccer",
    "centro cultural estación",
    "sala andamios",
    "enjoy antofagasta",
    "estadio regional",
    "club hípico",
    "gimnasio olímpico",
]

OUTPUT_FILE = "eventos.json"
PAUSA = 0.8

MESES_ES = {
    "ene": 1, "enero": 1,
    "feb": 2, "febrero": 2,
    "mar": 3, "marzo": 3,
    "abr": 4, "abril": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "junio": 6,
    "jul": 7, "julio": 7,
    "ago": 8, "agosto": 8,
    "sep": 9, "septiembre": 9,
    "oct": 10, "octubre": 10,
    "nov": 11, "noviembre": 11,
    "dic": 12, "diciembre": 12,
}

MESES_TEXTO = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

MESES_PATTERN = "|".join(MESES_ES.keys())


# ── Utilidades ───────────────────────────────────────────────────────────────

def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        print(f"  ⚠️  {url} → {e}")
        return None


def limpiar(texto):
    return re.sub(r"\s+", " ", texto).strip()


def es_ciudad_objetivo(texto):
    return any(c in texto.lower() for c in CIUDADES_OBJETIVO)


def parsear_fecha(dia, mes_str):
    mes_str = mes_str.lower().strip()
    mes_num = MESES_ES.get(mes_str)
    if not mes_num:
        return "", ""
    anio = datetime.now().year
    ahora = datetime.now()
    if mes_num < ahora.month or (mes_num == ahora.month and int(dia) < ahora.day):
        anio += 1
    try:
        fecha = datetime(anio, mes_num, int(dia))
        iso = fecha.strftime("%Y-%m-%d")
        texto = f"{int(dia)} de {MESES_TEXTO[mes_num]} de {anio}"
        return iso, texto
    except ValueError:
        return "", ""


def extraer_fecha_de_texto(texto):
    """Busca patrones de fecha en un texto y retorna (fecha_iso, fecha_texto)."""
    patron = re.search(
        rf"(\d{{1,2}})\s+(?:de\s+)?({MESES_PATTERN})",
        texto, re.IGNORECASE
    )
    if patron:
        return parsear_fecha(patron.group(1), patron.group(2))
    return "", ""


def detectar_venue(texto):
    """Detecta un venue conocido en el texto."""
    texto_lower = texto.lower()
    for v in VENUES_CONOCIDOS:
        if v in texto_lower:
            return v.title()
    return ""


def detectar_ciudad(texto):
    """Detecta la ciudad en un texto."""
    texto_lower = texto.lower()
    for c in CIUDADES_OBJETIVO:
        if c in texto_lower:
            return c.capitalize()
    return ""


def limpiar_nombre(nombre_crudo, venue="", ciudad=""):
    """
    Limpia el nombre del evento eliminando:
    - Venue repetido
    - Ciudad
    - Fechas (DD MES, DD de MES)
    - Precios (Desde: CLP ..., $...)
    - Texto residual
    """
    nombre = nombre_crudo

    # Quitar precios
    nombre = re.sub(r"Desde:?\s*CLP\s*[\d\.]+\s*CLP?", "", nombre, flags=re.IGNORECASE)
    nombre = re.sub(r"Desde:?\s*\$?\s*[\d\.]+", "", nombre, flags=re.IGNORECASE)
    nombre = re.sub(r"CLP\s*[\d\.]+", "", nombre, flags=re.IGNORECASE)
    nombre = re.sub(r"\$\s*[\d\.]+", "", nombre, flags=re.IGNORECASE)

    # Quitar fechas (DD MES, DD de MES de YYYY)
    nombre = re.sub(
        rf"\d{{1,2}}\s+(?:de\s+)?(?:{MESES_PATTERN})(?:\s+(?:de\s+)?\d{{4}})?",
        "", nombre, flags=re.IGNORECASE
    )

    # Quitar venue si está al inicio o repetido
    if venue:
        nombre = re.sub(re.escape(venue), "", nombre, flags=re.IGNORECASE)

    # Quitar ciudades
    for c in CIUDADES_OBJETIVO:
        nombre = re.sub(rf"\b{c}\b", "", nombre, flags=re.IGNORECASE)

    # Quitar separadores sueltos
    nombre = re.sub(r"\s*-\s*$", "", nombre)
    nombre = re.sub(r"^\s*-\s*", "", nombre)
    nombre = re.sub(r"\s*-\s*-\s*", " - ", nombre)

    return limpiar(nombre).strip(" -–—·")


def extraer_detalle(url):
    """
    Visita la página del evento y extrae:
      - og_title (título limpio)
      - imagen_url
      - descripcion
      - fecha_iso y fecha_texto
      - venue (si se puede detectar)
    """
    r = get(url)
    if not r:
        return "", "", "", "", "", ""

    soup = BeautifulSoup(r.text, "html.parser")

    # og:title
    og_title = ""
    tag = soup.find("meta", property="og:title")
    if tag and tag.get("content"):
        og_title = limpiar(tag["content"])

    # Imagen
    imagen = ""
    tag = soup.find("meta", property="og:image")
    if tag and tag.get("content"):
        imagen = tag["content"].strip()
    if not imagen:
        tag = soup.find("meta", attrs={"name": "twitter:image"})
        if tag and tag.get("content"):
            imagen = tag["content"].strip()

    # Descripción
    descripcion = ""
    tag = soup.find("meta", property="og:description")
    if tag and tag.get("content"):
        descripcion = limpiar(tag["content"])
    if not descripcion:
        tag = soup.find("meta", attrs={"name": "description"})
        if tag and tag.get("content"):
            descripcion = limpiar(tag["content"])

    # Fecha desde descripción o título
    fecha_iso, fecha_texto = extraer_fecha_de_texto(descripcion)
    if not fecha_iso:
        fecha_iso, fecha_texto = extraer_fecha_de_texto(og_title)

    # Venue
    venue = detectar_venue(og_title) or detectar_venue(descripcion)

    return og_title, imagen, descripcion, fecha_iso, fecha_texto, venue


# ── Scraper 1: Ticketplus ────────────────────────────────────────────────────

def scrape_ticketplus():
    print("\n🔍 Ticketplus.cl ...")
    r = get("https://ticketplus.cl/states/region-de-antofagasta")
    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    base = []

    for a in soup.find_all("a", href=re.compile(r"/events/")):
        texto = limpiar(a.get_text(" "))
        href = a.get("href", "")
        if not texto or len(texto) < 5:
            continue

        precio_match = re.search(r"CLP\s*([\d\.]+)", texto)
        precio = precio_match.group(1) if precio_match else ""

        evento_url = f"https://ticketplus.cl{href}" if href.startswith("/") else href
        base.append({
            "texto_crudo": texto,
            "precio": precio,
            "url": evento_url,
        })

    print(f"  → Obteniendo detalle de {len(base)} eventos...")
    eventos = []
    for i, b in enumerate(base):
        print(f"    [{i+1}/{len(base)}] {b['url'].split('/')[-1][:50]}...")
        og_title, imagen, desc, fecha_iso, fecha_texto, venue = extraer_detalle(b["url"])

        # Decidir el mejor nombre:
        # 1. og:title suele ser más limpio que el texto del listado
        # 2. Si no hay og:title, usar la descripción
        # 3. Último recurso: texto crudo del listado
        nombre_base = og_title or desc or b["texto_crudo"]

        # Detectar venue y ciudad
        if not venue:
            venue = detectar_venue(b["texto_crudo"])
        ciudad = detectar_ciudad(b["texto_crudo"]) or "Antofagasta"

        # Si no tenemos fecha del detalle, intentar del texto crudo
        if not fecha_iso:
            fecha_iso, fecha_texto = extraer_fecha_de_texto(b["texto_crudo"])

        # Limpiar nombre
        nombre = limpiar_nombre(nombre_base, venue=venue, ciudad=ciudad)

        eventos.append({
            "fuente": "Ticketplus",
            "nombre": nombre,
            "venue": venue,
            "descripcion": desc,
            "fecha_iso": fecha_iso,
            "fecha_texto": fecha_texto,
            "precio_desde_clp": b["precio"],
            "ciudad": ciudad,
            "imagen_url": imagen,
            "url": b["url"],
        })
        time.sleep(PAUSA)

    print(f"  ✅ {len(eventos)} eventos")
    return eventos


# ── Scraper 2: Ticketpro ─────────────────────────────────────────────────────

def scrape_ticketpro():
    print("\n🔍 Ticketpro.cl ...")
    r = get("https://www.ticketpro.cl/")
    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    base = []

    for a in soup.find_all("a", href=re.compile(r"/evento/")):
        texto = limpiar(a.get_text(" "))
        href = a.get("href", "")
        if not texto or len(texto) < 5 or not es_ciudad_objetivo(texto):
            continue

        precio_match = re.search(r"\$\s*([\d\.]+)", texto)
        precio = precio_match.group(1) if precio_match else ""

        ciudad_det = detectar_ciudad(texto) or ""

        evento_url = f"https://www.ticketpro.cl{href}" if href.startswith("/") else href
        base.append({
            "texto_crudo": texto,
            "precio": precio,
            "ciudad": ciudad_det,
            "url": evento_url,
        })

    print(f"  → Obteniendo detalle de {len(base)} eventos...")
    eventos = []
    for i, b in enumerate(base):
        print(f"    [{i+1}/{len(base)}] {b['url'].split('/')[-1][:50]}...")
        og_title, imagen, desc, fecha_iso, fecha_texto, venue = extraer_detalle(b["url"])

        nombre_base = og_title or desc or b["texto_crudo"]
        if not venue:
            venue = detectar_venue(b["texto_crudo"])
        ciudad = b["ciudad"] or detectar_ciudad(b["texto_crudo"])

        if not fecha_iso:
            fecha_iso, fecha_texto = extraer_fecha_de_texto(b["texto_crudo"])

        nombre = limpiar_nombre(nombre_base, venue=venue, ciudad=ciudad)

        eventos.append({
            "fuente": "Ticketpro",
            "nombre": nombre,
            "venue": venue,
            "descripcion": desc,
            "fecha_iso": fecha_iso,
            "fecha_texto": fecha_texto,
            "precio_desde_clp": b["precio"],
            "ciudad": ciudad,
            "imagen_url": imagen,
            "url": b["url"],
        })
        time.sleep(PAUSA)

    print(f"  ✅ {len(eventos)} eventos")
    return eventos


# ── Scraper 3: PuntoTicket ───────────────────────────────────────────────────

def scrape_puntoticket():
    print("\n🔍 PuntoTicket.com ...")
    base = []

    ciudades_pt = {
        "Antofagasta": "https://www.puntoticket.com/ciudad/antofagasta",
        "Iquique":     "https://www.puntoticket.com/ciudad/iquique",
        "Calama":      "https://www.puntoticket.com/ciudad/calama",
    }

    for ciudad, url in ciudades_pt.items():
        r = get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        vistos = set()

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            texto = limpiar(a.get_text(" "))
            if (
                href.startswith("/") and len(href) > 3
                and not any(x in href for x in [
                    "musica", "deportes", "teatro", "familia",
                    "especiales", "todos", "Account", "Cliente", "paginas", "#",
                ])
                and len(texto) > 4 and href not in vistos
            ):
                vistos.add(href)
                base.append({
                    "texto_crudo": texto,
                    "ciudad": ciudad,
                    "url": f"https://www.puntoticket.com{href}",
                })
        time.sleep(PAUSA)

    print(f"  → Obteniendo detalle de {len(base)} eventos...")
    eventos = []
    for i, b in enumerate(base):
        print(f"    [{i+1}/{len(base)}] {b['url'].split('/')[-1][:50]}...")
        og_title, imagen, desc, fecha_iso, fecha_texto, venue = extraer_detalle(b["url"])

        nombre_base = og_title or desc or b["texto_crudo"]
        if not venue:
            venue = detectar_venue(b["texto_crudo"])
        ciudad = b["ciudad"]

        if not fecha_iso:
            fecha_iso, fecha_texto = extraer_fecha_de_texto(b["texto_crudo"])

        nombre = limpiar_nombre(nombre_base, venue=venue, ciudad=ciudad)

        eventos.append({
            "fuente": "PuntoTicket",
            "nombre": nombre,
            "venue": venue,
            "descripcion": desc,
            "fecha_iso": fecha_iso,
            "fecha_texto": fecha_texto,
            "precio_desde_clp": "",
            "ciudad": ciudad,
            "imagen_url": imagen,
            "url": b["url"],
        })
        time.sleep(PAUSA)

    print(f"  ✅ {len(eventos)} eventos")
    return eventos


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Scraper de eventos — Norte de Chile  v4")
    print("=" * 55)

    todos = []
    todos += scrape_ticketplus()
    todos += scrape_ticketpro()
    todos += scrape_puntoticket()

    todos.sort(key=lambda e: e["fecha_iso"] if e["fecha_iso"] else "9999")

    resultado = {
        "generado_en": datetime.now().isoformat(),
        "total_eventos": len(todos),
        "eventos": todos,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    con_imagen = sum(1 for e in todos if e["imagen_url"])
    con_desc   = sum(1 for e in todos if e["descripcion"])
    con_fecha  = sum(1 for e in todos if e["fecha_iso"])
    con_venue  = sum(1 for e in todos if e["venue"])
    print(f"\n{'=' * 55}")
    print(f"  Total       : {len(todos)} eventos")
    print(f"  Con imagen  : {con_imagen}")
    print(f"  Con descripción : {con_desc}")
    print(f"  Con fecha   : {con_fecha}")
    print(f"  Con venue   : {con_venue}")
    print(f"  Archivo     : '{OUTPUT_FILE}'")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
