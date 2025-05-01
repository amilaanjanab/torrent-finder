import requests
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urljoin

class X1337Engine:
    name = "1337x"
    BASE_URL = "https://www.1337x.to"
    HEADERS = {'User-Agent': 'Mozilla/5.0'}

    @classmethod
    def search(cls, query, page=1):
        try:
            url = f"{cls.BASE_URL}/search/{urllib.parse.quote_plus(query)}/{page}/"
            response = requests.get(url, headers=cls.HEADERS)
            response.raise_for_status()
            return cls.parse_results(response.text)
        except Exception:
            return []

    @classmethod
    def parse_results(cls, html):
        soup = BeautifulSoup(html, 'html.parser')
        torrents = []
        
        for row in soup.select('table.table-list tbody tr'):
            try:
                name = row.select_one('td.coll-1 a:nth-of-type(2)').text.strip()
                url = urljoin(cls.BASE_URL, row.select_one('td.coll-1 a:nth-of-type(2)')['href'])
                seeds = row.select_one('td.coll-2').text.strip()
                leeches = row.select_one('td.coll-3').text.strip()
                size = row.select_one('td.coll-4').text.strip().split()[0]
                date = row.select_one('td.coll-date').text.strip()
                
                torrents.append({
                    'name': name,
                    'url': url,
                    'seeds': seeds,
                    'leeches': leeches,
                    'size': size,
                    'date': date,
                    'engine': cls.name
                })
            except Exception:
                continue
        return torrents

    @classmethod
    def get_magnet(cls, url):
        try:
            response = requests.get(url, headers=cls.HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.find('a', href=lambda href: href and href.startswith('magnet:'))['href']
        except Exception:
            return None