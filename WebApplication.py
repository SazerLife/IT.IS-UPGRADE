import dash                                         # модуль для создания веб приложений (pip install dash)
import dash_core_components as dcc
import dash_html_components as html
import pymysql                                      # модуль для работы с mySQL (pip install pymysql)
from pymysql.cursors import DictCursor
from datetime import timedelta as td

# --- Подключчение к БД ---
connection = pymysql.connect(
    host='localhost',
    user='root',                    # <-- Укажите имя пользователя MySQL сервера
    password='',                    # <-- Укажите пароль MySQL сервера
    db='all_to_the_bottom',
    charset='utf8mb4',
    cursorclass=DictCursor
)
cursor = connection.cursor()

# --- Названия всех категорий (название категории в БД : название категории на русском) ---
categories_name = {'fresh_fish': 'Свежая рыба', 'canned_food': 'Консервированная еда',
                   'semi_manufactures': 'Полуфабрикаты', 'caviar': 'Икра', 'frozen_fish': 'Замороженная рыба'}

# --- Формирование приложения Dush ---
app = dash.Dash(__name__)

# --- Формирование HTML страницы ---
app.layout = html.Div(children=[
    html.H1("All to the bottom (Генератор отчётов)"),
    html.Div("Web-приложение Александра Кузьмина для {IT.IS} UPGRADE"),
    dcc.Dropdown(
        id='MainDropDown',
        options=[
            {'label': 'Посетители из какой страны совершают больше всего действий на сайте?', 'value': 'MostAction'},
            {'label': 'Посетители из какой страны чаще всего интересуются товарами из определенных категорий?', 'value': 'MostPopularCategory'},
            {'label': 'В какое время суток чаще всего просматривают определенные категории товаров?', 'value': 'TimeOfDay'},
            {'label': 'Какая нагрузка (число запросов) на сайт за астрономический час?', 'value': 'Stress'}
        ],
        placeholder="Что вы бы хотели узнать?",
        searchable=False,
    ),
    html.Div(id='MainOutputContainer')
])


# --- Функция отслеживающая запрос из выподающего меню и формирующая ответ (возвращает HTML элемент) ---
@app.callback(
    dash.dependencies.Output('MainOutputContainer', 'children'),
    [dash.dependencies.Input('MainDropDown', 'value')])
def main_update(value):
    # Уловие для определения, что выбрал пользователь в выподающем меню
    if value == 'MostAction':
        countries = dict()      # словарик(Страна: Кол-во запросов)

        sql = "SELECT country FROM Requests"
        cursor.execute(sql)
        # Считаю количество запросов для каждой страны
        for row in cursor:
            if row['country'] in countries:
                countries[row['country']] += 1
            else:
                countries[row['country']] = 1

        # Ищу страну с наибольшим количеством запросов
        most_requests = max(countries.values())
        for country, requestsCount in countries.items():
            if requestsCount == most_requests:
                return html.H3(country + ' - ' + str(requestsCount) + ' запросов')

    elif value == 'MostPopularCategory':
        children = list()       # Лист с HTML элементами для return-а :)

        # Ищу страну с наибольшим количеством запросов для каждой категории
        for category in categories_name.keys():
            countries = dict()      # словарик(Страна: Кол-во запросов)

            sql = "SELECT country, category FROM Requests"
            cursor.execute(sql)
            # Считаю количество запросов для каждой страны
            for row in cursor:
                if row['category'] == category:
                    if row['country'] in countries:
                        countries[row['country']] += 1
                    else:
                        countries[row['country']] = 1

            # Ищу страну с наибольшим количеством запросов
            most_requests = max(countries.values())
            for country, requestsCount in countries.items():
                if requestsCount == most_requests:
                    children.append([categories_name[category], ' - ', country, ' - ', requestsCount, 'запросов'])
                    break

        # Из собранных HTML элементов формирую таблицу и возвращаю её
        return html.Table(
                [html.Tr([
                    html.Td(part) for part in child])
                        for child in children])

    elif value == 'TimeOfDay':
        children = list()       # Лист с HTML элементами для return-а :)

        # Для каждой категории ищу время суток с наибольшим кол-вом запросов
        for category in categories_name.keys():
            time_of_day = {'утром с 5:00 до 11:00': 0, 'днём с 11:00 до 17:00': 0, 'вечером с 17:00 до 23:00': 0, 'ночью с 23:00 до 6:00': 0}

            sql = "SELECT category, t FROM Requests"
            cursor.execute(sql)
            # Для каждого времени определяю к какому времени суток оно относится
            for row in cursor:
                if category == row['category']:
                    if td(hours=5) <= row['t'] < td(hours=11):
                        time_of_day['утром с 5:00 до 11:00'] += 1
                    elif td(hours=11) <= row['t'] < td(hours=17):
                        time_of_day['днём с 11:00 до 17:00'] += 1
                    elif td(hours=17) <= row['t'] < td(hours=23):
                        time_of_day['вечером с 17:00 до 23:00'] += 1
                    elif (td(hours=23) <= row['t'] <= td(hours=23, minutes=59, seconds=59) or
                          td(hours=0) <= row['t'] < td(hours=5)):
                        time_of_day['ночью с 23:00 до 6:00'] += 1

            # Ищу время суток, в которое производилось больше всего запросов
            most_requests = max(time_of_day.values())
            for timeD, requestsCount in time_of_day.items():
                if requestsCount == most_requests:
                    children.append([categories_name[category], ' - ', timeD])
                    break

        # Из собранных HTML элементов формирую таблицу и возвращаю её
        return html.Table(
            [html.Tr([
                html.Td(part) for part in child])
                for child in children])

    elif value == 'Stress':
        datetime = dict()       #словарик(дата+время: кол-во запросов за промежуток между предыдущим часом и текущим )

        sql = "SELECT d, t FROM Requests"
        cursor.execute(sql)

        # Для каждого времени в запросе определяю, к какому астаномическому часу он относится
        for row in cursor:
            for i in range(0, 24):
                if td(hours=i) <= row['t'] <= td(hours=i, minutes=59, seconds=59):
                    if str(row['d']) + '(' + str(td(days=2, hours=i + 1))[8:-3] + ')' in datetime.keys():
                        datetime[str(row['d']) + '(' + str(td(days=2, hours=i + 1))[8:-3] + ')'] += 1
                    else:
                        datetime[str(row['d']) + '(' + str(td(days=2, hours=i + 1))[8:-3]+ ')'] = 1
                    break

        # Формирую и возвращаю график, где ось X - астрономические часы, Y - кол-во запросов в каждый из них
        return dcc.Graph(
            figure=dict(
                data=[
                    dict(
                        x=list(datetime.keys()),
                        y=list(datetime.values()),
                        name='Число запросов в указанный час'
                    ),
                ],
                layout=dict(
                    title='Нагрузка на сайт',
                    showlegend=True,
                    legend=dict(
                        x=0,
                        y=1.0
                    ),
                    margin=dict(l=30, r=0, t=40, b=150),
                )
            )
            )

    return ''


# --- Запуск сервера ---
if __name__ == '__main__':
    app.run_server(debug=True)

# --- Оключение от БД ---
cursor.close()
connection.close()
