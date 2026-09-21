import requests
from bs4 import BeautifulSoup
import re

# Offizielle mobile.de-Händlerseite von Dreshaj Automobile
MOBILE_URL = "https://home.mobile.de/DRESHAJAUTOMOBILE"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def fetch_vehicles():
    try:
        response = requests.get(MOBILE_URL, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print("Fehler beim Abrufen der mobile.de Seite")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        vehicles = []

        # Parst die Fahrzeuge aus dem öffentlichen Händlerprofil
        for item in soup.find_all('div', class_=re.compile('.*seller-inventory-entry.*|.*g-row.*')):
            title_elem = item.find('span', class_=re.compile('.*headline.*|.*h3.*'))
            price_elem = item.find('span', class_=re.compile('.*price.*'))
            img_elem = item.find('img')

            if title_elem and price_elem:
                title = title_elem.text.strip()
                price = price_elem.text.strip()
                img_src = img_elem['src'] if img_elem and 'src' in img_elem.attrs else 'img/placeholder.jpg'
                
                vehicles.append({
                    'title': title,
                    'price': price,
                    'img': img_src,
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
        # Fallback falls mobile.de gerade blockiert oder keine Autos online sind
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
            <img src="{car['img']}" alt="{car['title']}" onerror="this.src='https://via.placeholder.com/400x250?text=Echtes+Foto+einfuegen'">
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
        print("index.html erfolgreich mit aktuellen Fahrzeugdaten überschrieben!")
    except Exception as e:
        print(f"Fehler beim Aktualisieren der Datei: {e}")

if __name__ == "__main__":
    update_index_file()
