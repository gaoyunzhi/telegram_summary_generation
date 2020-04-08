#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
import threading
from bs4 import BeautifulSoup
from telegram_util import log_on_fail
from telegram.ext import Updater
import cached_url
from message import Message

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

def getSoup(name):
    return BeautifulSoup(cached_url.get('https://telete.in/s/' + name), 'html.parser')

def getMessages():
    for name in readPool():
        soup = getSoup(name)
        for msg in soup.find_all('div', class_='tgme_widget_message'):
            msg = Message(msg)
            if not msg.text:
                continue
            text = msg.find('div', class_='tgme_widget_message_text')
            if (not text) or (not text.text):
                continue
            hash_value = hashlib.sha224(str(text.text).encode('utf-8')).hexdigest()
            if hash_value in hashes:
                continue
            author = msg.find('div', class_='tgme_widget_message_author')
            result = getParsedText(text)

@log_on_fail(debug_group)
def loopImp():
    if time.time() - last_run < 20 * 60 * 60:
        return
    last_run = time.time()
    messages = getMessages()
    # match with subscription

def loop():
    loopImp()
    threading.Timer(60 * 10, loop).start() 

if not 'once' in sys.argv:
    threading.Timer(1, loop).start()
else:
    loopImp()