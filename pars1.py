from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from bs4 import BeautifulSoup


# Записываем файл
with open('result_Brady.csv', 'w', encoding='utf-8-sig', newline='') as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerow(['Раздел', 'Код товара', 'Производитель', 'Наличие', 'Цена', 'Ссылка на карточку с товаром', 'Описание'])

categories = ['printerny', 'kartridzhi-i-lenty', 'blokiruyushchie-ustrojstva', 'ehtiketki-i-markery-brdy', 'software', 'gotovaya-markirovka', 'ribbony', 'aksessuary']

categories_mapping = {
    'printerny': 'Принтеры',
    'kartridzhi-i-lenty': 'Картриджи и ленты',
    'blokiruyushchie-ustrojstva': 'Блокирующие устройства',
    'ehtiketki-i-markery-brdy': 'Этикетки и маркеры',
    'software': 'Софт',
    'gotovaya-markirovka': 'Готовая маркировка',
    'ribbony': 'Риббоны',
    'aksessuary': 'Аксессуары'
}

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

for category in categories:
    print(f"Обработка категории: {category}")
    url = f"https://bradytool.ru/{category}/page-1?limit=100"
    driver.get(url)

    # Безопасное получение количества страниц
    try:
        result_text = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'result'))).text
        pages = int(result_text.split('(всего ')[1].split(' страниц')[0])
    except Exception as e:
        print(f"Не удалось получить количество страниц для категории {category}: {e}")
        pages = 1

    for page in range(1, pages + 1):
        new_url = f"https://bradytool.ru/{category}/page-{page}?limit=100"
        print(f"Обрабатывается страница {page} из {pages}")
        driver.get(new_url)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-name")))

        # Получаем ссылки на карточки товаров
        cards = driver.find_elements(By.CLASS_NAME, "product-name")
        links = [card.find_element(By.TAG_NAME, "a").get_attribute("href") for card in cards]

        # Обрабатываем каждую карточку
        for link in links:
            try:
                driver.get(link)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                sleep(.1)  # Даём время на загрузку динамического контента

                soup = BeautifulSoup(driver.page_source, 'lxml')

                razdel = categories_mapping.get(category, 'Неизвестный раздел')

                # 1. Код товара
                code_item = soup.find('li', string=lambda text: text and 'Код товара:' in text)
                code = code_item.get_text().split('Код товара: ')[1].strip() if code_item else None

                # 2. Цена
                price_element = soup.select_one('ul.list-unstyled h2')
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    price = price_text.replace('р.', '').replace(' ', '').strip()
                else:
                    price = None

                # 3. Наличие
                availability_item = soup.find('li', string=lambda text: text and 'Наличие:' in text)
                availability = availability_item.get_text().split('Наличие: ')[1].strip() if availability_item else None

                # 4. Производитель
                manufacturer_element = soup.select_one('li:-soup-contains("Производитель:") a')
                if manufacturer_element:
                    manufacturer = manufacturer_element.get_text(strip=True)
                else:
                    manufacturer = None

                # 5. Описание
                description_div = soup.find('div', class_='tab-pane active', id='tab-description')
                description = description_div.get_text(strip=True) if description_div else None

                # Формируем строку для записи
                row = [razdel, code, manufacturer, availability, price, link, description]
                print(row)

                # Записываем в CSV
                with open('result_Brady.csv', 'a', encoding='utf-8-sig', newline='') as file:
                    writer = csv.writer(file, delimiter=';', lineterminator='\n')
                    writer.writerow(row)

            except Exception as e:
                print(f"Ошибка при обработке товара {link}: {e}")
                continue

driver.quit()
print('Файл result_Brady.csv создан')
