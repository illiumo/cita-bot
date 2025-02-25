import asyncio
import time
import random
import unicodedata
from collections import defaultdict
import json
from playwright.async_api import async_playwright
from database.setup import SessionLocal
from database.models import Subscription
from bot.utils.state_manager import file_path

# Импортируем функцию send_notifications из notification_handler
from bot.handlers.notification_handler import send_notifications


########################################################################
#                     Настройки (Можно подправить)
########################################################################

CHECK_INTERVAL = 60  # Секунды между полными циклами
BATCH_SIZE = 1       # Сколько пар (провинция, процедура) проверяем за один "мини-цикл"
HEADLESS = False      # True = невидимый браузер, False = видно окно

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)... Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)... Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64)... Chrome/97.0.4692.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)... Safari/605.1.15"
]

ID_CITADO_VALUE = "Z8579791Z"     # Условный NIE
DES_CITADO_VALUE = "ALBERTO SORDI"  # ФИО
PAIS_NAC_VALUE = "ARMENIA"          # Страна
AGE_VALUE = "2000"                  # Год
CONFIG_PATH = file_path    # Путь к конфигу
########################################################################


def random_user_agent() -> str:
    """Выбираем случайный User-Agent из списка."""
    return random.choice(USER_AGENTS)


async def human_delay(min_time=0.5, max_time=1.0):
    """Рандомная задержка (эмуляция человека)."""
    import random
    import asyncio
    await asyncio.sleep(random.uniform(min_time, max_time))


def normalize_text(text):
    """Удаляет акценты, лишние пробелы, приводит к нижнему регистру."""
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return " ".join(text.strip().lower().split())


def get_procedure_text_from_config(procedure_id, config_path=CONFIG_PATH):
    """
    Находит в config.json название процедуры (campo "nombre") по её ID (campo "valor").
    Если не найдена — возвращаем сам ID.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for province_data in data.values():
            for category in ("tramites_oficinas_extranjeria", "tramites_policia_nacional"):
                for proc in province_data.get(category, []):
                    if proc.get("valor") == procedure_id:
                        return proc.get("nombre", procedure_id)
    except Exception as e:
        print(f"⚠️ Ошибка при чтении {config_path}: {e}")
    return procedure_id


########################################################################
#           Работа с БД: получаем и группируем подписки
########################################################################

def get_active_subscriptions():
    """Достаём все активные подписки (telegram_id, province, procedure)."""
    session = SessionLocal()
    try:
        subs = session.query(Subscription.telegram_id, Subscription.province, Subscription.procedure) \
            .filter(Subscription.status == 'active').all()
        return subs
    finally:
        session.close()

def group_subscriptions():
    """
    Группируем подписки по (province, procedure).
    Возвращаем: { (province, procedure): {telegram_id, ...} }
    """
    subscriptions = get_active_subscriptions()
    grouped = defaultdict(set)
    for telegram_id, province, procedure_id in subscriptions:
        # Храним их по (province, procedure_id), а при проверке преобразуем procedure_id -> текст
        grouped[(province, procedure_id)].add(telegram_id)
    return grouped


########################################################################
#     Основная асинхронная функция проверки одной пары (province, procedure)
########################################################################
async def find_available_appointments(province: str, procedure_id: str) -> bool:
    """
    Возвращает True, если в ходе проверки нашлись свободные записи, иначе False.
    Здесь procedure_id -> преобразуем в человеческое название из config.json, а потом ищем на сайте.
    """
    # 1) Сначала преобразуем ID в текст
    procedure_text = get_procedure_text_from_config(procedure_id)

    headers = {
        "User-Agent": random_user_agent(),
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(user_agent=headers["User-Agent"])
        page = await context.new_page()

        # Переходим на главную страницу
        response = await page.goto("https://icp.administracionelectronica.gob.es/icpplus/index.html",
                                   wait_until="domcontentloaded")
        if response and response.status == 429:
            print("❌ 429 Too Many Requests. Останавливаем работу на эту пару.")
            await browser.close()
            return False

        await page.wait_for_selector("select#form", timeout=8000)

        # Ищем значение для выбранной провинции
        provincias = await page.query_selector_all("select#form option")
        provincia_value = None
        for option in provincias:
            name = await option.inner_text()
            if normalize_text(name) == normalize_text(province):
                provincia_value = await option.get_attribute("value")
                break

        if not provincia_value:
            print(f"❌ Провинция '{province}' не найдена на сайте.")
            await browser.close()
            return False

        # Выбираем провинцию
        await page.select_option("select#form", value=provincia_value)
        await human_delay()
        await page.click("input#btnAceptar")
        await page.wait_for_load_state("domcontentloaded")

        # Определяем, куда ставить процедуру
        tramite_0_selector = "select[name='tramiteGrupo[0]']"
        tramite_1_selector = "select[name='tramiteGrupo[1]']"

        # Если начинается с "policia", то [1]
        if procedure_text.strip().lower().startswith("policia"):
            tramites_list_selector = tramite_1_selector
        else:
            tramites_list_selector = tramite_0_selector

        await page.wait_for_selector(tramites_list_selector, timeout=8000)
        tramites_options = await page.query_selector_all(f"{tramites_list_selector} option")

        tramite_value = None
        for option in tramites_options[1:]:
            text = normalize_text(await option.inner_text())
            if text == normalize_text(procedure_text):
                # Нашли нужную процедуру
                tramite_value = await option.get_attribute("value")
                break

        if not tramite_value:
            print(f"❌ Процедура '{procedure_text}' не найдена в провинции '{province}'.")
            await browser.close()
            return False

        # Выбираем процедуру
        await page.select_option(tramites_list_selector, value=tramite_value)
        await human_delay()
        await page.click("input#btnAceptar")
        await page.wait_for_load_state("domcontentloaded")

        # Нажимаем "Entrar"
        try:
            entrar_button = await page.wait_for_selector("input[value='Entrar']", timeout=15000)
        except:
            entrar_button = None
        if not entrar_button:
            print("❌ Кнопка 'Entrar' не найдена.")
            await browser.close()
            return False

        await human_delay()
        await entrar_button.click()
        await page.wait_for_load_state("domcontentloaded")

        # Заполняем форму
        await page.fill("#txtIdCitado", ID_CITADO_VALUE)
        await page.fill("#txtDesCitado", DES_CITADO_VALUE)
        if await page.query_selector("#txtAnnoCitado"):
            await page.fill("#txtAnnoCitado", AGE_VALUE)

        pais_nac_selector = await page.query_selector("#txtPaisNac")
        if pais_nac_selector:
            await page.select_option("#txtPaisNac", label=PAIS_NAC_VALUE)

        await human_delay()
        enviar_btn = await page.wait_for_selector("input#btnEnviar", timeout=5000)
        if enviar_btn:
            is_disabled = await page.evaluate("(el) => el.disabled", enviar_btn)
            if not is_disabled:
                await enviar_btn.click()
            else:
                print("⚠️ Кнопка 'Enviar' заблокирована.")
                await browser.close()
                return False

        await page.wait_for_load_state("domcontentloaded")

        # Проверяем текст "no hay citas"
        no_citas_selector = "div:has-text('no hay citas disponibles')"
        if await page.query_selector(no_citas_selector):
            print(f"❌ Для {province} - {procedure_text} сейчас нет мест.")
            await browser.close()
            return False

        # Если нет "no hay citas", значит потенциально есть записи
        print(f"✅ Найдены свободные места (или след. форма) для {province} - {procedure_text}!")
        await browser.close()
        return True


########################################################################
#               Асинхронный "батчовый" бесконечный цикл
########################################################################
async def main_loop():
    while True:
        grouped = group_subscriptions()  # {(prov, procedure_id): {tg_id1, tg_id2}}
        if not grouped:
            print("Нет активных подписок. Ожидаем...")
            await asyncio.sleep(CHECK_INTERVAL)
            continue

        combos = list(grouped.items())  # [((prov, proc_id), {user_ids}), ...]
        print(f"Нужно проверить {len(combos)} комбинаций (провинция+процедура).")

        batch_start = 0
        while batch_start < len(combos):
            batch_end = batch_start + BATCH_SIZE
            batch = combos[batch_start:batch_end]

            found_citas = {}  # { (province, procedure_id): {tg_id, ...} }

            # Обрабатываем батч
            for (province, procedure_id), user_ids in batch:
                print(f"Проверяем {province} / {procedure_id}, пользователи: {user_ids}")
                try:
                    is_available = await find_available_appointments(province, procedure_id)
                    if is_available:
                        found_citas[(province, procedure_id)] = user_ids
                except Exception as e:
                    print(f"⚠️ Ошибка при проверке {province}, {procedure_id}: {e}")

            # Если что-то нашли
            if found_citas:
                print(f"🔔 Найдены свободные места для {len(found_citas)} комбинаций!")
                # Вызываем send_notifications (из notification_handler)
                # Ожидает структуру вида: { (province, procedure_id): { telegram_ids } }
                send_notifications(found_citas)
            else:
                print("В этом батче свободных мест нет.")

            batch_start = batch_end
            print(f"Ждём {CHECK_INTERVAL}сек перед следующим батчем...")
            await asyncio.sleep(CHECK_INTERVAL)

        # После всех батчей — снова подождём
        print("⌛ Цикл проверки завершён. Ждём перед следующим циклом...")
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main_loop())
