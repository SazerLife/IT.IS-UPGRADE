import sys
import pymysql                                      # модуль для работы с бд (pip install pymysql)
from pymysql.cursors import DictCursor

sys.path.insert(0, "./Country_search")
from pysyge import GeoLocator, MODE_BATCH           # модуль для парсинга бд с диапзоном стран по IP

# --- Подключчение к БД ---
connection = pymysql.connect(
    host='localhost',
    user='root',                    # <-- Узказать имя пользователя MySQL сервера
    password='',                    # <-- Узказать пароль MySQL сервера
    db='all_to_the_bottom',
    charset='utf8mb4',
    cursorclass=DictCursor
)

logs = open('logs.txt', 'r')
geoData = GeoLocator('./Country_search\SxGeoCity.dat', MODE_BATCH)      # Инициализируем объект для поиска стран по IP

'''
Столбцы таблицы Requests:
1. Индивидуалный ID зпроса
2. Страна запроса (определятеся по Ip)
3. Дата запроса
4. Время запроса
5. Категория товара
'''
for line in logs.readlines():
    line = line.split()
    del(line[0:2], line[3])

    # --- Определение страны по IP ---
    country = ''
    location = geoData.get_location(line[3], detailed=True)     # в line[3] лежит IP
    if location != {}:
        country = location['info']['country']['name_ru']

    # --- Определяем, на странице с какой категорией и каким товаром находится пользователь ---
    line[4] = line[4][30:-1]        # отсекаем лишнюю часть в запросе
    Category = ''
    '''
    Если это не добавление в корзину и не оплата, то
    1. разбиваем оставшийся адрес на часть с категорией и часть с товаром
    2. присваевам посещённую категорию
    '''
    if not ("cart?goods_id" in line[4] or "pay?user_id" in line[4] or "success_pay" in line[4]):
        line[4] = line[4].split('/')
        Category = line[4][0]

    # --- Формируем лист со значениями переменных для таблицы в БД ---
    answerList = [line[2],
                  country,
                  line[0],
                  line[1],
                  Category
                  ]

    # --- Заполнение БД ---
    with connection.cursor() as cursor:
        sql = "INSERT INTO `Requests` (`requestId`, `country`, `d`, `t`, `category`) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, answerList)

# --- Коммитим и закрываем за собой файлы бд и логов =) ---
logs.close()
connection.commit()
connection.close()
