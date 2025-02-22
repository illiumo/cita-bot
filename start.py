
import asyncio
from playwright.async_api import async_playwright
import httpx
from fake_useragent import UserAgent


async def get_tramites_for_provincia(page, provincia_name):
    """
    Функция получает список процедур (trámites) для указанной провинции.
    """
    await page.goto("https://icp.administracionelectronica.gob.es/icpplus/index.html")
    await page.wait_for_selector("select#form")

    # Ищем провинцию
    provincias = await page.query_selector_all("select#form option")
    for provincia in provincias:
        value = await provincia.get_attribute("value")
        name = await provincia.inner_text()

        if provincia_name.lower() in name.lower():
            await page.select_option("select#form", value=value)
            await page.click("input#btnAceptar")
            await page.wait_for_load_state("domcontentloaded")

            # **Ждем появления списка процедур**
            await page.wait_for_selector("select[name='tramiteGrupo[0]']", timeout=5000)

            tramites = await page.query_selector_all("select[name='tramiteGrupo[0]'] option")
            tramite_list = []
            for tramite in tramites[1:]:  # Пропускаем первый элемент "Despliega..."
                tramite_text = await tramite.inner_text()
                tramite_value = await tramite.get_attribute("value")
                if tramite_value:  # Исключаем некорректные значения
                    tramite_list.append({"nombre": tramite_text, "valor": tramite_value})

            return tramite_list

    return None  # Если провинция не найдена


async def start():
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=headers["User-Agent"])
        page = await context.new_page()

        # Открываем сайт
        await page.goto("https://icp.administracionelectronica.gob.es/icpplus/index.html")
        print("✅ Открыли сайт!")

        # Ждём загрузки списка провинций
        await page.wait_for_selector("select#form")

        provincia_name = "Alicante"  # Здесь можно заменить на переменную от бота
        print(f"🔍 Выбираем провинцию: {provincia_name}")

        # Получаем процедуры для этой провинции
        tramites = await get_tramites_for_provincia(page, provincia_name)

        if not tramites:
            print("❌ Процедуры не найдены для этой провинции!")
            await browser.close()
            return

        print(f"✅ Найдено {len(tramites)} процедур!")
        for t in tramites:
            print(f" - {t['nombre']}")

        # Проверяем, что есть доступные процедуры
        if len(tramites) == 0:
            print("❌ Нет доступных процедур!")
            await browser.close()
            return

        # Выбираем **первую доступную** процедуру (можно передавать из бота)
        tramite_value = tramites[0]['valor']

        # Ждём загрузки селектора перед выбором
        await page.wait_for_selector("select[name='tramiteGrupo[0]']", timeout=5000)

        # Выбираем процедуру **через Playwright**
        await page.select_option("select[name='tramiteGrupo[0]']", value=tramite_value)
        print(f"✅ Выбрали процедуру: {tramites[0]['nombre']}")

        # Проверяем, что процедура действительно выбрана (через JS)
        selected_value = await page.evaluate('''
            document.querySelector("select[name='tramiteGrupo[0]']").value;
        ''')
        print(f"🔎 Проверка выбора: {selected_value}")

        if selected_value != tramite_value:
            print("❌ Ошибка выбора! Пробуем альтернативный метод...")
            await page.evaluate(f'''
                document.querySelector("select[name='tramiteGrupo[0]']").value = "{tramite_value}";
            ''')
            await page.evaluate('''
                document.querySelector("select[name='tramiteGrupo[0]']").dispatchEvent(new Event('change', { bubbles: true }));
            ''')

        # Ждём перед нажатием "Aceptar"
        await asyncio.sleep(4)

        # Убеждаемся, что кнопка доступна перед кликом
        await page.wait_for_selector("input#btnAceptar", timeout=5000)
        await page.click("input#btnAceptar")
        print("✅ Нажали 'Aceptar'!")

        # Ждём загрузки следующей страницы
        await page.wait_for_load_state("domcontentloaded")
        print("✅ Перешли на следующую страницу!")

        # Оставляем браузер открытым на 10 сек для проверки
        await asyncio.sleep(30)

        # Закрываем браузер
        await browser.close()


# Запускаем асинхронную функцию
asyncio.run(start())
