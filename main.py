import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from openpyxl import Workbook
from tqdm import tqdm, tqdm as tqdm_module


MINIMUM_MEMBERS = 1000


# Logging handler compatible with tqdm
class TqdmCompatibleHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm_module.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)


# Настройка логирования в файл
file_handler = logging.FileHandler("parser.log", mode="w", encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)

handler = TqdmCompatibleHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logging.getLogger().handlers = [handler, file_handler]
logging.getLogger().setLevel(logging.INFO)


def gather_channel_links(url):
    links = []
    logging.info(f"📄 Загружаем страницу: {url}")
    time.sleep(random.uniform(1, 3))
    html = requests.get(url)
    bs = BeautifulSoup(html.text, "html.parser")

    channel_link_tags = bs.find_all("div", class_="tg-channel-link")
    logging.info(f"🔍 Найдено {len(channel_link_tags)} блоков со ссылками")
    for cl in channel_link_tags:
        channel_link = cl.find("a")
        if channel_link:
            channel_url = channel_link.get("href")
            channel_parent_div = cl.find_parent("div")
            members_count = int(
                channel_parent_div.find("span", {"class": "tg-user-count"})
                .get_text()
                .strip()
            )
            if members_count <= MINIMUM_MEMBERS:
                logging.info(
                    f"❌ Пропускаем канал с количеством участников {members_count} < {MINIMUM_MEMBERS}"
                )
                continue
            else:
                if channel_url not in links:
                    links.append(channel_url)
                    logging.info(
                        f"🌐 Добавлена ссылка на канал: https://tgramsearch.com{channel_url}"
                    )
    logging.info(f"📦 Всего ссылок с этой страницы: {len(links)}")
    return [f"https://tgramsearch.com{link}" for link in links]


def extract_data(url):
    logging.info(f"🔗 Извлекаем ссылку со страницы: {url}")
    time.sleep(random.uniform(1, 3))
    html = requests.get(url)
    bs = BeautifulSoup(html.text, "html.parser")

    channel_card_div = bs.find(
        "div", {"class": ["tg-channel-wrapper", "is-detail"]}
    )
    if channel_card_div:
        channel_link = channel_card_div.find("a", {"class": "app"})
        if channel_link:
            channel_url = channel_link.attrs["href"].replace(
                "tg://resolve?domain=", "@"
            )
            channel_name = (
                channel_card_div.find("h1", {"class": "tg-channel-header"})
                .get_text()
                .strip()
            )
            members_count = int(
                channel_card_div.find("span", {"class": "tg-user-count"})
                .get_text()
                .strip()
            )
            logging.info(
                f"✅ Финальная ссылка на Telegram-канал: {channel_url}"
            )
            return channel_url, channel_name, members_count
        else:
            logging.warning(
                f"❌ Ссылка на Telegram-канал не найдена внутри контейнера на странице: {url}"
            )
    else:
        logging.warning(
            f"❌ Контейнер с деталями канала не найден на странице: {url}"
        )


def get_channel_data(channel_url):
    logging.info(f"🚀 Начинаем сбор данных с категории: {channel_url}")
    links = []
    gathered_links = []
    page_num = 1
    url = f"{channel_url}?page={page_num}"
    while True:
        old_len = len(gathered_links)
        time.sleep(random.uniform(1, 3))
        page_links = gather_channel_links(url)
        for p in page_links:
            if p not in gathered_links:
                gathered_links.append(p)
        new_len = len(gathered_links)
        logging.info(
            f"📄 Обработана страница {page_num}, всего собрано: {len(gathered_links)}"
        )
        if old_len == new_len:
            break
        page_num += 1
        url = f"{channel_url}?page={page_num}"

    logging.info(
        f"📚 Завершён сбор всех страниц. Обнаружено {len(gathered_links)} ссылок для обработки."
    )
    logging.info("🎯 Закончен сбор ссылок, начинаем извлечение финальных URL")
    for link in tqdm(
        gathered_links, desc="📦 Извлечение информации о каналах"
    ):
        data = extract_data(link)
        if data and data not in links:
            links.append(data)
    return links


def write_xlsx(links: list, category: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = category

    ws.append(
        ["Ссылка", "Название канала", "Категория", "Количество участников"]
    )

    for url, name, members in links:
        ws.append([url, name, category, members])

    filename = f"{category}_channels.xlsx"
    wb.save(filename)
    logging.info(f"💾 Данные успешно сохранены в файл: {filename}")


def main():
    category_name = input("Введите название категории: ")
    logging.info("🧠 Запуск основной процедуры парсинга...")
    links = get_channel_data("https://tgramsearch.com/categories/it")
    logging.info(f"📊 Найдено уникальных Telegram-ссылок: {len(links)}")
    write_xlsx(links, category_name)
    logging.info("✅ Работа завершена! Все данные сохранены.")


if __name__ == "__main__":
    main()
