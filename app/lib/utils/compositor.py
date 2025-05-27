
from app import settings
from app.lib.utils.DTOs import CalculationDTO
from textwrap import dedent

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

    fstring = f'''
        {calculation.place_a_name} - {calculation.place_b_name}
        Транспорт: {calculation.transport_name}
        {price}
        {SMS_TEXT_REDIAL_PHONE}
        
        https://intersmartgroup.com/
        
        Ефективність – наш стандарт. Довіряйте Inter Smart.'''

    return dedent(fstring).lstrip()


def generate_map_url(*args):
    if len(args) < 2:
        raise RuntimeError('Internal error 6')

    base = f'https://www.google.com.ua/maps/dir/'
    s = list()
    s.append(base)

    for place in args:
        s.append(f'{str(place.lat)},{str(place.lng)}/')
    return str().join(s)


def generate_place_chain(*args):

    if len(args) < 1:
        raise RuntimeError('Internal error 7')

    s = list()
    for place in args:
        s.append(place.name)
        s.append(' - ')
    s.pop()

    return str().join(s)


def compose_telegram(intent, calculation, url, ip, phone_num='#'):
    intent_dict = {
        'calc': 'Просчет',
        'callback': 'Клиент нажал Перезвонить',
        'acquire': 'Просчет без номера'
    }

    if calculation.is_price_per_ton:
        # s.append(str(rounded_cost) + '0')
        # returns format '10 700.68' https://stackoverflow.com/questions/13082620/
        price = f'{calculation.price_per_ton} {calculation.currency} за тонну'
    else:
        # s.append(str(__round_cost(details['cost'])) + '0')
        price = f'{calculation.price} {calculation.currency} {calculation.currency}'

    if phone_num is not None:
        phone = f'Телефон клиента: +{phone_num}'
    else:
        phone = ''

    fstring = f'''
        {intent_dict[intent]}
        Lang: {"ru" if calculation.locale == 'ru_UA' else "ua"}
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


def format_cost(cost: float) -> str:
    return '{:,.2f}'.format(__round_cost(cost)).replace(',', ' ')


def format_cost_per_ton(cpt: float) -> str:
    return '{:,.2f}'.format(__round_cost(cpt)).replace(',', ' ')
