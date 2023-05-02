import datetime
from datetime import date, time
import random
from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from config import *
import bd
from bd import create_tables, Client, Person, session, Seen_persones

class Bot:

    def __init__(self):
        self.vk_user = vk_api.VkApi(token=access_token)
        self.vk_user_api = self.vk_user.get_api()
        self.vk_bot = vk_api.VkApi(token=bot_token)
        self.vk_bot_api = self.vk_bot.get_api()
        self.longpoll = VkLongPoll(self.vk_bot)

        self.age_from = 0
        self.age_to = 0
        self.city_id = 0
        self.city_title = 0

    def write_msg(self, user_id, message, photos=None):
        params = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
        if photos:
            attachment = photos
            print(attachment)
        return self.vk_bot.method('messages.send', params)

    def name(self, user_id):
        # получаем имя
        user_info = self.vk_bot_api.users.get(user_id=user_id)
        try:
            name = user_info[0]['first_name']
            return name
        except KeyError:
            self.write_msg(user_id, "Ошибка")

    def sex_user(self, user_id):
        # пол
        users_sex = self.vk_user_api.users.get(user_id=user_id, fields="sex")
        if users_sex[0]['sex'] == 1:
            return 2
        elif users_sex[0]['sex'] == 2:
            return 1
        else:
            print("Ошибка")

    def input_looking_age(self, user_id, age):
        global age_from, age_to
        a = age.split("-")
        try:
            age_from = int(a[0])
            age_to = int(a[1])
            if age_from == age_to:
                self.write_msg(user_id, f' Ищем возраст {age_to}')
                return
            self.write_msg(user_id, f' Ищем возраст в пределах от {age_from} и до {age_to}')
            return
        except IndexError:
            age_to = int(age)
            self.write_msg(user_id, f' Ищем возраст {age_to}')
            return
        except NameError:
            self.write_msg(user_id, f' NameError! Введен неправильный числовой формат!')
            return
        except ValueError:
            self.write_msg(user_id, f' ValueError! Введен неправильный числовой формат!')
            return

    def get_years_of_person(self, bdate: str) -> object:
        bdate_splited = bdate.split(".")
        month = ""
        try:
            reverse_bdate = datetime.date(int(bdate_splited[2]), int(bdate_splited[1]), int(bdate_splited[0]))
            today = datetime.date.today()
            years = (today.year - reverse_bdate.year)
            if reverse_bdate.month >= today.month and reverse_bdate.day > today.day or reverse_bdate.month > today.month:
                years -= 1
        except IndexError:
            if bdate_splited[1] == "1":
                month = "января"
            elif bdate_splited[1] == "2":
                month = "февраля"
            elif bdate_splited[1] == "3":
                month = "марта"
            elif bdate_splited[1] == "4":
                month = "апреля"
            elif bdate_splited[1] == "5":
                month = "мая"
            elif bdate_splited[1] == "6":
                month = "июня"
            elif bdate_splited[1] == "7":
                month = "июля"
            elif bdate_splited[1] == "8":
                month = "августа"
            elif bdate_splited[1] == "9":
                month = "сентября"
            elif bdate_splited[1] == "10":
                month = "октября"
            elif bdate_splited[1] == "11":
                month = "ноября"
            elif bdate_splited[1] == "12":
                month = "декабря"
            return f'День рождения {int(bdate_splited[0])} {month}.'

    def get_age_of_user(self, user_id):
        try:
            info = self.vk_user_api.users.get(user_ids=user_id,fields="bdate",)[0]['bdate']
            if self.get_years_of_person(info) != None:
                num_age = self.get_years_of_person(info).split()[0]
                age_from = num_age
                age_to = num_age
                if num_age == "День":
                    print(f'Ваш {self.get_years_of_person(info)}')
                    self.write_msg(user_id,f'введите возраст поиска в формате : 21-35.')
                    for event in self.longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            age = event.text
                            return self.input_looking_age(user_id, age)
                return print(f' Ищем вашего возраста {age_to}')
        except KeyError:
            self.write_msg(user_id, 'введите возраст поиска в формате : 21-35.')
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    age = event.text
                    return self.input_looking_age(user_id, age)

    def get_city(self, user_id):
        self.write_msg(user_id,
                      f' Введите "Да" - поиск будет произведен в городе указанный в профиле.'
                      f' Или введите название города, например: Краснодар')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                city_user = event.text.lower()
                user_id = event.user_id
                if city_user == "да":
                    info = self.vk_user_api.users.get(user_id=user_id,fields="city")
                    city_id = info[0]['city']["id"]
                    city_title = info[0]['city']["title"]
                    return f' в городе {city_title}.'
                else:
                    cities = self.vk_user_api.database.getCities(
                        country_id=1,
                        q=city_user.capitalize(),
                        need_all=1,
                        count=50)['items']
                    for i in cities:
                        if i["title"] == city_user.capitalize():
                            city_id = i["id"]
                            city_title = city_user.capitalize()
                            return f' в городе {city_title}'

    def looking_for_persons(self, user_id):
        # ищет кандидатов
        global list_found_persons
        list_found_persons = []
        profiles = self.vk_user_api.users.search(
            city=self.city_id,
            hometown=self.city_title,
            sex=self.sex_user(user_id),
            status=1,
            age_from=self.age_from,
            age_to=self.age_to,
            has_photo=1,
            count=1000,)
        try:
            profiles = profiles['items']
        except KeyError:
            return

        result = []
        for profile in profiles:
            if profile['is_closed'] == False:
                result.append({'name': profile['first_name'] + ' ' + profile['last_name'],
                               'id': profile['id']})

        return result

    def photos_get(self, user_id):
        # получение фото
        photo_param = {'owner_id': user_id, 'album_id': 'profile',
                       'extended': '1', 'count': '20'}
        photos = self.vk_bot_api.method('photos.get', photo_param)
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
                photo_dict = {likes_count: photos_results[likes_count] for likes_count in
                              sorted(photos_results, reverse=True)}
                photos_results = list(photo_dict.values())[0:photos_count]
        return

    def show_all_users(self, user_id, persons):
        # найденные юзеры
        for person in persons:
            person_id = person['user_id']
            print(person_id)
            photos = self.photos_get(person_id)
            if photos:
                self.write_msg(user_id, *self.show(person))
                pair = session.query(person).filter(person.person_id == (person_id)).all()
                if not bool(pair):
                    self.add_to_bd(person)
                # добавляем в просмотренные
                self.add_to_seen(person['user_id'])
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        request = event.text.lower()
                        user_id = event.user_id
                if request == 'Дальше':
                    continue
                elif request == 'Стоп':
                    self.write_msg(user_id, "Пока")
                return True

    def show(self, user_id, profile, photos_results):
        # выводит инфу о пользователе
        person_age = self.get_age_of_user(user_id)
        age = f", {person_age} {('год', ('лет', 'года')[0 < person_age % 10 < 5])[person_age % 10 != 1]}"
        return f"{profile['first_name']} {age}\nhttps://vk.com/id{profile['user_id']}", photos_results

    def add_to_bd(user_info, user_id):
        # добавление в бд
        client_bd = Client(client_id=user_id, first_name=user_info['first_name'], bdate=user_info.get('bdate', 0),
                           sex=user_info['sex'], city=user_info['city'], age=user_info['age'])
        session.add(client_bd)
        session.commit()

    def add_to_seen(person_id, user_id):
        person = Seen_persones(seen_person_id=person_id, client_id_client=user_id, liked=False)
        session.add(person)
        session.commit()

    def get_info_from_bd(user_id):
        # достает инфу
        info = {}
        try:
            info['user_id'] = session.query(Client.user_id).filter(Client.user_id == user_id).all()[0][0]
            info['first_name'] = session.query(Client.first_name).filter(Client.user_id == user_id).all()[0][0]
            info['bdate'] = session.query(Client.bdate).filter(Client.user_id == user_id).all()[0][0]
            info['sex'] = session.query(Client.sex).filter(Client.user_id == user_id).all()[0][0]
            info['city'] = session.query(Client.city).filter(Client.user_id == user_id).all()[0][0]
            info['age'] = session.query(Client.age).filter(Client.user_id == user_id).all()[0][0]
        except:
            pass
        return info

    def add_person_to_bd(person):
        try:
            person_bd = Person(person_id=person['user_id'], name=person['first_name'], bdate=person['bdate'],
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
                if request == 'привет' or request == 'начать':
                    self.write_msg(user_id, f'{self.name(user_id)}, привет! я помогу найти тебе пару!')
                elif request == 'поиск':
                    self.get_age_of_user(user_id)
                    self.get_city(user_id)
                    self.looking_for_persons(user_id)
                elif request == 'дальше':
                    if self.show_all_users() != 0:
                        self.show(user_id)
                    else:
                        self.write_msg(user_id, f'{self.name(user_id)}, наберите "Поиск"')

                else:
                    self.write_msg(user_id, f'{self.name(user_id)}, бот готов, наберите: \n '
                                            f' "Поиск" - Поиск людей. \n')

if __name__ == '__main__':
    bot = Bot()
    bot.main()

