import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. объявляем переменные для правильного формирования ссылки-запроса ( указываем свои данные: магазины, итоговое количество чеков, даты )
retailer = "D,S" # перечень магазинов по которым вы хотите получить чеки: D - Пятерочка, S - Перекресток
count_checks = 11 # количество чеков
date_from = "2024-10-01" # дата от какого числа
date_to = "2024-10-31" # дата к какому числу

# 2. ссылка-запрос ( её не меняем )
url = f"https://id.x5.ru/api/secure/lk-checks/checks?codeTc={retailer}&size={count_checks}&from={date_from}&to={date_to}&page=0"

# 3. токен-авторизации ( указываем свой в соответствии с инструкцией )
access_token = "..." 

# 4. id google-таблицы ( указываем свой в соответствии с инструкцией )
spreadsheet_id = "..."

# конфигурация для google-таблиц
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(spreadsheet_id).sheet1

# заголовки - то без чего не получится сделать запрос (будет падать 400-я ошибка)
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
}

# запрос к api
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    rows = []

    # заголовки для google-таблицы: то как вы хотите видеть запись
    rows.append(["Магазин", "Дата", "Общая сумма покупки", "Список товаров", "", "", ""]) # "" - пустая ячейка
    rows.append(["", "", "", "Товар", "Цена", "Количество", "Метрика"]) # "" - пустая ячейка

    # обрабатываем каждый чек в данных
    for check in data:
        shop = check["title"]
        date = check["created"]
        total_amount = check["amountRegular"]

        # первый товар в чеке
        first_item = True
        for item in check["items"]:
            item_name = item["name"]
            price = item["priceRegular"]
            quantity = item["quantity"]
            metric = item.get("weightUomCode", "шт")

            # если это первая строка для данного чека, добавляем данные магазина, даты и суммы
            if first_item:
                rows.append([shop, date, total_amount, item_name, price, quantity, metric])
                first_item = False
            else:
                # остальные строки только с информацией о товаре
                rows.append(["", "", "", item_name, price, quantity, metric])

    # удаление все данные из google-таблицы перед загрузкой новых
    sheet.clear() # опциональный элемент - если вы хотите накапливать информацию о чеках нужно изменить

    # добавляем данные разом в таблицу
    sheet.append_rows(rows)
    
    print("Данные успешно добавлены в Google Sheets.")
else:
    print("Ошибка доступа:", response.status_code)