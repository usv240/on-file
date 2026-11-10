"""Render the Devpost gallery images from gallery.html: one PNG per section, 1500 x 1000 at 2x.

    python proposal/gallery/render.py
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        page = await browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=2)
        await page.goto((HERE / "gallery.html").as_uri())
        await page.evaluate("document.fonts.ready")
        ok = await page.evaluate("document.fonts.check('800 40px Archivo')")
        if not ok:
            raise SystemExit("Archivo did not load")
        for i, el in enumerate(await page.query_selector_all("section.art:not(.vcard)"), 1):
            out = HERE / f"on-file-gallery-{i}.png"
            await el.screenshot(path=str(out))
            print(out.name, out.stat().st_size // 1024, "KB")
        # the walkthrough video's opening and closing cards
        (HERE / "video").mkdir(exist_ok=True)
        for el in await page.query_selector_all("section.vcard"):
            out = HERE / "video" / f"{await el.get_attribute('id')}.png"
            await el.screenshot(path=str(out))
            print("video/" + out.name)
        await browser.close()


asyncio.run(main())
