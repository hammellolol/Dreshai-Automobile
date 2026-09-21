import os
import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

MOBILE_URL = "https://home.mobile.de/DRESHAJAUTOMOBILE"

def download_image(img_url, filename):
    try:
        if not os.path.exists("img"):
            os.makedirs("img")
        if img_url.startswith("//"):
            img_url = "https:" + img_url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(img_url, headers=headers, timeout=10)
        if res.status_code == 200:
            filepath = os.path.join("img", filename)
            with open(filepath, "wb") as f:
                f.write(res.content)
            return filepath
    except Exception as e:
        print(f"Bildfehler: {e}")
    return None

def fetch_vehicles():
    vehicles = []
    with sync_playwright() as p:
        # Startet unsichtbaren Chrome-Browser mit echtem User-Agent
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Lade mobile.de...")
            page.goto(MOBILE_URL, wait_until="networkidle", timeout=30000)
            
            # Scrollen, um Lazy-Loading der Bilder auszulösen
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(2000)

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Sucht Inserate-Container
            entries = soup.find_all(['div', 'article'], class_=re.compile('.*seller-inventory-entry.*|.*g-row.*|.*listing.*'))

            for idx, item in enumerate(entries):
                title_elem = item.find(['span', 'h3', 'h2'], class_=re.compile('.*headline.*|.*title.*'))
                price_elem = item.find(['span', 'div'], class_=re.compile('.*price.*'))
                img_elem = item.find('img')

                if title_elem and price_elem:
                    title = title_elem.text.strip()
                    price = price_elem.text.strip()

                    img_src = None
                    if img_elem:
                        img_src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')

                    local_img = None
                    if img_src and not img_src.startswith("data:"):
                        local_img = download_image(img_src, f"auto_{idx + 1}.jpg")

                    vehicles.append({
                        'title': title,
                        'price': price,
                        'img': local_img if local_img else 'img/placeholder.jpg',
                        'ez': 'Auf Anfrage',
                        'km': 'Auf Anfrage',
                        'fuel': 'Benzin / Diesel'
                    })

        except Exception as e:
            print(f"Fehler beim Laden der Seite: {e}")
        finally:
            browser.close()

    return vehicles

def generate_static_html(vehicles):
    if not vehicles:
        return """
        <div class="info-box">
            <p><strong>Aktueller Fahrzeugbestand:</strong> Kontaktaufnahme direkt per Telefon.</p>
            <p><strong>Telefon:</strong> <a href="tel:01717729532">0171 7729532</a></p>
        </div>
        """

    html = ""
    for car in vehicles:
        html += f"""
        <div class="car-card">
            <img src="{car['img']}" alt="{car['title']}" onerror="this.src='https://via.placeholder.com/400x250?text=Foto+wird+geladen'">
            <div class="car-details">
                <h3>{car['title']}</h3>
                <div class="car-price">{car['price']}</div>
                <ul class="car-specs">
                    <li><strong>Erstzulassung:</strong> {car['ez']}</li>
                    <li><strong>Kilometerstand:</strong> {car['km']}</li>
                    <li><strong>Kraftstoff:</strong> {car['fuel']}</li>
                </ul>
                <a href="tel:01717729532" class="btn">Jetzt anfragen</a>
            </div>
        </div>
        """
    return html

def update_index_file():
    vehicles = fetch_vehicles()
    new_html = generate_static_html(vehicles)

    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()

        start_marker = "<!-- CARS_START -->"
        end_marker = "<!-- CARS_END -->"

        pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
        updated_content = pattern.sub(f"{start_marker}\n{new_html}\n{end_marker}", content)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"{len(vehicles)} Fahrzeuge erfolgreich eingelesen und index.html aktualisiert!")
    except Exception as e:
        print(f"Fehler beim Schreiben der index.html: {e}")

if __name__ == "__main__":
    update_index_file()
