
from app import settings
from app.lib.utils.DTOs import CalculationDTO
from textwrap import dedent
from app.lib.calc.place import Place
from app.lib.calc.place import LatLngAble
from typing import Optional

SMS_TEXT_REDIAL_PHONE = settings.SMS_TEXT_REDIAL_PHONE


def make_sms_text(calculation: CalculationDTO) -> str:
    """
    Generates a marketing-style SMS text message based on calculation data
    :param calculation: CalculationDTO object containing data
    :return: A formatted SMS text as a string

    Looks like this:
        Дніпро - Київ
        Транспорт: Тент 20
        19 800.00 UAH за тонну
        +380501234567

        https://intersmartgroup.com/ua

        Ефективність – наш стандарт. Довіряйте Inter Smart.
    """
    price_value = calculation.price_per_ton if calculation.is_price_per_ton else calculation.price
    price_tag = 'за тонну' if calculation.is_price_per_ton else ''
    price = f'{price_value} {calculation.currency} {price_tag}'.strip()

    fstring = f'''
        {calculation.place_a_name} - {calculation.place_b_name}
        Транспорт: {calculation.transport_name}
        {price}
        {SMS_TEXT_REDIAL_PHONE}
        
        https://intersmartgroup.com/ua
        
        Ефективність – наш стандарт. Довіряйте Inter Smart.'''

    return dedent(fstring).strip()


def generate_map_url(*places: LatLngAble) -> str:
    """
    Generates a Google Maps Directions URL for a route through multiple places
    :param places: One or more objects with `lat` and `lng` attributes
    :return: A string containing the Google Maps directions URL
    """
    if len(places) < 2:
        raise ValueError("At least two places are required to generate a map URL")

    base_url = f'https://www.google.com.ua/maps/dir/'
    path = '/'.join(f'{place.lat},{place.lng}' for place in places)

    return f'{base_url}{path}/'


def generate_place_chain(*places: Place) -> str:
    """
    Generates a string of place names separated by ' - '
    :param places: iterable of Places
    :return: string of place names
    """
    if len(places) < 2:
        raise ValueError("At least two places are required to generate place chain")
    return ' - '.join(place.name for place in places)


def compose_telegram_message_text(
    intent: str, 
    calculation: CalculationDTO,
    url: str, 
    ip: str, 
    calculation_id: str,
    phone_num: Optional[str] = None) -> str:
    """
    Compose a Telegram message based on CalculationDTO and some other data
    :param intent: (str) Intent of the original request ('calc', 'callback' or 'acquire')
    :param calculation: (CalculationDTO) dataclass object containing data.
    :param url: (str) Source page URL
    :param ip: (str) Client IP address
    :param calculation_id: (str) Calculation ID - calculation digest
    :param phone_num: (str, optional) number of the client
    :return: (str) A formatted Telegram message.

    Looks like this:
        'Просчет без номера
        Lang: ru
        Page URL: https://intersmartgroup.com/

        IP: 159.224.254.148 (http://ip-api.com/line/159.224.254.148)

        Дніпро - Високе

        Google Maps (https://www.google.com.ua/maps/dir/48.464717,35.046183/50.3302582,34.2722895/)

        Расчет: Дніпро - Високе
        Расстояние: 386.9 км
        Google Maps (https://www.google.com.ua/maps/dir/48.464717,35.046183/50.3302582,34.2722895/)

        Авто: Тент 20
        Цена: 19 800.00 UAH, (51.15 за км):
          Vehicle: 45.0
          Departure: 0.9
          Arrival: 1.2
          Distance: 1.255
          Currency: 1.0'
    """
    intents = {'calc': 'Просчет', 'callback': 'Клиент нажал Перезвонить', 'acquire': 'Просчет без номера'}
    intent_text = intents.get(intent, 'Неизвестный интент')

    price_value = calculation.price_per_ton if calculation.is_price_per_ton else calculation.price
    price_tag = 'за тонну' if calculation.is_price_per_ton else ''
    price = f'{price_value} {calculation.currency} {price_tag}'.strip()

    phone = f'Телефон клиента: +{phone_num}' if phone_num else ''

    fstring = f'''
        {intent_text}
        Lang: {"ru" if calculation.locale == 'ru_UA' else "ua"}, [id]({calculation_id})
        Page URL: `{url}`
        
        IP: [{ip}](http://ip-api.com/line/{ip})
        
        {calculation.place_a_name} - {calculation.place_b_name}
        
        [Google Maps]({calculation.map_link})
        
        Расчет: *{calculation.place_chain}*
        Расстояние: {calculation.distance} км
        [Google Maps]({calculation.chain_map_link})
        
        Авто: {calculation.transport_name}
        Цена: {price}, ({calculation.price_per_km} за км):
          Vehicle: {calculation.pfactor_vehicle}
          Departure: {calculation.pfactor_departure}
          Arrival: {calculation.pfactor_arrival}
          Distance: {calculation.pfactor_distance}
          Currency: {calculation.currency_rate}
        {phone}
    '''
    return dedent(fstring).strip()


def round_cost(cost: float) -> float:
    """
    Rounds float number depending on ranges:
         0 -  1300:     987.13 ->   990.0
      1300 - 35000:   26138.25 -> 26100.0
     35000 -   inf:   68925.14 -> 69000.0
    :param cost: (float) input
    :return: (float) rounded
    """
    if 0 < cost <= 1300:
        return round(cost, -1)
    elif 1300 < cost <= 35000:
        return round(cost, -2)
    elif 35000 < cost:
        return round(cost, -3)


def format_cost(cost: float) -> str:
    """
    Formats input float into a nice and readable string
    17700.0 -> '17 700.00'
    :param cost: (float)
    :return: (str) Formatted string
    """
    return '{:,.2f}'.format(cost).replace(',', ' ')

