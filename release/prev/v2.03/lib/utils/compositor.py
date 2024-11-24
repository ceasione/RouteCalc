
from settings import SMS_TEXT_REDIAL_PHONE

def __round_cost(cost):

    if 0 < cost <= 1300:
        return round(cost, -1)
    elif 1300 < cost <= 35000:
        return round(cost, -2)
    elif 35000 < cost:
        return round(cost, -3)


def make_sms_text(place_a_name: str,
                  place_b_name: str,
                  vehicle_name: str,
                  cost_is_per_ton: bool,
                  cost: float) -> str:
    s = list()
    s.append(f'{place_a_name} - {place_b_name}\n')
    s.append(f"Транспорт: {vehicle_name}\n")
    if cost_is_per_ton:
        cost_per_ton = cost / 25.0
        s.append('{:,.2f}'.format(__round_cost(cost_per_ton)).replace(',', ' '))  # returns format '10 700.68'
        # https://stackoverflow.com/questions/13082620/
        s.append(' грн за тонну\n')
    else:
        s.append('{:,.2f}'.format(__round_cost(cost)).replace(',', ' '))
        s.append(' грн\n')
    s.append(f'{SMS_TEXT_REDIAL_PHONE}\n\n')
    s.append('https://intersmartgroup.com/\n\n')
    s.append('Ціна розрахована автоматично та не є кінцевою. Завжди телефонуйте!')
    return str().join(s)


def test_make_sms_text():
    print(make_sms_text("Калуш", "Смела", "Автовоз", False, 14158.38))


def __generate_map_url(*args):
    if len(args) < 2:
        raise RuntimeError('Internal error 6')

    base = f'https://www.google.com.ua/maps/dir/'
    s = list()
    s.append(base)

    for place in args:
        s.append(f'{str(place.lat)},{str(place.lng)}/')
    return str().join(s)


def __generate_place_chain(*args):

    if len(args) < 1:
        raise RuntimeError('Internal error 7')

    s = list()
    for place in args:
        s.append(place.name)
        s.append(' - ')
    s.pop()

    return str().join(s)


def compose_telegram(intent, details, locale, url, ip):
    s = list()

    # Просчет или Клиент нажал ПЕРЕЗВОНИТЬ
    if intent == 'calc':
        s.append('Просчет\n\n')
    elif intent == 'callback':
        s.append('Клиент нажал Перезвонить\n\n')
    else:
        raise RuntimeError('Internal Error 5')

    s.append(f'Lang: {"ua" if locale == "uk_UA" else "ru"}\n')
    s.append(f'Page URL: {url}\n')
    s.append(f'IP: {ip}\n\n')

    # Из: Репки, Черниговская область, Украина
    # В: Смела, Черкасская область, Украина
    # Маршрут: https://www.google.com.ua/maps/dir/50.5465397,30.4010721/50.5380305,30.4443308/50.554393,30.469565/
    s.append(f'{details["place_a"].name_long}\n\n')
    s.append(f'{details["place_b"].name_long}\n\n')
    s.append(f'[Google Maps]({__generate_map_url(details["place_a"], details["place_b"])})\n\n')

    # Расчитанный маршрут: Чернигов - Репки - Смела - Черкассы
    # Расчитанное растояние: 985 км
    # [ссылка](https://)
    s.append(f'Расчет: *{__generate_place_chain(*details["route"])}*\n')
    s.append(f'Расстояние: {round(float(details["total_distance"])/1000, 0)} км\n')
    s.append(f'[Google Maps]({__generate_map_url(*details["route"])})\n\n')

    # Авто: Тент 10
    # Цена: 13600,00
    # Телефон клиента: 380672232586
    s.append(f'Авто: {details["vehicle"].name}\n')
    s.append('Цена: ')

    # 10 700.68
    if details['vehicle'].price_per_ton:
        cost_per_ton = details['cost'] / 25.0
        # s.append(str(rounded_cost) + '0')
        # returns format '10 700.68' https://stackoverflow.com/questions/13082620/
        s.append('{:,.2f}'.format(__round_cost(cost_per_ton)).replace(',', ' '))
        s.append(' грн за тонну')
    else:
        # s.append(str(__round_cost(details['cost'])) + '0')
        s.append('{:,.2f}'.format(__round_cost(details['cost'])).replace(',', ' '))
        s.append(' грн')


    s.append(f', ({round(details["price"], 2)} грн/км)\n')
    s.append(f'Телефон клиента: +{details["client_phone"]}')

    return str().join(s)

if __name__ == '__main__':
    test_make_sms_text()