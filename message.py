from bs4 import BeautifulSoup
import cached_url
import sys
from telegram_util import compactText, matchKey, clearUrl, cutCaption
from datetime import datetime, timedelta

def getCnLink(item):
	if 'telegra.ph' not in item['href']:
		return item['href']
	b = BeautifulSoup(cached_url.get(item['href'], 
		force_cache=True), 'html.parser')
	try:
		return b.find('address').find('a')['href']
	except Exception as e:
		if 'test' in sys.argv:
			print(e)
		return item['href']

def getTextCN(soup, config):
	new_soup = BeautifulSoup(str(soup), features='lxml')
	links = set()
	for x in new_soup.find_all('a'):
		link = compactText(clearUrl(getCnLink(x))) # 呵呵...
		if link in links or (links and x.text == 'source'):
			x.replace_with('')
		else:
			links.add(link)
			x['href'] = link
			c = 0
			for y in x:
				c += 1
				if c == 1:
					y.replace_with(link)
				else:
					y.replace_with('')
	if config == 'cn':
		result = compactText(new_soup.get_text(separator=' '))
		return result.strip().strip('|')
	return str(new_soup)

# TODO: may need timestamp info
class Message():
	def __init__(self, soup):
		self.soup = soup
		self.raw_text = soup.find('div', class_='tgme_widget_message_text') \
			or BeautifulSoup('', features='lxml')
		self.text_cn = '' # 墙内版本
		
	def getCnText(self, config):
		return getTextCN(self.raw_text, config)

	def getText(self, config):
		prefix = '【%s】\n' % self.getTitle() 
		if config == 'us':
			text = prefix + ''.join([str(x) for x in self.raw_text.children])
			return text.replace('<br/>', '\n')
		return prefix + self.getCnText(config).replace('\n\n', '\n')
		
	def getMsgPreview(self):
		preview = self.soup.find('a', class_='tgme_widget_message_link_preview')
		if preview:
			return preview.text

	def getTitle(self):
		title = self.soup.find('div', class_='link_preview_title')
		if title:
			return title.text
		try:
			text = next(self.raw_text.children)
		except:
			return
		if not isinstance(text, str):
			text = text.text
		return cutCaption(text, '', 10)

	def getAllText(self):
		raw = [self.getOrgLink(), self.getMsgLink(), 
			self.getMsgPreview(), str(self.raw_text)]
		return '\n\n'.join([x or '' for x in raw])

	def getView(self):
		text = self.soup.find('span', class_='tgme_widget_message_views').text.strip()
		base = 1
		if text.endswith('K'):
			base = 1000
			text = text[:-1]
		return float(text) * base

	# def isRecent(self):
	# 	t = self.soup.find('time')
	# 	return datetime.now() - timedelta(days=1.5) <= \
	# 		datetime.strptime(t['datetime'][:19], '%Y-%m-%dT%H:%M:%S')

	def getTime(self):
		for t in self.soup.find_all('time'):
			if 'datetime' in t:
				return t['datetime']
		return 0

	def getWeight(self):
		w = self.getView()
		if matchKey(self.getAllText(), ['1.', '编者按']):
			w += 500
		if matchKey(self.getAllText(), ['daily_feminist']):
			w += 200
		return w
		
	def getOrgLink(self):
		forward = self.soup.find('a', class_='tgme_widget_message_forwarded_from_name')
		if forward:
			return forward['href']

	def getMsgLink(self):
		return self.soup.find('a', class_='tgme_widget_message_date')['href']

	def getID(self):
		return self.getOrgLink() or self.getMsgLink()

	def match(self, keys):
		return matchKey(self.getAllText(), keys)

	def getDebug(self):
		t = self.soup.find('time')
		return self.getView(), len(self.raw_text.text), \
			self.getMsgLink().split('/')[3], \
			self.getOrgLink() and self.getOrgLink().split('/')[3], \
			(not not matchKey(self.getAllText(), ['1.', '编者按', 'daily_feminist'])), \
			t['datetime'][:10]
