
from impsettings import settings
from lib.utils.DTOs import CalculationDTO
from lib.utils.DTOs import LocaleDTO

SMS_TEXT_REDIAL_PHONE = settings.SMS_TEXT_REDIAL_PHONE


def __round_cost(cost):

    if 0 < cost <= 1300:
        return round(cost, -1)
    elif 1300 < cost <= 35000:
        return round(cost, -2)
    elif 35000 < cost:
        return round(cost, -3)


def make_sms_text(calculation: CalculationDTO) -> str:
    if calculation.is_price_per_ton:
        price = f'{calculation.price_per_ton} {calculation.currency} за тонну'
    else:
        price = f'{calculation.price} {calculation.currency}'

    fstring = f'''{calculation.place_a_name} - {calculation.place_b_name}
Транспорт: {calculation.transport_name}
{price}
{SMS_TEXT_REDIAL_PHONE}

https://intersmartgroup.com/

Ефективність – наш стандарт. Довіряйте Inter Smart.'''

    return fstring


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


def compose_telegram(intent, calculation, url, ip, phone_num='#'):
    s = list()

    # Просчет или Клиент нажал ПЕРЕЗВОНИТЬ
    if intent == 'calc':
        s.append('Просчет\n\n')
    elif intent == 'callback':
        s.append('Клиент нажал Перезвонить\n\n')
    elif intent == 'acquire':
        s.append('Просчет без номера\n\n')
    else:
        raise RuntimeError('Internal Error 5')

    s.append(f'Lang: {"ua" if calculation.locale.is_uk_ua() else "ru"}\n')
    s.append(f'Page URL: `{url}`\n\n')
    s.append(f'IP: [{ip}](http://ip-api.com/line/{ip})\n\n')

    # Из: Репки, Черниговская область, Украина
    # В: Смела, Черкасская область, Украина
    # Маршрут: https://www.google.com.ua/maps/dir/50.5465397,30.4010721/50.5380305,30.4443308/50.554393,30.469565/
    s.append(f'{calculation.place_a_name} - {calculation.place_b_name}\n\n')
    s.append(f'[Google Maps]({calculation.map_link})\n\n')

    # Расчитанный маршрут: Чернигов - Репки - Смела - Черкассы
    # Расчитанное растояние: 985 км
    # [ссылка](https://)
    s.append(f'Расчет: *{calculation.place_chain}*\n')
    s.append(f'Расстояние: {calculation.distance} км\n')
    s.append(f'[Google Maps]({calculation.chain_map_link})\n\n')

    # Авто: Тент 10
    # Цена: 13600,00
    # Телефон клиента: 380672232586
    s.append(f'Авто: {calculation.transport_name}\n')
    s.append('Цена: ')

    # 10 700.68
    if calculation.is_price_per_ton:
        # s.append(str(rounded_cost) + '0')
        # returns format '10 700.68' https://stackoverflow.com/questions/13082620/
        s.append(calculation.price_per_ton)
        s.append(f' {calculation.currency} за тонну')
    else:
        # s.append(str(__round_cost(details['cost'])) + '0')
        s.append(calculation.price)
        s.append(f' {calculation.currency}')

    s.append(f', ({calculation.price_per_km} за км):\n')
    s.append(f'  Vehicle: {calculation.pfactor_vehicle}\n')
    s.append(f'  Departure: {calculation.pfactor_departure}\n')
    s.append(f'  Arrival: {calculation.pfactor_arrival}\n')
    s.append(f'  Distance: {calculation.pfactor_distance}\n')
    s.append(f'  Currency: {calculation.currency_rate}')
    if phone_num is not None:
        s.append(f'\n\nТелефон клиента: +{phone_num}')

    return str().join(s)


def make_calculation_dto(details, locale) -> CalculationDTO:
    raw_price = details['cost']
    transport_capacity = details['vehicle'].weight_capacity
    price_per_ton = '{:,.2f}'.format(__round_cost(raw_price/float(transport_capacity))).replace(',', ' ')
    price = '{:,.2f}'.format(__round_cost(raw_price)).replace(',', ' ')

    return CalculationDTO(place_a_name=details["place_a"].name,
                          place_a_name_long=details["place_a"].name_long,
                          place_b_name=details["place_b"].name,
                          place_b_name_long=details["place_b"].name_long,
                          map_link=__generate_map_url(details["place_a"], details["place_b"]),
                          place_chain=__generate_place_chain(*details["route"]),
                          chain_map_link=__generate_map_url(*details["route"]),
                          distance=str(round(float(details["total_distance"])/1000, 1)),
                          transport_id=details['vehicle'].id,
                          transport_name=details['vehicle'].name if locale == 'ru_UA' else details['vehicle'].name_ua,
                          transport_capacity=transport_capacity,
                          price=price,
                          currency=details['currency'],
                          currency_rate=details['currency_rate'],
                          price_per_ton=price_per_ton,
                          price_per_km=str(round(details['price'], 2)),
                          is_price_per_ton=details['vehicle'].price_per_ton,
                          pfactor_vehicle=details['pfactor_vehicle'],
                          pfactor_departure=details['pfactor_departure'],
                          pfactor_arrival=details['pfactor_arrival'],
                          pfactor_distance=details['pfactor_distance'],
                          locale=LocaleDTO(locale))
