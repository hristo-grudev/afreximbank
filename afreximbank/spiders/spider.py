import datetime
import json

import scrapy
from scrapy.exceptions import CloseSpider

from scrapy.loader import ItemLoader

from ..items import AfreximbankItem
from itemloaders.processors import TakeFirst
import requests

url = "https://www.afreximbank.com/wp-admin/admin-ajax.php"

base_payload = "action=get_custom_entries&posts_per_page=99999&orderby=date&order=DESC&post_type=post&post_status=publish&category_name=news&date_query=%5B%7B%22after%22%3A%2220080101%22%2C+%22before%22%3A%22{}1231%22%2C+%22inclusive%22%3Atrue%7D%5D&render_place=news_page"
headers = {
  'authority': 'www.afreximbank.com',
  'pragma': 'no-cache',
  'cache-control': 'no-cache',
  'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
  'accept': '*/*',
  'x-requested-with': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
  'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'origin': 'https://www.afreximbank.com',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.afreximbank.com/category/news/',
  'accept-language': 'en-US,en;q=0.9,bg;q=0.8',
  'cookie': '_ga=GA1.2.2030451782.1618231250; _gid=GA1.2.1947664565.1618319857; _gat_gtag_UA_139450284_1=1'
}


class AfreximbankSpider(scrapy.Spider):
	name = 'afreximbank'
	start_urls = ['https://www.afreximbank.com/category/news/']
	current_year = datetime.datetime.today().year

	def parse(self, response):
		data = requests.request("POST", url, headers=headers, data=base_payload.format(self.current_year))
		data = json.loads(data.text)
		raw_data = scrapy.Selector(text=data['entries_html'])

		post_links = raw_data.xpath('//h2[@itemprop="headline"]/a/@href').getall()
		yield from response.follow_all(post_links, self.parse_post)

	def parse_post(self, response):
		title = response.xpath('//h1/text()').get()
		description = response.xpath('//section[@class="entry-content"]//text()[normalize-space()]').getall()
		description = [p.strip() for p in description if '{' not in p]
		description = ' '.join(description).strip()
		date = response.xpath('//time/text()').get()

		item = ItemLoader(item=AfreximbankItem(), response=response)
		item.default_output_processor = TakeFirst()
		item.add_value('title', title)
		item.add_value('description', description)
		item.add_value('date', date)

		return item.load_item()
