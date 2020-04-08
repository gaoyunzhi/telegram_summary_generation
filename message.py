from bs4 import BeautifulSoup
import cached_url
import sys
from telegram_util import cleanUrl

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
	for x in new_soup.find_all('a'):
		x.replace_with(' %s ' % getCnLink(x))
	return cleanUrl(x.text)

class Message():
	def __init__(self, soup):
		self.raw_text = soup.find('div', class_='tgme_widget_message_text')
		self.text_cn = '' # 墙内版本
		
	def getCnText(self):
		self.text_cn = self.text_cn or getTextCN(self.raw_text)
		return self.text_cn

	def getMsgPreview(self):
		preview = self.raw_text.find('a', class_='tgme_widget_message_link_preview')
		if preview:
			return preview.text

	def getHiddenText(self):
		raw = [self.getOrgLink(), self.getMsgLink(), self.getMsgPreview()]
		return '\n\n'.join([x or '' for x in raw])

	def getView(self):
		return int(self.raw_text.find('span', class_=tgme_widget_message_views).text)
		
	def getOrgLink(self):
		forward = self.raw_text.find('a', class_='tgme_widget_message_forwarded_from_name')
		if forward:
			return forward['href']

	def getMsgLink(self):
		return self.raw_text.find('a', class_='tgme_widget_message_date')['href']

	def getID(self):
		return self.getOrgLink() or self.getMsgLink()

