import asyncio
import json
import random
from playwright.async_api import async_playwright

CONFIG_FILE = "config.json"
BASE_URL = "https://icp.administracionelectronica.gob.es/icpplus/index.html"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; rv:99.0) Gecko/20100101 Firefox/99.0",
]

def random_user_agent() -> str:
    return random.choice(USER_AGENTS)

async def human_delay(min_time=1.0, max_time=3.0):
    """Простая рандомная задержка."""
    await asyncio.sleep(random.uniform(min_time, max_time))

async def random_scroll(page):
    """Лёгкая эмуляция движений мыши/прокрутки."""
    scroll_distance = random.randint(200, 800)
    await page.mouse.wheel(0, scroll_distance)
    await human_delay(0.5, 1.5)

async def gather_provinces(page):
    """Собирает список (name, value) всех провинций, кроме «Seleccione provincia»."""
    await page.goto(BASE_URL)
    await page.wait_for_selector("select#form")
    province_options = await page.query_selector_all("select#form option")
    province_list = []
    for i in range(1, len(province_options)):
        name = await province_options[i].inner_text()
        value = await province_options[i].get_attribute("value")
        province_list.append((name, value))
    return province_list

async def scrape_provinces(provinces_batch):
    """Собирает данные по конкретному пакету провинций (batch). Возвращает словарь с данными."""
    province_data = {}
    # Случайный user-agent для каждого батча
    ua = random_user_agent()
    print(f"Запускаем браузер для батча с User-Agent: {ua}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=ua,
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        for province_name, province_value in provinces_batch:
            try:
                print(f"📍 Проверяем провинцию: {province_name}")
                await page.goto(BASE_URL)
                await page.wait_for_selector("select#form")
                await human_delay(1, 3)
                await random_scroll(page)

                # Выбираем провинцию
                await page.select_option("select#form", value=province_value)
                await human_delay(0.5, 1.5)

                # Кликаем "Aceptar"
                await page.click("input#btnAceptar")
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(1, 3)
                await random_scroll(page)

                province_data[province_name] = {
                    "tramites_oficinas_extranjeria": [],
                    "tramites_policia_nacional": []
                }

                # Сбор данных для tramiteGrupo[0] (офисы иностранцев)
                tramite_0_selector = "select[name='tramiteGrupo[0]']"
                if await page.query_selector(tramite_0_selector):
                    tramites_0_options = await page.query_selector_all(f"{tramite_0_selector} option")
                    for option in tramites_0_options[1:]:
                        text = await option.inner_text()
                        value = await option.get_attribute("value")
                        if value:
                            province_data[province_name]["tramites_oficinas_extranjeria"].append({
                                "nombre": text,
                                "valor": value
                            })
                    await human_delay(0.5, 1.5)
                else:
                    print(f"⚠️ Нет селектора tramiteGrupo[0] в {province_name}.")

                # Сбор данных для tramiteGrupo[1] (процедуры полиции)
                tramite_1_selector = "select[name='tramiteGrupo[1]']"
                if await page.query_selector(tramite_1_selector):
                    tramites_1_options = await page.query_selector_all(f"{tramite_1_selector} option")
                    for option in tramites_1_options[1:]:
                        text = await option.inner_text()
                        value = await option.get_attribute("value")
                        if value:
                            province_data[province_name]["tramites_policia_nacional"].append({
                                "nombre": text,
                                "valor": value
                            })
                    await human_delay(0.5, 1.5)
                else:
                    print(f"⚠️ Нет селектора tramiteGrupo[1] в {province_name}.")

                extranjeria_count = len(province_data[province_name]["tramites_oficinas_extranjeria"])
                policia_count = len(province_data[province_name]["tramites_policia_nacional"])
                print(f"✅ {province_name}: extranjería={extranjeria_count}, policía={policia_count}")

            except Exception as e:
                print(f"❌ Ошибка при обработке {province_name}: {e}")
                province_data[province_name] = {
                    "tramites_oficinas_extranjeria": [],
                    "tramites_policia_nacional": []
                }
                # Для осторожности после ошибки можно сделать побольше паузу
                await human_delay(5, 10)

        await browser.close()

    return province_data

async def scrape_all_provinces():
    """Собирает полный список провинций, делит на батчи, обходит каждый батч."""
    # Словарь, куда в конце запишем всё
    final_data = {}

    async with async_playwright() as p:
        # Один контекст, чтобы просто получить список провинций
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        all_provinces = await gather_provinces(page)
        await browser.close()

    # Перемешиваем, чтобы каждый раз порядок был разный
    random.shuffle(all_provinces)

    # Допустим, мы делим на батчи по 10 провинций. Можно изменить.
    batch_size = 10
    batches = [all_provinces[i:i + batch_size] for i in range(0, len(all_provinces), batch_size)]

    for batch_index, provinces_batch in enumerate(batches, start=1):
        print(f"=== Обработка батча {batch_index} из {len(batches)} ===")
        # Собираем данные по этому батчу
        batch_data = await scrape_provinces(provinces_batch)

        # Объединяем в финальный словарь
        final_data.update(batch_data)

        # Сохраняем промежуточный результат (на случай, если скрипт прервётся)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)

        print(f"=== Батч {batch_index} готов! ===")



        # После каждого батча – большая пауза, чтобы "остыть"
        if batch_index < len(batches):
            sleep_minutes = random.randint(3, 8)  # меняйте диапазон на более долгий, если нужно
            print(f"⏳ Ждём {sleep_minutes} минут перед следующим батчем...")
            await asyncio.sleep(sleep_minutes * 60)

    # В конце ещё раз пишем результат
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    print("✅ Все батчи успешно обработаны и данные сохранены в config.json!")

async def schedule_update():
    """Этот цикл будет раз в час заново запускать процесс сбора."""
    while True:
        await scrape_all_provinces()
        print("⏳ Ждём 1 час до следующего обновления...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(schedule_update())