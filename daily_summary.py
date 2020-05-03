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
import random
import requests
import tweepy

item_limit = 10

def getFile(name):
    with open(name) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

credential = getFile('credential')

auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
auth.set_access_token(credential['twitter_access_token'], credential['twitter_access_secret'])
api = tweepy.API(auth)

bot = Updater(credential['bot_token'], use_context=True).bot
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
            raw_list.append((msg.getTime() + random.random(), msg))
    raw_list.sort(reverse=True)
    raw_list = [y.getText(config) for x, y in raw_list[:item_limit * 5]]
    if config in ['cn', 'jianshu']:
        raw_list = [x for x in raw_list if not matchKey(str(x), [
                'youtu', 'twitter', 't.co', 'bbc.in', 'instagram',
            ]) and len(x.split('http')[0]) < 500]
    return raw_list[:item_limit]

def getMsg(raw_list):
    return '每日文章精选' + '\n\n' + \
        '\n\n'.join([x.strip().replace('\n\n', '\n') for x in raw_list])

def sendJianshu(messages, keys):
    # I think I need cookiejar
    raw_list = getRawList(messages, 'jianshu', keys)
    s = requests.Session()
    cookie_obj = requests.cookies.create_cookie(domain='www.jianshu.com',
        name='COOKIE_NAME',value=getFile('jianshu_cookie'))
    s.cookies.set_cookie(cookie_obj)
    headers = {}
    headers['method'] = 'POST'
    headers['accept'] = 'application/json'
    headers['content_type'] = 'application/json; charset=utf-8'
    headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'
    data = {'notebook_id': "1870443", 'title': "每日文章精选", 'at_bottom': False}
    r = s.post('https://www.jianshu.com/author/notes', headers=headers, 
        data = data)
    note_id = r.json()['id']
    print(note_id)
    r = s.get('https://www.jianshu.com/author/notes/%d/content' % note_id, headers = headers)
    print(r, r.content)
    # getMsg(raw_list)
    headers['referer'] = 'https://www.jianshu.com/writer'
    headers['method'] = 'PUT'   
    headers['origin'] = 'https://www.jianshu.com'
    headers['authority'] = 'www.jianshu.com'
    headers['path'] = '/author/notes/%d' % note_id
    data = {'id': note_id,  'autosave_control': 1, 'content': '<p>123</p>','title': '1234'}
    r = s.put('https://www.jianshu.com/author/notes/%d' % note_id, headers=headers, 
        data = data)
    print(r, r.reason)
    r = s.put('https://www.jianshu.com/author/notes/%d/publicize' % note_id, headers=headers)
    print(r, r.reason)

def sendMsg(messages, name, config, keys):
    raw_list = getRawList(messages, config, keys)
    if 'debug' in sys.argv:
        target = -1001198682178
    else:
        target = '@' + name
    if config == 'cn':
        r = bot.send_message(target, getMsg(raw_list), 
            disable_web_page_preview=True) 
    else:
        r = bot.send_message(target, getMsg(raw_list), 
            disable_web_page_preview=True, parse_mode='html')
    if name == 'daily_read' or 'debug' in sys.argv:
        link = 'https://t.me/%s/%d' % (name, r.message_id)
        api.update_status(link)
    #     sendJianshu(messages, keys)

def getMessages():
    messages = {}
    for name in readPool():
        soup = getSoup(name)
        for msg in soup.find_all('div', class_='tgme_widget_message'):
            msg = Message(msg)
            if msg.getTitle():
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

if 'once' not in sys.argv and 'debug' not in sys.argv:
    threading.Timer(1, loop).start()
else:
    loopImp()