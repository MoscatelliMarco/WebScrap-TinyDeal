import scrapy
import pandas as pd

class SpecialOffersSpider(scrapy.Spider):
    name = "special_offers"
    allowed_domains = ["web.archive.org"]

    def __init__(self):
        super().__init__()
        self.data = []

    # Instead of start_urls I use a function that runs as first request
    # Change the default Scrapy User-Agent to prevent any blocks of this type from the website
    def start_requests(self):
        yield scrapy.Request(url="https://web.archive.org/web/20190225123327/https://www.tinydeal.com/specials.html", callback=self.parse, headers= {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        })

    def parse(self, response):
        # Iterate over all products in the page
        for product in response.xpath("//ul[@class='productlisting-ul']/div/li"):
            self.data.append({
                "title": product.xpath(".//a[@class='p_box_title']/text()").get(),
                "url": response.urljoin(product.xpath(".//a[@class='p_box_img']/@href").get()),
                "discounted_price": product.xpath(".//span[@class='productSpecialPrice fl']/text()").get(),
                "original_price": product.xpath(".//span[@class='normalprice fl']/text()").get()
            })

        next_page = response.xpath("//a[@class='nextPage']/@href").get()

        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse, headers= {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
            })

    def closed(self, reason):

        # Convert list to dataframe
        df = pd.DataFrame(self.data)

        # Remove $ from prices
        df['discounted_price'] = df['discounted_price'].str.replace('$', '')
        df['original_price'] = df['original_price'].str.replace('$', '')

        # Convert prices into float numbers
        df[['discounted_price', 'original_price']] = df[['discounted_price', 'original_price']].astype(float)

        # Calculate discount and sort dataframe by it
        df['discount'] = (1 - df['discounted_price'] / df['original_price']).round(4) * 100
        df = df.sort_values(by='discount', ascending=False)

        # Remove NaNs and reset index
        df.dropna(inplace=True)
        df.reset_index(inplace=True, drop=True)

        # Save and print df
        df.to_csv('products_data.csv')
        print(df)