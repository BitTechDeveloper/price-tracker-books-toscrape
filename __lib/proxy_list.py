import requests
from bs4 import BeautifulSoup


def proxy_list_from_free_proxy(https_only=True, elite_only=True):
    """
    Fetches a list of high-quality free proxies from https://free-proxy-list.net/ via scraping.
    Returns a list of full proxy URLs in 'http://ip:port' format suitable for ProxyConfiguration.
    """
    url = "https://free-proxy-list.net/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table table-striped table-bordered")
    if not table:
        raise ValueError("Proxy table not found. Site structure may have changed.")
    proxies = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 8:
            continue
        ip = cols[0].text.strip()
        port = cols[1].text.strip()
        https = cols[6].text.strip().lower() == "yes"
        anonymity = cols[4].text.strip().lower()
        if https_only and not https:
            continue
        if elite_only and anonymity != "elite proxy":
            continue
        proxies.append(f"http://{ip}:{port}")  # Prepend http://
    return proxies


def proxy_list_from_free_proxy_anonymous(https_only=True):
    """
    Fetches a list of anonymous (not elite, not transparent) free proxies from https://free-proxy-list.net/ via scraping.
    Returns a list of full proxy URLs in 'http://ip:port' format suitable for ProxyConfiguration.
    Filters for:
    - HTTPS support (if https_only=True)
    - Anonymity level exactly 'anonymous proxy' (excludes 'elite proxy' and 'transparent proxy')
    """
    url = "https://free-proxy-list.net/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table table-striped table-bordered")
    if not table:
        raise ValueError("Proxy table not found. Site structure may have changed.")
    proxies = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 8:
            continue
        ip = cols[0].text.strip()
        port = cols[1].text.strip()
        https = cols[6].text.strip().lower() == "yes"
        anonymity = cols[4].text.strip().lower()
        if https_only and not https:
            continue
        if anonymity != "anonymous":
            continue
        proxies.append(f"http://{ip}:{port}")
    return proxies


def proxy_list_from_proxyscrape(limit=None):
    """
    Fetches highest quality free proxies from ProxyScrape API.
    Returns a list of full proxy URLs in 'http://ip:port' format suitable for ProxyConfiguration.
    """
    base_url = "https://api.proxyscrape.com/v2/"
    params = {
        "request": "displayproxies",
        "protocol": "http",  # http includes HTTPS-capable proxies
        "timeout": "5000",
        "country": "all",
        "ssl": "all",
        "anonymity": "elite,anonymous",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    response = requests.get(base_url, params=params, headers=headers)
    response.raise_for_status()
    if not response.text.strip():
        return []
    proxies = [
        f"http://{line.strip()}" for line in response.text.splitlines() if line.strip()
    ]
    if limit:
        proxies = proxies[:limit]
    return proxies
