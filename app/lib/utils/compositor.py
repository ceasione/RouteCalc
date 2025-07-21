
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


class TelegramMessageComposer:

    def __init__(
        self,
        intent: str,
        url: str,
        ip: str,
        calculation: Optional[CalculationDTO] = None,
        phone_num: Optional[str] = None,
        blacklisted: bool = False,
    ):
        self.intent = intent
        self.calculation = calculation
        self.url = url
        self.ip = ip
        self.phone_num = phone_num
        self.blacklisted = blacklisted

    def __str__(self):

        if self.calculation is None:
            raise ValueError('Calculation DTO is required to generate telegram msg')

        blacklisted = '*BLACKLISTED*' if self.blacklisted else ''

        intents = {
            'calc': 'Просчет',
            'callback': 'Клиент нажал Перезвонить',
            'acquire': 'Просчет без номера'}

        intent_text = intents.get(self.intent, 'Unknown intent')

        if self.calculation.is_price_per_ton:
            price_value = self.calculation.price_per_ton
            price_tag = 'за тонну'
        else:
            price_value = self.calculation.price
            price_tag = ''

        price = f'{price_value} {self.calculation.currency} {price_tag}'.strip()

        phone = f'Телефон клиента: +{self.phone_num}' if self.phone_num else ''

        fstring = f'''
            {blacklisted}
            
            {intent_text}
            Lang: {"ru" if self.calculation.locale == 'ru_UA' else "ua"}
            Page URL: `{self.url}`

            IP: [{self.ip}](http://ip-api.com/line/{self.ip})

            {self.calculation.place_a_name} - {self.calculation.place_b_name}

            [Google Maps]({self.calculation.map_link})

            Расчет: *{self.calculation.place_chain}*
            Расстояние: {self.calculation.distance} км
            [Google Maps]({self.calculation.chain_map_link})

            Авто: {self.calculation.transport_name}
            Цена: {price}, ({self.calculation.price_per_km} за км):
            Currency: {self.calculation.currency_rate}
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

