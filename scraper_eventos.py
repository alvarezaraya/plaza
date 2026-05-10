"""
scraper_eventos.py
==================
Extrae eventos culturales con imágenes desde tres fuentes chilenas:
  - Ticketplus.cl  (Región de Antofagasta)
  - Ticketpro.cl   (filtrando ciudades del norte)
  - PuntoTicket.com (filtrando ciudades del norte)

Estrategia de imágenes:
  Cada sitio expone la imagen del evento en el meta tag og:image
  de la página individual del evento. El scraper primero obtiene
  la lista de eventos y luego visita cada uno para extraer la imagen.

Requisitos:
    pip install requests beautifulsoup4

Uso:
    python scraper_eventos.py

Salida:
    eventos.json
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

# Pausa entre requests para no sobrecargar los servidores (en segundos)
PAUSA = 0.8


# ── Utilidades ───────────────────────────────────────────────────────────────

def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        print(f"  ⚠️  Error: {url} → {e}")
        return None


def limpiar(texto):
    return re.sub(r"\s+", " ", texto).strip()


def es_ciudad_objetivo(texto):
    texto = texto.lower()
    return any(c in texto for c in CIUDADES_OBJETIVO)


def extraer_og_image(url):
    """
    Visita la página del evento y extrae la URL de imagen
    desde el meta tag og:image. Devuelve string vacío si no encuentra.
    """
    r = get(url)
    if not r:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")

    # Buscar <meta property="og:image" content="...">
    tag = soup.find("meta", property="og:image")
    if tag and tag.get("content"):
        return tag["content"].strip()

    # Alternativa: twitter:image
    tag = soup.find("meta", attrs={"name": "twitter:image"})
    if tag and tag.get("content"):
        return tag["content"].strip()

    return ""


# ── Scraper 1: Ticketplus ────────────────────────────────────────────────────

def scrape_ticketplus():
    print("\n🔍 Ticketplus.cl ...")
    url = "https://ticketplus.cl/states/region-de-antofagasta"
    r = get(url)
    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    eventos = []

    for a in soup.find_all("a", href=re.compile(r"/events/")):
        texto = limpiar(a.get_text(" "))
        href = a.get("href", "")
        if not texto or len(texto) < 5:
            continue

        fecha_match = re.search(
            r"\b(\d{1,2})\s*(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\b",
            texto, re.IGNORECASE,
        )
        fecha = (
            f"{fecha_match.group(1)} {fecha_match.group(2).upper()}"
            if fecha_match else ""
        )

        precio_match = re.search(r"CLP\s*([\d\.]+)", texto)
        precio = precio_match.group(1) if precio_match else ""

        nombre = texto.split(fecha)[0].strip() if fecha else texto[:80]
        evento_url = f"https://ticketplus.cl{href}" if href.startswith("/") else href

        eventos.append({
            "fuente": "Ticketplus",
            "nombre": limpiar(nombre),
            "fecha": fecha,
            "precio_desde_clp": precio,
            "url": evento_url,
            "ciudad": "Antofagasta/Región",
            "imagen_url": "",
        })

    print(f"  → Extrayendo imágenes de {len(eventos)} eventos...")
    for i, evento in enumerate(eventos):
        print(f"    [{i+1}/{len(eventos)}] {evento['nombre'][:45]}...")
        evento["imagen_url"] = extraer_og_image(evento["url"])
        time.sleep(PAUSA)

    print(f"  ✅ {len(eventos)} eventos con imagen")
    return eventos


# ── Scraper 2: Ticketpro ─────────────────────────────────────────────────────

def scrape_ticketpro():
    print("\n🔍 Ticketpro.cl ...")
    url = "https://www.ticketpro.cl/"
    r = get(url)
    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    eventos = []

    for a in soup.find_all("a", href=re.compile(r"/evento/")):
        texto = limpiar(a.get_text(" "))
        href = a.get("href", "")
        if not texto or len(texto) < 5:
            continue
        if not es_ciudad_objetivo(texto):
            continue

        fecha_match = re.search(
            r"\b(\d{1,2})\s*(enero|febrero|marzo|abril|mayo|junio|julio|"
            r"agosto|septiembre|octubre|noviembre|diciembre)\b",
            texto, re.IGNORECASE,
        )
        fecha = (
            f"{fecha_match.group(1)} {fecha_match.group(2).capitalize()}"
            if fecha_match else ""
        )

        precio_match = re.search(r"\$\s*([\d\.]+)", texto)
        precio = precio_match.group(1) if precio_match else ""

        ciudad_det = next(
            (c.capitalize() for c in CIUDADES_OBJETIVO if c in texto.lower()), ""
        )

        slug = href.rstrip("/").split("/")[-1]
        nombre_url = slug.replace("-", " ").split("--")[0].title()
        evento_url = f"https://www.ticketpro.cl{href}" if href.startswith("/") else href

        eventos.append({
            "fuente": "Ticketpro",
            "nombre": nombre_url,
            "fecha": fecha,
            "precio_desde_clp": precio,
            "url": evento_url,
            "ciudad": ciudad_det,
            "imagen_url": "",
        })

    print(f"  → Extrayendo imágenes de {len(eventos)} eventos...")
    for i, evento in enumerate(eventos):
        print(f"    [{i+1}/{len(eventos)}] {evento['nombre'][:45]}...")
        evento["imagen_url"] = extraer_og_image(evento["url"])
        time.sleep(PAUSA)

    print(f"  ✅ {len(eventos)} eventos con imagen")
    return eventos


# ── Scraper 3: PuntoTicket ───────────────────────────────────────────────────

def scrape_puntoticket():
    print("\n🔍 PuntoTicket.com ...")
    eventos = []

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
                href.startswith("/")
                and len(href) > 3
                and not any(x in href for x in [
                    "musica", "deportes", "teatro", "familia",
                    "especiales", "todos", "Account", "Cliente",
                    "paginas", "#",
                ])
                and len(texto) > 4
                and href not in vistos
            ):
                vistos.add(href)
                evento_url = f"https://www.puntoticket.com{href}"

                fecha_match = re.search(
                    r"\b(\d{1,2})\s+de\s+"
                    r"(enero|febrero|marzo|abril|mayo|junio|julio|"
                    r"agosto|septiembre|octubre|noviembre|diciembre)",
                    texto, re.IGNORECASE,
                )
                fecha = (
                    f"{fecha_match.group(1)} de {fecha_match.group(2).capitalize()}"
                    if fecha_match else ""
                )

                eventos.append({
                    "fuente": "PuntoTicket",
                    "nombre": limpiar(texto),
                    "fecha": fecha,
                    "precio_desde_clp": "",
                    "url": evento_url,
                    "ciudad": ciudad,
                    "imagen_url": "",
                })

        time.sleep(PAUSA)

    print(f"  → Extrayendo imágenes de {len(eventos)} eventos...")
    for i, evento in enumerate(eventos):
        print(f"    [{i+1}/{len(eventos)}] {evento['nombre'][:45]}...")
        evento["imagen_url"] = extraer_og_image(evento["url"])
        time.sleep(PAUSA)

    print(f"  ✅ {len(eventos)} eventos con imagen")
    return eventos


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Scraper de eventos culturales — Norte de Chile")
    print("  (con imágenes)")
    print("=" * 55)

    todos = []
    todos += scrape_ticketplus()
    todos += scrape_ticketpro()
    todos += scrape_puntoticket()

    resultado = {
        "generado_en": datetime.now().isoformat(),
        "total_eventos": len(todos),
        "fuentes": ["Ticketplus", "Ticketpro", "PuntoTicket"],
        "eventos": todos,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    con_imagen = sum(1 for e in todos if e["imagen_url"])
    print(f"\n{'=' * 55}")
    print(f"  Total eventos : {len(todos)}")
    print(f"  Con imagen    : {con_imagen}")
    print(f"  Guardado en   : '{OUTPUT_FILE}'")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
