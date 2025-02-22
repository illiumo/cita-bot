import asyncio
import json
from playwright.async_api import async_playwright
import asyncio
from playwright.async_api import async_playwright
import httpx
from fake_useragent import UserAgent


async def get_provincias_y_tramites():
    result = {}
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=headers["User-Agent"])
        page = await context.new_page()

        response = await page.goto("https://icp.administracionelectronica.gob.es/icpplus/index.html",
                        wait_until="domcontentloaded")
        if response and response.status == 429:
            print("❌ Получили 429 Too Many Requests. Останавливаем работу.")
            await browser.close()
            return

        await page.wait_for_selector("select#form")

        # Получаем список провинций
        provincias = await page.query_selector_all("select#form option")

        for provincia in provincias:
            value = await provincia.get_attribute("value")
            name = await provincia.inner_text()

            if "Selecciona" in name:  # Пропускаем пустое значение
                continue

            print(f"🔍 Проверяем {name}...")

            # Выбираем провинцию
            await page.select_option("select#form", value=value)
            await page.click("input#btnAceptar")
            await page.wait_for_load_state("domcontentloaded")


            #Получаем адресса отделений в провинции
            await page.wait_for_selector("select[name='side']")
            address = await page.query_selector_all("select[name='side'] option")

            # Получаем список доступных процедур
            await page.wait_for_selector("select[name='tramiteGrupo[0]']")
            tramites = await page.query_selector_all("select[name='tramiteGrupo[0]'] option")

            tramite_list = []
            for tramite in tramites:
                tramite_text = await tramite.inner_text()
                tramite_value = await tramite.get_attribute("value")
                tramite_list.append({"nombre": tramite_text, "valor": tramite_value})

            result[name] = tramite_list

            # Возвращаемся назад
            await page.go_back()
            await page.wait_for_selector("select#form")

        await browser.close()

    # Сохраняем данные в JSON
    with open("provincias_tramites.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print("✅ Данные сохранены!")


# Запускаем парсер
asyncio.run(get_provincias_y_tramites())