from bot import *


def main():
    if not database_exists(engine.url):
        create_database(engine.url)
    create_tables(engine)
    list_chosen = []
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                user_id = event.user_id
                request = event.text.lower()
                if request == 'привет':
                    add_table(user_data(user_id))
                    write_msg(user_id,
                                   f"Привет, это бот VKinder!\n"
                                   f"Бот осуществляет поиск подходящей по критериям пары.\n"
                                   f"Чтобы начать поиск введите команду 'поиск'.\n"
                                   f"Для окончания работы с ботом введите команду 'пока'.", None)
                elif request in ['поиск', 'да']:
                    random_choice = []
                    get_random_user_data = get_random_user(persons_data(user_id), user_id)
                    random_choice.append(get_random_user_data)
                    add_user_table([get_random_user_data], user_id)
                    if random_choice[0]['id'] not in list_chosen:
                        write_msg(user_id,
                                       {random_choice[0]['first_name'] + ' ' + random_choice[0]['last_name']},
                                       {' '.join(get_photos_list(sort_likes(photos_get(random_choice[0]['id']))))})
                        write_msg(user_id, f"Ссылка на профиль:{random_choice[0]['vk_link']}", None)
                        write_msg(user_id,  f"Продолжить поиск? Напишите дa или нет.\n", None)
                    else:
                        continue

                elif request in ['пока', 'нет']:
                    write_msg(user_id, "До новых встреч!", None)
                    break
                else:
                    write_msg(user_id, "Не понял. Напишите по-другому.", None)


main()
