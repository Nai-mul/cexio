import os
import glob
import asyncio
import argparse
from itertools import cycle

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions
from bot.utils.version_updater import parser as ps

start_text = """


███████╗██╗███████╗     ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
██╔════╝██║╚══███╔╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
███████╗██║  ███╔╝     ██║     ██║   ██║██║  ██║█████╗  ██████╔╝
╚════██║██║ ███╔╝      ██║     ██║   ██║██╔══╝  ██╔══██╗
███████║██║███████╗    ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
╚══════╝╚═╝╚══════╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝

CEX.IO BOT V 2.3
Prepared and Developed by: F.Davoodi                                                                                                    
"""

global tg_clients


def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]
    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []
    return proxies


async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        return None  # No sessions found

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients


async def auto_update_version():
    while True:
        await asyncio.sleep(3600)
        ps.get_app_version()


async def process() -> None:
    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")
    ps.get_app_version()

    tg_clients = await get_tg_clients()

    if tg_clients is None:
        # No sessions, prompt to create a session
        print(start_text)
        print("No sessions found. Please create a session first.")
        await register_sessions()
    else:
        # Sessions found, automatically run clicker
        print("Sessions found. Starting clicker...")
        await run_tasks(tg_clients=tg_clients)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    with open("x-appl-version.txt", "r") as f:
        version = f.read()
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
                app_version=str(version),
            )
        )
        for tg_client in tg_clients
    ]
    tasks.append(asyncio.create_task(auto_update_version()))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(process())
