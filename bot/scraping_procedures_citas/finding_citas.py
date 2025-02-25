import asyncio
import unicodedata
import random
from playwright.async_api import async_playwright

PROVINCIA = "Asturias"#Ceuta
PROCEDURA = "FAMILIARES DE RESIDENTES COMUNITARIOS"#"POLICÍA - COMUNICACIÓN DE CAMBIO DE DOMICILIO"

# Тестовые данные для формы
ID_CITADO_VALUE = "Z8579791Z"    # txtIdCitado
DES_CITADO_VALUE = "ALBERTO SORDI"  # txtDesCitado
PAIS_NAC_VALUE = "ARMENIA"         # txtPaisNac
AGE_VALUE = "2000" #txtAnnoCitado

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
]


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


async def human_delay(min_time=0.5, max_time=1.0):
    """Рандомная задержка для эмуляции поведения человека."""
    await asyncio.sleep(random.uniform(min_time, max_time))


def normalize_text(text):
    """Удаляет акценты, лишние пробелы, приводит к нижнему регистру и убирает невидимые символы."""
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return " ".join(text.strip().lower().split())


async def find_available_appointments(provincia, tramite):
    headers = {
        "User-Agent": random_user_agent(),
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=headers["User-Agent"])
        page = await context.new_page()

        # Переходим на главную страницу
        response = await page.goto("https://icp.administracionelectronica.gob.es/icpplus/index.html",
                                   wait_until="domcontentloaded")
        if response and response.status == 429:
            print("❌ Получили 429 Too Many Requests. Останавливаем работу.")
            await browser.close()
            return

        await page.wait_for_selector("select#form")

        # 1. Выбираем провинцию
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

        # 2. Ищем нужную процедуру (tramiteGrupo[0] или tramiteGrupo[1])
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

        # Выбираем процедуру
        await page.select_option(tramites_list_selector, value=tramite_value)
        await human_delay()
        await page.click("input#btnAceptar")
        await page.wait_for_load_state("domcontentloaded")

        # 3. Нажимаем "Entrar"
        print("⏳ Ожидаем кнопку 'Entrar'...")
        entrar_button = None
        try:
            entrar_button = await page.wait_for_selector("input[value='Entrar']", timeout=10000)
        except:
            entrar_button = None

        if not entrar_button:
            print("❌ Кнопка 'Entrar' не найдена.")
            await browser.close()
            return

        await human_delay()
        await entrar_button.click()
        await page.wait_for_load_state("domcontentloaded")

        # 4. Заполняем форму (txtIdCitado, txtDesCitado, txtPaisNac...)
        print("✅ Заполняем форму txtIdCitado, txtDesCitado, txtPaisNac...")

        # NIE/ID
        await page.fill("#txtIdCitado", ID_CITADO_VALUE)
        # ФИО
        await page.fill("#txtDesCitado", DES_CITADO_VALUE)
        #Age
        age_selector = await page.query_selector("#txtAnnoCitado")
        if age_selector:
            await page.fill("#txtAnnoCitado", AGE_VALUE)
        # Страна
        pais_nac_selector = await page.query_selector("#txtPaisNac")
        if pais_nac_selector:
            await page.select_option("#txtPaisNac", label=PAIS_NAC_VALUE)
        else:
            print("❌ Ошибка: Селектор #txtPaisNac не найден!")

        #await page.select_option("#txtPaisNac", label=PAIS_NAC_VALUE)
        # Если в <option> нет label=..., используйте value=...

        await human_delay()
        # Нажимаем "Enviar" (или "Aceptar")
        btn_enviar = await page.wait_for_selector("input#btnEnviar", state="visible", timeout=5000)

        if btn_enviar:
            is_disabled = await page.evaluate("(el) => el.disabled", btn_enviar)
            if is_disabled:
                print("⚠️ Кнопка 'Enviar' заблокирована!")
            else:
                await btn_enviar.scroll_into_view_if_needed()
                await human_delay()
                await btn_enviar.click()

        await page.wait_for_load_state("domcontentloaded")

        # 5. Проверяем, есть ли сообщение "no hay citas" (или "En este momento no hay citas disponibles")
        # Можно проверить через текст в каком-то контейнере, например:
        no_citas_selector = "div:has-text('no hay citas disponibles')"
        # Или используйте точный CSS, если есть, напр.: .msgErrorText

        if await page.query_selector(no_citas_selector):
            # Значит, в данный момент нет записей
            print("❌ En este momento no hay citas disponibles!")
            # Если нужно нажать "Aceptar":
            accept_btn = await page.query_selector("input[value='Aceptar']")  # или button
            if accept_btn:
                await accept_btn.click()
            await browser.close()
            return

        # 6. Если нет сообщения «no hay citas», возможно, страница с оффисами (idSede)
        id_sede_selector = "#idSede"  # Пример
        if await page.query_selector(id_sede_selector):
            # Собираем все офисы
            options = await page.query_selector_all(f"{id_sede_selector} option")
            available_offices = []
            for opt in options:
                office_text = await opt.inner_text()
                office_val = await opt.get_attribute("value")
                # Пропускаем пустую опцию, если есть
                if office_val and office_val.strip():
                    available_offices.append((office_text.strip(), office_val.strip()))

            print("✅ Доступные офисы:")
            for idx, (text, val) in enumerate(available_offices, start=1):
                print(f"{idx}. {text} [value={val}]")

            # Можно нажать "Siguiente" и т.д. — или просто завершить
            # next_btn = await page.query_selector("input[value='Siguiente']")
            # if next_btn:
            #     await next_btn.click()
            #     ...и так далее

        else:
            # Иначе, ни "no hay citas" сообщения, ни "#idSede" — может быть другая логика
            print("⚠️ Ни офис, ни ошибка. Смотрим HTML страницы...")

        # На всякий случай выводим часть HTML текущей страницы
        html_content = await page.content()
        print("\n🔎 HTML страницы (обрезано до 500 символов):\n")
        print(html_content[:500])

        print("⏳ Ожидание 30 секунд...")
        await asyncio.sleep(30)
        await browser.close()


# Запуск поиска
asyncio.run(find_available_appointments(PROVINCIA, PROCEDURA))
