import datetime
import random
from random import randrange
import vk_api
from vk_api import longpoll

from config import *
from vk_api.longpoll import VkLongPoll, VkEventType
import bd
from bd import create_tables, client, person, session, seen_persones


class Bot:

    def __init__(self):
        self.vk_bot = vk_api.VkApi(token=bot_token)
        self.vk_bot_api = self.vk_bot.get_api()
        self.longpoll = VkLongPoll(self.vk_bot)

    def write_msg(self, user_id, message, photos=None):
        params = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
        if photos:
            attachment = photos
            print(attachment)
        return self.vk_bot.method('messages.send', params)

    def name(self, user_id):
        # получаем имя
        user_info = self.vk_bot_api.get(user_id=user_id)
        try:
            name = user_info[0]['first_name']
            return name
        except KeyError:
            self.write_msg(user_id, "Ошибка")

    def sex_user(self, user_id):
        # пол
        users_sex = self.vk_bot.users.get(user_id=user_id, fields="sex")
        if users_sex[0]['sex'] == 1:
            return 2
        elif users_sex[0]['sex'] == 2:
            return 1
        else:
            print("Ошибка")

    def get_bdate(self, user_id, field):
        # дата рождения
        birthday = {'bdate': 'вашу дату рождения в формате XX.XX. XXXX'}
        self.write_msg(user_id, f'Уточните некоторые параметры поиска: \n{birthday[field]}')
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if field == 'bdate':
                        if len(event.text.split('.')) != 3:
                            self.write_msg(user_id, 'Неверно указана дата рождения')
                            return False
                        return event.text

    def get_age(date):
        # высчитываем возраст
        return datetime.datetime.now().year - int(date[-4:])

    def get_age_of_user(self, user_id, age):
        # возрастные рамки
        global age_from, age_to
        a = age.split("-")
        try:
            age_from = int(a[0])
            age_to = int(a[1])
            if age_from == age_to:
                self.write_msg(user_id, f' Ищем возраст {self.get_age(age_to)}')
                return
            self.write_msg(user_id, f' Ищем возраст в пределах от {age_from} и до {self.get_age(age_to)}')
            return
        except ValueError:
            self.write_msg(user_id, f' Ошибка!')
            return

    def get_city(self, user_id):
         #город
        global city_id, city_title
        self.write_msg(user_id, f' Введите "Да" - поиск будет произведен в городе указанный в профиле.'
                               f'Введите название города, например: Краснодар')
        for event in longpoll.listen():
             if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                 if event.lower == "да":
                     info = self.vk_bot.get(user_id=user_id, fields="city")
                     city_id = info[0]['city']["id"]
                     city_title = info[0]['city']["title"]
                 else:
                     city = self.vk_bot.database.getCities(
                         country_id=1,
                         q=event.capitalize(),
                         need_all=1,
                         count=1)['items']
                     for i in city:
                         if i["title"] == event.capitalize():
                             city_id = i["id"]
                             city_title = event.capitalize()
                         else:
                             self.write_msg('Ошибка')

    def looking_for_persons(self, user_id, city_id, age_from, age_to, sex, offset=None):
        # ищет кандидатов
        profiles = self.vk_bot.method('users.search',
                                           {'city_id': city_id,
                                            'age_from': age_from,
                                            'age_to': age_to,
                                            'sex': sex,
                                            'count': 50,
                                            'status': 1 or 6,
                                            'offset': offset
                                            })
        try :
            profiles = profiles['items']
        except KeyError:
            return

        result = []
        for profile in profiles:
            if profile['is_closed'] == False:
                result.append({'name': profile['first_name'] + ' ' + profile['last_name'],
                               'id': profile['id'] })

        return result


    def photos_get(self, user_id):
        # получение фото
        photo_param = {'owner_id': user_id, 'album_id': 'profile',
                            'extended': '1', 'count': '20'}
        photos = self.vk_bot.method('photos.get', photo_param)
        photos_count = 3 if photos.get('count') >= 3 else photos.get('count')
        try:
            photos = photos['items']
        except KeyError:
            return
        photos_results = {}
        if photos_count:
            for photo in photos:
                    photo_user = photo.get('id')
                    likes = photo.get('likes', {}).get('count')
                    photos_results[likes] = f'photo{user_id}_{photo_user}'
                    photo_dict = {likes_count: photos_results[likes_count] for likes_count in sorted(photos_results, reverse=True)}
                    photos_results = list(photo_dict.values())[0:photos_count]
        return

    def show_all_users(self, user_id, persons):
        #найденные юзеры
        for person in persons:
            person_id = person['user_id']
            print(person_id)
            photos = self.photos_get(person_id)
            if photos:
                self.write_msg(user_id, *self.show(person, photos))
                pair = session.query(person).filter(person.person_id == (person_id)).all()
                if not bool(pair):
                    self.add_to_bd(person)
                # добавляем в просмотренные
                self.add_to_seen(person['user_id'], user_id)
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        request = event.text.lower()
                        user_id = event.user_id
                if request == 'Дальше':
                    continue
            elif request == 'Стоп':
                self.write_msg(user_id, "Пока")
                return True


    def show(self,profile, photos_results):
        # выводит инфу о пользователе
        person_age = self.get_age()
        age = f", {person_age} {('год', ('лет', 'года') [0 < person_age % 10 < 5])[person_age % 10 != 1]}"
        return f"{profile['first_name']} {age}\nhttps://vk.com/id{profile['user_id']}", photos_results

    def add_to_bd(user_info, user_id):
        # добавление в бд
        user_bd = client(user_id=user_id, first_name=user_info['first_name'], bdate=user_info.get('bdate', 0),
                       sex=user_info['sex'], city=user_info['city'], age=user_info['age'])
        session.add(user_bd)
        session.commit()

    def add_to_seen(person_id, user_id):
        person = seen_persones(seen_person_id=person_id, user_id_user=user_id, liked=False)
        session.add(person)
        session.commit()

    def get_info_from_bd(user_id):
        # достает инфу
        info = {}
        try:
            info['user_id'] = session.query(client.user_id).filter(client.user_id == user_id).all()[0][0]
            info['first_name'] = session.query(client.first_name).filter(client.user_id == user_id).all()[0][0]
            info['bdate'] = session.query(client.bdate).filter(client.user_id == user_id).all()[0][0]
            info['sex'] = session.query(client.sex).filter(client.user_id == user_id).all()[0][0]
            info['city'] = session.query(client.city).filter(client.user_id == user_id).all()[0][0]
            info['age'] = session.query(client.age).filter(client.user_id == user_id).all()[0][0]
        except:
            pass
        return info

    def add_person_to_bd(person):
        try:
            person_bd = person(person_id=person['user_id'], name=person['first_name'], bdate=person['bdate'],
                               sex=person['sex'], city=person['city'])
            session.add(person_bd)
            session.commit()
        except:
            pass

    def main(self):
        create_tables(bd.engine)
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                request = event.text.lower()
                user_id = event.user_id
                if request =='привет' or 'начать':
                    self.write_msg(user_id,f'Привет! я помогу найти тебе пару!')
                elif request =='поиск':
                    self.get_age_of_user(user_id)
                    self.get_city(user_id)
                    self.looking_for_persons(user_id)
                elif request == 'Дальше':
                    if self.show_all_users() != 0:
                        self.show(user_id)
                    else:
                        self.write_msg(user_id, f' В начале наберите Поиск')

                else:
                    self.write_msg(user_id, f'{self.name(user_id)} Бот готов, наберите: \n '
                                      f' "Поиск" - Поиск людей. \n')

if __name__  == '__main__':
  bot = Bot()
  bot.main()
