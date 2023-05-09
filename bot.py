import datetime
import random
from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from config import bot_token, access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from bd import create_tables, drop_tables, Client, Person, seen_person


engine = create_engine('postgresql://postgres:Anast29123@localhost:5432/VKinder')
if not database_exists(engine):
    create_database(engine)

drop_tables(engine)
create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

vk_user = vk_api.VkApi(token=access_token)
vk_bot = vk_api.VkApi(token=bot_token)
longpoll = VkLongPoll(vk_bot)


def write_msg( user_id, message, photos=None):
    params = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
    if photos:
        attachment = photos
        print(attachment)
    return vk_bot.method('messages.send', params)


def check_info(user_id):
    user_info = {}
    response = vk_user.method('users.get', {'user_id': user_id,
                                                 'v': 5.131,
                                                 'fields': 'first_name, last_name, bdate, sex, city'})
    if response:
        for key, values in response[0].items():
            if key == 'is_closed' or key == 'can_access_closed':
                break
            elif key == 'city':
                user_info[key] = values['id']
            else:
                user_info[key] = values
    else:
        return False
    return user_info

def check_missing_info(user_info):
    if user_info:
        for item in ['bdate', 'city']:
            if not user_info.get(item):
                user_info[item] = ''
        if user_info.get('bdate'):
            if len(user_info['bdate'].split('.')) != 3:
                user_info[item] = ''
        return user_info
    write_msg(user_info['id'], 'Ошибка', None)
    return False

def check_bdate(user_info, user_id):
    if user_info:
        for item_dict in [user_info]:
            if len(item_dict['bdate'].split('.')) != 3:
                write_msg(user_id, f'Введите дату рождения в формате ХХ.ХХ.ХХХХ: ', None)
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        user_info['bdate'] = event.text
                        return user_info
            else:
                return user_info
    write_msg(user_info['id'], 'Ошибка', None)
    return False

def get_city(city_user):
    values = {'country_id': 1,
        'q': f'{city_user}',
        'count': 50,
        'need_all': 0}
    response = vk_user.method('database.getCities', values=values)
    if response:
        if response.get('items'):
            return response.get('items')
        write_msg(city_user, 'Ошибка ввода города', None)
        return False

def check_city(user_info, user_id):
    if user_info:
        for item in [user_info]:
            if item['city'] == '':
                write_msg(user_id, f'Введите название города, например: Краснодар', None)
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        user_info['city'] = get_city(event.text)[0]['id']
                        return user_info
            else:
                return user_info
    write_msg(user_info['id'], 'Неверно указан город! Введите правильное название:', None)
    return False


def get_age(user_info):
    if user_info:
        for key, value in user_info:
            user_info['age'] = datetime.datetime.now().year - int(user_info['bdate'][-4:])
            return user_info
    write_msg(user_info['id'], 'Ошибка', None)
    return False


def looking_for_persons(user_info):
    # ищет кандидатов
    if user_info['age'] - 5 < 18:
        age_from = 18
    else:
        age_from = user_info['age'] - 5
        age_to = user_info['age'] + 5

    profiles = vk_user.method('users.search', {'age_from': age_from,
                                                    'age_to': age_to,
                                                    'sex': 3 - user_info['sex'],
                                                    'city': user_info['city'],
                                                    'status': 1 or 6,
                                                    'has_photo': 1,
                                                    'count': 50,
                                                    'offset':0,
                                                    'v': 5.131})

    if profiles:
        if profiles.get('items'):
            return profiles.get('items')
        write_msg(user_info['id'], 'Ошибка поиска', None)
        return False


def photos_get( user_id):
    # получение фото
    photo_param = {'owner_id': user_id, 'album_id': 'profile',
                   'extended': '1', 'count': '20'}
    photos = vk_user.method('photos.getAll', photo_param)
    if photos:
        if photos.get('items'):
            return photos.get('items')
        write_msg(user_id, 'Ошибка', None)
        return False

def sort_likes( photos_dict):
    photos_likes_list = []

    for photo in photos_dict:
        likes = photo.get('likes')
        photos_likes_list.append([photo.get('user_id'), photo.get('id'), likes.get('count')])
    photos_by_likes_list = sorted(photos_likes_list, key=lambda x: x[2], reverse=True)
    return photos_by_likes_list

def get_photos_list( sort_list):
    photos_list = []
    count = 0
    for photos in sort_list:
        photos_list.append('photo' + str(photos[0]) + '_' + str(photos[1]))
        count += 1
        if count == 3:
            return photos_list

def get_users_list( user_info, user_id):
    person_list = []
    if user_info:
        for person in user_info:
            if person.get('is_closed') == False:
                user_info.append(
                    {'first_name': person.get('first_name'), 'last_name': person.get('last_name'),
                     'id': person.get('id'), 'vk_link': 'vk.com/id' + str(person.get('id')),
                     'is_closed': person.get('is_closed')
                     })
            else:
                continue
        return person_list
    write_msg(user_id, 'Ошибка при поиске', None)
    return False

def user_data( user_id):
    user_data = [get_age(check_city(check_bdate(check_missing_info(check_info(user_id)), user_id), user_id))]
    if user_data:
        return user_data
    write_msg(user_id, 'Ошибка', None)
    return False

def persons_data(user_id):
    persons_data = get_users_list(looking_for_persons(get_age(check_city(check_bdate(check_missing_info(check_info(user_id)), user_id), user_id))),
        user_id)
    if persons_data:
        return persons_data
    write_msg(user_id, 'Ошибка', None)
    return False


def get_random_user(user_info, user_id):
    if user_info:
        return random.choice(user_info)
    write_msg(user_id, 'Ошибка', None)
    return False


def add_table(user_info):
    if user_info:
        for item in user_info:
            user_record = Session.query(Client).filter_by(user_id=item['id']).scalar()
            if not user_record:
                user_record = Client(id=item['id'])
            Session.add(user_record)
            Session.commit()
        return True
    write_msg(user_info['id'], 'Ошибка', None)
    return False


def add_user_table(user_info, user_id):
    try:
        for item in user_info:
            users_record = Session.query(Person).filter_by(id=item['id']).scalar()
            if not users_record:
                users_record = Person(id=item['id'])
            Session.add(users_record)
            Session.commit()
        return True
    except TypeError:
        Session.rollback()
        write_msg(user_id, 'Ошибка', None)
        return False


def seen_person(random_choice):
    for item in random_choice:
        random_user_record = Session.query(seen_person).filter_by(id=item['id']).scalar()
        if not random_user_record:
            random_user_record = seen_person(id=item['id'], first_name=item['first_name'],
                                             last_name=item['last_name'],
                                             vk_link=item['vk_link'])
        Session.add(random_user_record)
    return Session.commit()
