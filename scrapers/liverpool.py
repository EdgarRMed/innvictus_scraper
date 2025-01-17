from selenium import webdriver
from pyvirtualdisplay import Display
import asyncio
import json
from models.cache import ListCache
from models.products import LiverPoolProduct
from configs import global_vars
import logging


class LiverPoolNewProdsScraper:
    def __init__(self, queue):
        self.config = json.load(open(global_vars.MAIN_CONFIG_FILE_LOCATION))
        self.queue = queue
        print = logging.getLogger(' LiverpoolMonitor ').info
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        # self.options.add_argument('--headless')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('start-maximized')
        self.options.add_argument('disable-infobars')
        self.webdriver_path = self.config.get("WEBDRIVER_PATH")
        self.loop = asyncio.new_event_loop()
        self.driver = None
        self.URLs = [
            'https://www.liverpool.com.mx/tienda/zapatos/catst1105210',
            'https://www.liverpool.com.mx/tienda/zapatos/catst1010801',
            'https://www.liverpool.com.mx/tienda/zapatos/catst1011086'
        ]
        self.itter_time = 10

    def start(self):
        self.cache = ListCache('LiverPoolCache')
        self.loop.run_until_complete(self.main())

    async def main(self):
        display = Display(visible=0, size=(800, 800))  
        display.start()
        self.driver = webdriver.Chrome(
            executable_path=self.webdriver_path, options=self.options)
        self.driver.implicitly_wait(10)
        # await self.create_cache()
        while True:
            try:
                all_links = await self.get_all_prod_links()
                print(f'[+] Got {len(all_links)} prod links!')
                for link in all_links:
                    if not self.cache.has_item(link):
                        prod = await self.get_prod_details(link)
                        self.queue.put(prod)
                        self.cache.add_item(link)
                await asyncio.sleep(self.itter_time)
            except Exception as e:
                print(e)

    async def create_cache(self):
        print('[+] Creating cache ..')
        links = await self.get_all_prod_links()
        self.cache.replace_cache(links)
        print('[+] Created cache for prods')

    async def get_all_prod_links(self):
        links = []
        for url in self.URLs:
            self.driver.get(url)
            prods_list = self.driver.find_elements_by_xpath(
                '//li[@class="m-product__card card-masonry"]')
            for prod in prods_list:
                link = prod.find_element_by_tag_name('a').get_attribute('href')
                links.append(link)
        return links

    async def get_prod_details(self, link):
        self.driver.get(link)
        prod = LiverPoolProduct()
        prod.name = self.driver.find_element_by_xpath(
            '//h1[@class="a-product__information--title"]').text
        prod.link = link
        out_of_stock_sizes = self.driver.find_elements_by_xpath(
            '//button[@class="a-btn a-btn--actionpdp -disabled"]')
        for size in out_of_stock_sizes:
            prod.out_of_stock_sizes.append(size.text)
        in_stock_sizes = self.driver.find_elements_by_xpath(
            '//button[@class="a-btn a-btn--actionpdp"]')
        for size in in_stock_sizes:
            prod.in_stock_sizes.append(size.text)
        prod.img_link = self.driver.find_element_by_xpath(
            '//img[@id="image-real"]').get_attribute('src')
        prod.color = self.driver.find_element_by_xpath(
            '//p[@class="a-product__paragraphColor m-0 mt-2 mb-1"]').text.split(':')[-1].strip()
        prod.price = self.driver.find_element_by_xpath(
            '//p[@class="a-product__paragraphDiscountPrice m-0 d-inline "]').text.split('\n')[0].replace(',', '').replace('$', '')
        return prod

    # def quit_browser(self):
    #     if self.driver is not None:
    #         self.driver.quit()
    #         self.driver = None
