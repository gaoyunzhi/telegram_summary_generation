#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
import threading
from bs4 import BeautifulSoup
from telegram_util import log_on_fail, matchKey
from telegram.ext import Updater
import cached_url
from message import Message
import sys

item_limit = 20

def getFile(name):
    with open(name) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

bot = Updater(getFile('credential')['bot_token'], use_context=True).bot
debug_group = bot.get_chat(-1001198682178)

last_run = 0

def readPool():
    with open('pool') as f:
        return [x.strip() for x in f.read().split() if x.strip()]

def getSoup(name):
    return BeautifulSoup(cached_url.get('https://telete.in/s/' + name), 'html.parser')

def getRawList(messages, config, keys):
    raw_list = []
    for msg in messages.values():
        if msg.match(keys):
            raw_list.append([msg.getWeight(), msg])
    raw_list.sort(reverse=True)
    if 'test' in sys.argv:
        if len(raw_list) > item_limit or not raw_list:
            print('warning, %s matched %d item' % (str(keys), len(raw_list)))
    raw_list = [y.getText(config) for x, y in raw_list[:item_limit]]
    if config == 'cn':
        raw_list = [x for x in raw_list 
            if not matchKey(x, ['youtu', 'twitter', 't.co'])]
    return raw_list

def getMsg(raw_list):
    return '每日文章精选' + '\n\n' + \
        '\n\n'.join([x.strip().replace('\n\n', '\n') for x in raw_list])

def sendMsg(messages, name, config, keys):
    raw_list = getRawList(messages, config, keys)
    if not raw_list:
        return
    if 'debug' in sys.argv:
        target = -1001198682178
    else:
        target = '@' + name
    if config == 'cn':
        bot.send_message(target, getMsg(raw_list), 
            disable_web_page_preview=True) 
        return
    bot.send_message(target, getMsg(raw_list), 
        disable_web_page_preview=True, parse_mode='html') 

def getMessages():
    messages = {}
    for name in readPool():
        soup = getSoup(name)
        for msg in soup.find_all('div', class_='tgme_widget_message'):
            msg = Message(msg)
            if msg.getTitle() and msg.isRecent():
                messages[msg.getID()] = msg
    return messages

@log_on_fail(debug_group)
def loopImp():
    global last_run
    if time.time() - last_run < 20 * 60 * 60:
        return
    last_run = time.time()
    messages = getMessages()
    configs = getFile('config')
    for name, keys in getFile('subscription').items():
        sendMsg(messages, name, configs[name], keys)

def loop():
    loopImp()
    threading.Timer(60 * 10, loop).start() 

if not 'once' in sys.argv:
    threading.Timer(1, loop).start()
else:
    loopImp()