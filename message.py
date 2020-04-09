from bs4 import BeautifulSoup
import cached_url
import sys
from telegram_util import cleanUrl, matchKey, clearUrl
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

def getTextCN(soup):
	new_soup = BeautifulSoup(str(soup), features='lxml')
	links = set()
	for x in new_soup.find_all('a'):
		link = cleanUrl(clearUrl(getCnLink(x))) # 呵呵...
		if link in links or (links and x.text == 'source'):
			x.replace_with('')
		else:
			links.add(link)
			x.replace_with(' %s ' % link)
	result = cleanUrl(new_soup.get_text(separator=' '))
	return result.strip().strip('|')

# TODO: may need timestamp info
class Message():
	def __init__(self, soup):
		self.soup = soup
		self.raw_text = soup.find('div', class_='tgme_widget_message_text') \
			or BeautifulSoup('', features='lxml')
		self.text_cn = '' # 墙内版本
		
	def getCnText(self):
		self.text_cn = self.text_cn or getTextCN(self.raw_text)
		return self.text_cn

	def getText(self, locale):
		prefix = '【%s】\n' % self.getTitle() 
		if locale == 'cn':
			return prefix + self.getCnText().replace('\n\n', '\n')
		text = prefix + ''.join([str(x) for x in self.raw_text.children])
		return text.replace('<br/>', '\n')

	def getMsgPreview(self):
		preview = self.soup.find('a', class_='tgme_widget_message_link_preview')
		if preview:
			return preview.text

	def getTitle(self):
		title = self.soup.find('div', class_='link_preview_title')
		if title:
			return title.text

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

	def isRecent(self):
		t = self.soup.find('time')
		return datetime.now() - timedelta(days=1.5) <= \
			datetime.strptime(t['datetime'][:19], '%Y-%m-%dT%H:%M:%S')

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

