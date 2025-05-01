import requests
from urllib.parse import quote, urlparse, parse_qs
import time
from typing import List, Dict

class YTSEngine:
    name = "YTS Movies"
    BASE_URL = "https://yts.mx/api/v2"
    TORRENT_BASE = "https://yts.mx/torrent/download"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    @classmethod
    def search(cls, query: str, page: int = 1, retries: int = 3) -> List[Dict]:
        """Search YTS (YIFY) torrents with retry logic"""
        results = []
        attempts = 0
        
        while attempts < retries:
            try:
                url = f"{cls.BASE_URL}/list_movies.json?query_term={quote(query)}&page={page}"
                response = requests.get(url, headers=cls.HEADERS, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                if data.get('status') != 'ok':
                    raise ValueError("API returned non-OK status")
                
                movies = data.get('data', {}).get('movies', [])
                if not movies:
                    return results
                
                for movie in movies:
                    if not movie.get('torrents'):
                        continue
                        
                    for torrent in movie['torrents']:
                        # Get the actual magnet link from the torrent URL
                        magnet = cls._extract_magnet(torrent['url'])
                        if not magnet:
                            continue
                            
                        results.append({
                            'name': f"{movie['title']} ({movie['year']}) [{torrent['quality']}]",
                            'url': f"https://yts.mx/movie/{movie['slug']}",
                            'seeds': torrent['seeds'],
                            'leeches': torrent['peers'],
                            'size': torrent['size'],
                            'date': torrent['date_uploaded'],
                            'engine': cls.name,
                            'magnet': magnet
                        })
                return results
                
            except requests.exceptions.RequestException as e:
                attempts += 1
                if attempts < retries:
                    time.sleep(1)
                continue
            except Exception as e:
                print(f"YTS parse error: {str(e)[:100]}")
                return results
        
        return results

    @classmethod
    def _extract_magnet(cls, torrent_url: str) -> str:
        """Extract magnet link from YTS torrent URL"""
        try:
            # Example URL: https://yts.mx/torrent/download/HASH123456789
            hash = urlparse(torrent_url).path.split('/')[-1]
            if not hash or len(hash) < 10:
                return ""
                
            # Construct magnet link
            return f"magnet:?xt=urn:btih:{hash}&dn={quote('YTS Movie')}&tr=udp://tracker.opentrackr.org:1337/announce"
        except Exception:
            return ""

    @classmethod
    def get_magnet(cls, url):
        """YTS provides magnet directly in search results"""
        return None  # Already handled in search()