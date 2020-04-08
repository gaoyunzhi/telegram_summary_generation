#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
import threading
from bs4 import BeautifulSoup
from telegram_util import log_on_fail
from telegram.ext import Updater
import cached_url

with open('credential') as f:
    bot = Updater(yaml.load(f, Loader=yaml.FullLoader)['bot_token'], 
        use_context=True).bot

last_run = 0

def readPool():
    with open('pool') as f:
        return [x.strip() for x in f.read().split() if x.strip()]


with open('DB') as f:
    DB = yaml.load(f, Loader=yaml.FullLoader)

def getParsedText(text):
    result = ''
    for item in text:
        if item.name in set(['br']):
            result += '\n'
            continue
        if item.name == 'i':
            if item.text:
                result += '<i>' + item.text + '</i>'
            continue
        if item.name == 'a':
            telegraph_url = export_to_telegraph.export(item['href'])
            if telegraph_url:
                item['href'] = telegraph_url
                del item['rel']
                if 'http' in item.text:
                    item.contents[0].replaceWith(telegraph_url)
        if str(item).startswith('原文') and 'telegra' in result:
            return result
        result += str(item)
    return result

def keyMatch(chat_id, author, result):
    if (not isinstance(chat_id, int)) or (not DB[chat_id]):
        return False
    for key in DB[chat_id]:
        if key in str(author) or key in str(result):
            return True
    return False

def intersect(l1, l2):
    return set(l1).intersection(l2)

@log_on_fail(debug_group)
def loopImp():
    if time.time() - last_run < 20 * 60 * 60:
        return
    last_run = time.time()
    for name in readPool():
        soup = getSoup('https://telete.in/s/' + item)
        for msg in soup.find_all('div', class_='tgme_widget_message_bubble'):
            text = msg.find('div', class_='tgme_widget_message_text')
            if (not text) or (not text.text):
                continue
            hash_value = hashlib.sha224(str(text.text).encode('utf-8')).hexdigest()
            if hash_value in hashes:
                continue
            author = msg.find('div', class_='tgme_widget_message_author')
            result = getParsedText(text)
            matches = [chat_id for chat_id in DB if keyMatch(chat_id, str(author), result)]
            if intersect(matches, PAUSED):
                continue
            for chat_id in matches:
                try:
                    bot.send_message(chat_id=chat_id, text=result, parse_mode='HTML')
                    time.sleep(1)
                except Exception as e:
                    print(chat_id)
                    print(e)                        
                    print(result)
            hashes.add(hash_value)
            saveHashes(hash_value)

def loop():
    loopImp()
    threading.Timer(60 * 10, loop).start() 

if not 'once' in sys.argv:
    threading.Timer(1, loop).start()
else:
    loopImp()