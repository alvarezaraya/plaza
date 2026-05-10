"""
scraper_eventos.py  v3
======================
Extrae eventos culturales con imagen y descripción desde:
  - Ticketplus.cl  (Región de Antofagasta)
  - Ticketpro.cl   (filtrando ciudades del norte)
  - PuntoTicket.com (filtrando ciudades del norte)

Por cada evento visita su página individual y extrae:
  - imagen_url   → meta og:image
  - descripcion  → meta og:description
  - fecha_iso    → fecha en formato YYYY-MM-DD (para ordenar en Swift)
  - fecha_texto  → fecha legible en español

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

OUTPUT_FILE = "eventos.json"
PAUSA = 0.8   # segundos entre requests

# Meses en español → número
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
    """
    Convierte día + nombre de mes en:
      fecha_iso  → "2026-05-23"
      fecha_texto → "23 de mayo de 2026"
    Devuelve ("", "") si no puede parsear.
    """
    mes_str = mes_str.lower().strip()
    mes_num = MESES_ES.get(mes_str)
    if not mes_num:
        return "", ""

    anio = datetime.now().year
    # Si el mes ya pasó este año, probablemente es el año siguiente
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


def extraer_detalle(url):
    """
    Visita la página del evento y extrae:
      - imagen_url
      - descripcion
      - fecha_iso y fecha_texto (si la descripción contiene fecha más precisa)
    """
    r = get(url)
    if not r:
        return "", "", "", ""

    soup = BeautifulSoup(r.text, "html.parser")

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

    # Intentar extraer fecha desde la descripción (más precisa que el listado)
    # Formato típico Ticketplus: "Sábado 23 MAY - 20:00 hrs"
    fecha_iso, fecha_texto = "", ""
    patron = re.search(
        r"(\d{1,2})\s+(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC"
        r"|enero|febrero|marzo|abril|mayo|junio|julio|agosto"
        r"|septiembre|octubre|noviembre|diciembre)",
        descripcion, re.IGNORECASE
    )
    if patron:
        fecha_iso, fecha_texto = parsear_fecha(patron.group(1), patron.group(2))

    return imagen, descripcion, fecha_iso, fecha_texto


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

        # Nombre: texto antes del recinto (segunda aparición del nombre)
        partes = texto.split("  ")
        nombre = limpiar(partes[0]) if partes else texto[:80]

        evento_url = f"https://ticketplus.cl{href}" if href.startswith("/") else href
        base.append({"nombre": nombre, "precio": precio, "url": evento_url})

    print(f"  → Obteniendo detalle de {len(base)} eventos...")
    eventos = []
    for i, b in enumerate(base):
        print(f"    [{i+1}/{len(base)}] {b['nombre'][:50]}...")
        imagen, desc, fecha_iso, fecha_texto = extraer_detalle(b["url"])
        eventos.append({
            "fuente": "Ticketplus",
            "nombre": b["nombre"],
            "descripcion": desc,
            "fecha_iso": fecha_iso,
            "fecha_texto": fecha_texto,
            "precio_desde_clp": b["precio"],
            "ciudad": "Antofagasta",
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

        ciudad_det = next(
            (c.capitalize() for c in CIUDADES_OBJETIVO if c in texto.lower()), ""
        )

        slug = href.rstrip("/").split("/")[-1]
        nombre = slug.replace("-", " ").split("--")[0].title()
        evento_url = f"https://www.ticketpro.cl{href}" if href.startswith("/") else href
        base.append({"nombre": nombre, "precio": precio, "ciudad": ciudad_det, "url": evento_url})

    print(f"  → Obteniendo detalle de {len(base)} eventos...")
    eventos = []
    for i, b in enumerate(base):
        print(f"    [{i+1}/{len(base)}] {b['nombre'][:50]}...")
        imagen, desc, fecha_iso, fecha_texto = extraer_detalle(b["url"])
        eventos.append({
            "fuente": "Ticketpro",
            "nombre": b["nombre"],
            "descripcion": desc,
            "fecha_iso": fecha_iso,
            "fecha_texto": fecha_texto,
            "precio_desde_clp": b["precio"],
            "ciudad": b["ciudad"],
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
                    "nombre": texto,
                    "ciudad": ciudad,
                    "url": f"https://www.puntoticket.com{href}",
                })
        time.sleep(PAUSA)

    print(f"  → Obteniendo detalle de {len(base)} eventos...")
    eventos = []
    for i, b in enumerate(base):
        print(f"    [{i+1}/{len(base)}] {b['nombre'][:50]}...")
        imagen, desc, fecha_iso, fecha_texto = extraer_detalle(b["url"])
        eventos.append({
            "fuente": "PuntoTicket",
            "nombre": b["nombre"],
            "descripcion": desc,
            "fecha_iso": fecha_iso,
            "fecha_texto": fecha_texto,
            "precio_desde_clp": "",
            "ciudad": b["ciudad"],
            "imagen_url": imagen,
            "url": b["url"],
        })
        time.sleep(PAUSA)

    print(f"  ✅ {len(eventos)} eventos")
    return eventos


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Scraper de eventos — Norte de Chile  v3")
    print("=" * 55)

    todos = []
    todos += scrape_ticketplus()
    todos += scrape_ticketpro()
    todos += scrape_puntoticket()

    # Ordenar por fecha (eventos sin fecha van al final)
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
    print(f"\n{'=' * 55}")
    print(f"  Total    : {len(todos)} eventos")
    print(f"  Con imagen : {con_imagen}")
    print(f"  Con descripción : {con_desc}")
    print(f"  Con fecha : {con_fecha}")
    print(f"  Archivo  : '{OUTPUT_FILE}'")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
