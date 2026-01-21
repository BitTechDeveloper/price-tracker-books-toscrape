import json
import os

import pandas as pd
from apify import Actor
from crawlee.crawlers import BeautifulSoupCrawler
from crawlee.http_clients import CurlImpersonateHttpClient
from crawlee.proxy_configuration import ProxyConfiguration
from crawlee.storages import Dataset
from dotenv import load_dotenv

from lib.db_export import export_to_mysql, export_to_postgresql, export_to_sqlite
from lib.proxy_list import (
    proxy_list_from_free_proxy,
    proxy_list_from_free_proxy_anonymous,
    proxy_list_from_proxyscrape,
)

from .routes import router

load_dotenv()


async def main() -> None:
    """The crawler entry point."""
    async with Actor:
        actor_input = await Actor.get_input() or {}

        errors = {}
        tiered_proxy_urls = [[None]]
        proxy_configuration = None

        # Try Apify Proxy
        try:
            proxy_configuration = await Actor.create_proxy_configuration(
                actor_proxy_input=actor_input.get("proxySettings")
            )
        except Exception as e:
            errors["Apify Proxy"] = str(e)

        # Build free proxy tiers
        proxies_funcs = (
            proxy_list_from_free_proxy,
            proxy_list_from_free_proxy_anonymous,
            proxy_list_from_proxyscrape,
        )

        for proxy_func in proxies_funcs:
            try:
                tier = proxy_func()
                if tier:
                    tiered_proxy_urls.append(tier)
            except Exception as e:
                errors[getattr(proxy_func, "__name__", str(proxy_func))] = str(e)

        # Fallback to free tiers
        if proxy_configuration is None and tiered_proxy_urls:
            proxy_configuration = ProxyConfiguration(
                tiered_proxy_urls=tiered_proxy_urls
            )
            Actor.log.info(f"Using {len(tiered_proxy_urls)} free proxy tiers")

        if proxy_configuration is None:
            Actor.log.warning(
                "No proxies configured. Crawl may get blocked by the target site."
            )

        crawler = BeautifulSoupCrawler(
            request_handler=router,
            max_requests_per_crawl=10,
            http_client=CurlImpersonateHttpClient(),
            proxy_configuration=proxy_configuration,
            use_session_pool=True,
            max_request_retries=10,
        )

        if errors:
            for name, err in errors.items():
                crawler.log.info(f"Proxy source {name} failed: {err}")

        await crawler.run(["https://books.toscrape.com"])

        # File exports

        if not Actor.is_at_home():
            await crawler.export_data(path="data/result.csv")
            await crawler.export_data(path="data/result.json", indent=4)

            dataset = await Dataset.open()
            data = await dataset.get_data()

            # Manual JSONL
            with open("data/result.jsonl", "w", encoding="utf-8") as f:
                for item in data.items:
                    json.dump(item, f, ensure_ascii=False)
                    f.write("\n")

            if data.items:
                df = pd.DataFrame(data.items)
                if not df.empty:
                    df.to_excel("data/result.xlsx", index=False)

                # Database exports via separate functions
                await export_to_sqlite(data.items)

                mysql_config = actor_input.get("mysql") or {
                    "host": "localhost",
                    "port": int(os.getenv("MYSQL_PORT", 3306)),
                    "user": os.getenv("MYSQL_USER", "testuser"),
                    "password": os.getenv("MYSQL_PASSWORD", ""),
                    "database": os.getenv("MYSQL_DATABASE", "testdb"),
                    "table": "books",
                }
                await export_to_mysql(data.items, mysql_config)

                postgres_config = actor_input.get("postgres") or {
                    "host": "localhost",
                    "port": int(os.getenv("POSTGRES_PORT", 5432)),
                    "user": os.getenv("POSTGRES_USER", "testuser"),
                    "password": os.getenv("POSTGRES_PASSWORD", ""),
                    "database": os.getenv("POSTGRES_DB", "testdb"),
                    "table": "books",
                }
                await export_to_postgresql(data.items, postgres_config)
