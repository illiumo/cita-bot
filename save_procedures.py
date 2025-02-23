import json
import asyncio
import unicodedata
import random
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

# Провинция и процедура, которые будем проверять
PROVINCIA = "Ceuta"
PROCEDURA = "POLICÍA - COMUNICACIÓN DE CAMBIO DE DOMICILIO"


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
]


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


async def human_delay(min_time=1.0, max_time=3.0):
    """Рандомная задержка для эмуляции поведения человека."""
    await asyncio.sleep(random.uniform(min_time, max_time))


async def random_scroll(page):
    """Рандомная прокрутка страницы для имитации живого пользователя."""
    scroll_distance = random.randint(200, 1200)
    await page.mouse.wheel(0, scroll_distance)
    await human_delay(0.5, 1.5)


async def random_mouse_movement(page):
    """Рандомные движения мыши по экрану."""
    width, height = await page.evaluate("() => [window.innerWidth, window.innerHeight]")
    x, y = random.randint(50, width - 50), random.randint(50, height - 50)
    await page.mouse.move(x, y, steps=random.randint(5, 20))
    await human_delay(0.2, 0.5)


def normalize_text(text):
    """Удаляет акценты, лишние пробелы, приводит к нижнему регистру и убирает невидимые символы."""
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return " ".join(text.strip().lower().split())


async def find_available_appointments(provincia, tramite):
    headers = {"User-Agent": random_user_agent(), "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"}

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

        await random_mouse_movement(page)
        await random_scroll(page)

        # Выбираем провинцию
        provincias = await page.query_selector_all("select#form option")
        provincia_value = None
        for option in provincias:
            name = await option.inner_text()
            if normalize_text(name) == normalize_text(provincia):
                provincia_value = await option.get_attribute("value")
                break

        if not provincia_value:
            print(f"❌ Провинция '{provincia}' не найдена.")
            await browser.close()
            return

        await page.select_option("select#form", value=provincia_value)
        await human_delay()
        await page.click("input#btnAceptar")
        await page.wait_for_load_state("domcontentloaded")

        await random_scroll(page)

        # Определяем, в каком списке искать процедуру
        tramite_0_selector = "select[name='tramiteGrupo[0]']"
        tramite_1_selector = "select[name='tramiteGrupo[1]']"

        if tramite.startswith("POLICÍA"):
            tramites_list_selector = tramite_1_selector
        else:
            tramites_list_selector = tramite_0_selector

        await page.wait_for_selector(tramites_list_selector)
        tramites_options = await page.query_selector_all(f"{tramites_list_selector} option")

        tramite_value = None
        for option in tramites_options[1:]:  # Пропускаем первую пустую опцию
            text = normalize_text(await option.inner_text())
            value = await option.get_attribute("value")
            if text == normalize_text(tramite):
                tramite_value = value
                break

        if not tramite_value:
            print(f"❌ Процедура '{tramite}' не найдена в провинции '{provincia}'.")
            await browser.close()
            return

        # Выбираем найденную процедуру
        await page.select_option(tramites_list_selector, value=tramite_value)
        await human_delay(1, 2)
        await page.click("input#btnAceptar")
        await page.wait_for_load_state("domcontentloaded")

        # 🔴 Нажатие кнопки "Entrar" после загрузки новой страницы
        print("⏳ Ожидаем загрузку страницы с кнопкой 'Entrar'...")

        entrar_button = None
        try:
            entrar_button = await page.wait_for_selector("input[value='Entrar']", timeout=10000)
        except:
            print("⚠️ Кнопка 'input[value=Entrar]' не найдена, пробуем другой селектор...")

        if not entrar_button:
            try:
                entrar_button = await page.wait_for_selector("button:text('Entrar')", timeout=5000)
            except:
                print("⚠️ Кнопка 'button:text(Entrar)' тоже не найдена.")

        if entrar_button:
            print("✅ Кнопка 'Entrar' найдена! Нажимаем...")
            await human_delay(0.5, 2.0)
            await entrar_button.click()
            await page.wait_for_load_state("domcontentloaded")
        else:
            print("❌ Кнопка 'Entrar' не найдена.")
            print("🛠️ Отладка: сохраняем HTML страницы в файл...")
            html_content = await page.content()
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("📄 HTML страницы сохранен в debug_page.html. Проверь его вручную!")
            await browser.close()
            return

        print("⏳ Ожидание 30 секунд перед закрытием браузера...")
        await asyncio.sleep(120)
        await browser.close()


# Запуск поиска
asyncio.run(find_available_appointments(PROVINCIA, PROCEDURA))
