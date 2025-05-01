import requests
from bs4 import BeautifulSoup
import urllib.parse

class TPBEngine:
    name = "The Pirate Bay"
    BASE_URL = "https://apibay.org"
    HEADERS = {'User-Agent': 'Mozilla/5.0'}

    @classmethod
    def search(cls, query, page=1):
        try:
            url = f"{cls.BASE_URL}/q.php?q={urllib.parse.quote_plus(query)}&cat=0"
            response = requests.get(url, headers=cls.HEADERS)
            response.raise_for_status()
            data = response.json()
            return cls.parse_results(data)
        except Exception as e:
            print(f"TPB search error: {e}")
            return []

    @classmethod
    def parse_results(cls, data):
        torrents = []
        for item in data:
            try:
                if item['name'] == 'No results returned':
                    continue
                    
                name = item['name']
                size_gb = int(item['size']) / (1024**3)
                torrents.append({
                    'name': name,
                    'url': f"https://thepiratebay.org/description.php?id={item['id']}",
                    'seeds': item['seeders'],
                    'leeches': item['leechers'],
                    'size': f"{size_gb:.2f} GB",
                    'date': cls.format_date(item['added']),
                    'engine': cls.name,
                    'magnet': f"magnet:?xt=urn:btih:{item['info_hash']}&dn={urllib.parse.quote(name)}"
                })
            except Exception as e:
                print(f"TPB parse error: {e}")
                continue
        return torrents

    @classmethod
    def format_date(cls, timestamp):
        try:
            from datetime import datetime
            return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
        except:
            return timestamp

    @classmethod
    def get_magnet(cls, url):
        # TPB provides magnet directly in search results
        return None