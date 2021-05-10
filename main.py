import os
from datetime import datetime
from math import gcd
import requests
import schedule
import telebot
from bs4 import BeautifulSoup

name = ''
url = ''
period = None
timeformat = "%Y-%m-%d %H:%M:%S"

bot = telebot.TeleBot('token')


def get_gcd():
    with open('system_info.txt') as file:
        return int(file.readline())


def add_user(userid):
    temp = {}
    with open('system_info.txt') as file:
        file.readline()
        for i in file.readlines():
            key, val = i.strip().split(':')
            temp[key] = val
    temp[userid] = 0
    with open('system_info.txt', 'w') as file:
        file.readline()
        for key, val in temp.items():
            file.write('{}:{}\n'.format(key, val))


def update_gcd(newgcd):
    with open('system_info.txt', 'r') as file:
        lines = file.readlines()
    os.remove('system_info.txt')
    with open('system_info.txt', 'w') as file:
        file.write(str(newgcd))
        file.writelines(lines[1:])


def get_count(userid):
    temp = {}
    with open('system_info.txt') as file:
        file.readline()
        for i in file.readlines():
            key, val = i.strip().split(':')
            temp[key] = val
    return temp[userid]


def change_count(userid, delta):
    temp = {}
    with open('system_info.txt') as file:
        file.readline()
        for i in file.readlines():
            key, val = i.strip().split(':')
            temp[key] = val
    # res = temp[userid]
    temp[userid] += delta
    # with open('system_info.txt', 'w') as file:
    #     file.readline()
    #     for key, val in temp.items():
    #         file.write('{}:{}\n'.format(key, val))
    # return res


def parse(checker_url):
    page = requests.get(checker_url)
    if page.status_code == 200:
        return -1
    soup = BeautifulSoup(page.text, 'html.parser')
    content = soup.text
    return content


def get_del_checker_number(message):
    ind = int(message.text) - 1
    userid = str(message.from_user.id)
    c = get_count(userid)
    change_count(userid, -1)
    if os.path.isfile(userid + '_' + str(ind) + '.txt'):
        os.remove(userid + '_' + str(ind) + '.txt')
    else:
        bot.send_message(message.chat.id, 'Такого чекера не существует.')
    for i in range(ind + 1, c):
        os.rename(userid + '_' + str(i) + '.txt', userid + '_' + str(i - 1) + '.txt')
    gc = -1
    for i in range(c - 1):
        with open(userid + '_' + str(i) + '.txt', 'r') as file:
            cur = int(file.readline().split()[2])
            gc = cur if gc == -1 else gcd(cur, gc)
    update_gcd(gc)
    gc = get_gcd()
    # bot.register_next_step_handler(message, get_command)
    schedule.every(gc).minutes.do(checking)


def get_checker_name(message):
    global name
    name = message.text
    bot.send_message(message.chat.id, 'Введите url страницы')
    bot.register_next_step_handler(message, get_url)


def get_url(message):
    global url
    url = message.text
    bot.send_message(message.chat.id, 'Введите период чекинга в формате чч:мм')
    bot.register_next_step_handler(message, get_period)


def get_period(message):
    global period
    strperiod = message.text
    period = datetime.datetime.strptime(strperiod, '%H:%M')
    userid = str(message.from_user.id)
    create_checker(message, userid)


def create_checker(message, userid):
    global name, url, period
    c = change_count(userid, 1)
    minutes = period.hour * 60 + period.minute
    content = parse(url)
    with open('system_info.txt', 'r') as file:
        gc = int(file.readline())
    if gc == -1:
        gc = minutes
    else:
        gc = gcd(gc, minutes)
    update_gcd(gc)
    if content == -1:
        bot.send_message(message.chat.id, 'Не удалось подключиться')
    else:
        datenow = datetime.datetime.now().strftime(timeformat)
        with open(userid + '_' + str(c) + '.txt', 'w') as file:
            file.write(name + '#' + url + '#' + minutes + '#' + datenow)
            file.write(content)
    gc = get_gcd()
    schedule.every(gc).minutes.do(checking)


def check(message, file, c):
    info = file.readline().split(sep='#')
    curname = info[0]
    cururl = info[1]
    minutes = int(info[2])
    datelast = info[3]
    datetimelast = datetime.strptime(datelast, timeformat)
    datetimenow = datetime.now()
    difdate = datetimenow - datetimelast
    difminutes = difdate.second // 60
    if difminutes >= minutes:
        newcontent = parse(cururl)
        if newcontent != -1:
            lastcontent = file.readline()
            if lastcontent != newcontent:
                bot.send_message(message.chat.id, 'Изменения в чекере с именем ' + curname + '.\nЕго номер - ' + str(
                    c) + ';\nURL - ' + str(cururl) + '.')
                lastcontent = newcontent
    userid = message.from_user.id
    os.remove(userid + '_' + str(c) + '.txt')
    datenow = datetimenow.strftime(timeformat)
    with open(userid + '_' + str(c) + '.txt', 'w') as file:
        file.write(curname + '#' + cururl + '#' + minutes + '#' + datenow)
        file.write(lastcontent)


def checking(message):
    with open('system_info.txt', 'r') as file:
        lines = file.readlines()
    with open('temp.txt', 'w') as file:
        file.writelines(lines[1:])
    temp = {}
    with open('system_info.txt') as file:
        file.readline()
        for i in file.readlines():
            key, val = i.strip().split(':')
            temp[key] = val
    for key, value in temp.items():
        userid = key
        c = int(value)
        for i in range(c):
            with open(userid + '_' + str(i) + '.txt', 'r') as file:
                check(message, file, i)
    # bot.register_next_step_handler(message, get_command)





@bot.message_handler(content_types=['text'])
def handler(message):
    textt = message.text
    if textt == '/newchecker':
        bot.send_message(message.chat.id, 'Введите название чекера')
        # bot.register_next_step_handler(message, get_checker_name)
    elif textt == '/showcheckers':
        userid = str(message.from_user.id)
        c = get_count(userid)
        if c == 0:
            bot.send_message(message.chat.id, 'Чекеров нет.')
        else:
            for i in range(c):
                with open(userid + '_' + str(i) + '.txt', 'r') as file:
                    curname, cururl, minutes, lastdate = map(str, file.readline().split(sep='#'))
                    minutes = int(minutes)
                    text = str(i + 1) + ') ' + 'Имя чекера - ' + str(
                        curname) + '\nURL - ' + cururl + '\nПериод - ' + minutes + '\nДата последней проверки - ' + datetime + '. '
                    bot.send_message(message.chat.id, text)
        # bot.register_next_step_handler(message, get_command)
    elif textt == '/deletechecker':
        bot.send_message(message.chat.id, 'Введите номер чекера')
        # bot.register_next_step_handler(message, get_del_checker_number)

@bot.message_handler(commands=['/start'])
def start_command(message):
    bot.send_message(message.chat.id, 'Я чекер сайтов.')
    bot.register_next_step_handler(message, handler)


bot.polling(none_stop=True, interval=0)
