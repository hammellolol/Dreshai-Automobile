import os
import re
import requests
from bs4 import BeautifulSoup

MOBILE_URL = "https://home.mobile.de/DRESHAJAUTOMOBILE"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def download_image(img_url, filename):
    """Lädt das Bild herunter und speichert es im img/-Ordner."""
    try:
        if not os.path.exists("img"):
            os.makedirs("img")
            
        # Falls die URL protokollrelativ ist (z.B. //i.ebayimg.com/...)
        if img_url.startswith("//"):
            img_url = "https:" + img_url

        res = requests.get(img_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            filepath = os.path.join("img", filename)
            with open(filepath, "wb") as f:
                f.write(res.content)
            return filepath
    except Exception as e:
        print(f"Fehler beim Bild-Download ({img_url}): {e}")
    return None

def fetch_vehicles():
    try:
        response = requests.get(MOBILE_URL, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print("Fehler beim Abrufen der mobile.de Seite")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        vehicles = []

        entries = soup.find_all('div', class_=re.compile('.*seller-inventory-entry.*|.*g-row.*'))
        
        for idx, item in enumerate(entries):
            title_elem = item.find('span', class_=re.compile('.*headline.*|.*h3.*'))
            price_elem = item.find('span', class_=re.compile('.*price.*'))
            img_elem = item.find('img')

            if title_elem and price_elem:
                title = title_elem.text.strip()
                price = price_elem.text.strip()
                
                # Realen Bild-Pfad finden (mobile.de nutzt meist data-src)
                img_src = None
                if img_elem:
                    img_src = img_elem.get('data-src') or img_elem.get('data-lazy-src') or img_elem.get('src')

                local_img_path = None
                if img_src:
                    clean_name = f"auto_{idx + 1}.jpg"
                    local_img_path = download_image(img_src, clean_name)

                vehicles.append({
                    'title': title,
                    'price': price,
                    'img': local_img_path if local_img_path else 'https://via.placeholder.com/400x250?text=Kein+Foto',
                    'ez': 'Auf Anfrage',
                    'km': 'Auf Anfrage',
                    'fuel': 'Benzin / Diesel'
                })
        return vehicles
    except Exception as e:
        print(f"Fehler beim Scraping: {e}")
        return []

def generate_static_html(vehicles):
    if not vehicles:
        return """
        <div class="info-box">
            <p><strong>Aktueller Fahrzeugbestand:</strong> Rufen Sie uns direkt an, um unsere neusten Fahrzeuge zu erfragen.</p>
            <p><strong>Telefon:</strong> <a href="tel:01717729532">0171 7729532</a></p>
        </div>
        """

    html = ""
    for car in vehicles:
        html += f"""
        <div class="car-card">
            <img src="{car['img']}" alt="{car['title']}" onerror="this.src='https://via.placeholder.com/400x250?text=Foto+nicht+verfuegbar'">
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
        print("index.html und Bilder erfolgreich aktualisiert!")
    except Exception as e:
        print(f"Fehler beim Aktualisieren der Datei: {e}")

if __name__ == "__main__":
    update_index_file()
