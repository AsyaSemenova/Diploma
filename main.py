import datetime
import random
from random import randrange
import vk_api
from vk_api import longpoll

from config import *
from vk_api.longpoll import VkLongPoll, VkEventType


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
        # записывает инфу
        try:
            profiles = self.vk_bot.method('users.search',
                                           {'city_id': city_id,
                                            'age_from': age_from,
                                            'age_to': age_to,
                                            'sex': sex,
                                            'count': 50,
                                            'status': 1 or 6,
                                            'offset': offset
                                            })
        except KeyError:
            return
        profiles = profiles['items']
        result = []
        for profile in profiles:
            if profile['is_closed'] == False:
                result.append({'name': profile['first_name'] + ' ' + profile['last_name'],
                               'id': profile['id'] })

        return result


    def photos_get(self, user_id):
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

    def show(self,profile, photos_results):
        person_age = self.get_age()
        age = f", {person_age} {('год', ('лет', 'года') [0 < person_age % 10 < 5])[person_age % 10 != 1]}"
        return f"{profile['first_name']} {age}\nhttps://vk.com/id{profile['user_id']}", photos_results

    def main(self):
        # create_tables(bot)
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                request = event.text.lower()
                user_id = event.user_id
                if request =='привет' or 'начать':
                    Bot.write_msg(user_id,f'Привет! я помогу найти тебе пару!')
                elif request == 'поиск':
                    Bot.get_age_of_user(user_id)
                    Bot.get_city(user_id)
                    Bot.looking_for_persons(user_id)
                    Bot.show(user_id)
                else:
                    Bot.write_msg(user_id, f'{Bot.name(user_id)} Бот готов, наберите: \n '
                                          f' "Поиск" - для поиска кандидатов. \n')


bot = Bot()
