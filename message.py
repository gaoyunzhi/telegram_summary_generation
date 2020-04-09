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
	return cleanUrl(new_soup.get_text(separator=' '))

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
		# May need to deal with '<br>'
		return prefix + str(self.raw_text)

	def getMsgPreview(self):
		preview = self.soup.find('a', class_='tgme_widget_message_link_preview')
		if preview:
			return preview.text

	def getTitle(self):
		title = self.soup.find('div', class_='link_preview_title')
		if title:
			return title.text

	def getHiddenText(self):
		raw = [self.getOrgLink(), self.getMsgLink(), self.getMsgPreview()]
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
		return datetime.now() - timedelta(days=1) <= \
			datetime.strptime(t['datetime'][:10], '%Y-%m-%d')


	def getWeight(self):
		return self.getView() + len(self.raw_text.text) * 10
		
	def getOrgLink(self):
		forward = self.soup.find('a', class_='tgme_widget_message_forwarded_from_name')
		if forward:
			return forward['href']

	def getMsgLink(self):
		return self.soup.find('a', class_='tgme_widget_message_date')['href']

	def getID(self):
		return self.getOrgLink() or self.getMsgLink()

	def match(self, keys):
		return matchKey(self.getHiddenText(), keys) or \
			matchKey(str(self.raw_text), keys)

