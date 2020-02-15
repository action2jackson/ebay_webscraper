from django.views.generic import ListView
import requests
from bs4 import BeautifulSoup


# Start class = homepage
class Index(ListView):
    # Overrides some ListView's variables
    queryset = []
    context_object_name = "items"
    # Front-end attachment
    template_name = "ebay_scraper/index.html"



    # Passes Queryset to Django
    def get_context_data(self, *args, **kwargs):
        # Super() returns an object that allows you to access the parent class through 'super' 
        # Get, Set and Return Context 
        context = super(Index, self).get_context_data(*args, **kwargs)
        context['queryset'] = self.queryset
        return context   



    # Get search results data (Queryset), scrape the results, and send them to Django
    def get_queryset(self):

        # Look at the urls of sites to find the changes for different searches
        base_url = "https://www.ebay.com/sch/parser.html?_from=R40&_nkw={item}&_ipg=25"
        prices_url = "&_udlo={price_low}&_udhi={price_high}"

        # Gets Items, Price Low and Price High
        item = self.request.GET.get('item')
        price_low = self.request.GET.get('from')
        price_high = self.request.GET.get('to')

        # IF the method is 'GET' and an Item was entered
        if self.request.method == 'GET' and item:
            # Puts the Item chosen into a list
            item = "+".join(item.split())
            # If the the Price Low and Price High option are entered
            if price_low and price_high:
                # Add Price Low an Price High to the original url (formatted)
                url = (base_url + prices_url).format(item=item,price_low=price_low,price_high=price_high)
            else:
                # else just add Item to the original url
                url = base_url.format(item=item)
            # scraper stores Scraper class and app runs scraper
            scraper = Scraper(base_url=url)
            app = scraper.run()
            return app


# Class for webscraping code
class Scraper(Index):
    # Scraper Constructor
    def __init__(self, base_url=None):

        super(Scraper, self).__init__()

        # Original url from Index class is dropped down
        self.base_url = base_url

        # : takes the whole list and clears it before all the scraper methods go to work
        self.queryset[:] = []



    # Configures scraped data from ebay into a list
    def run(self):
        try: 
            # Create bs object with method make_soup
            bs = self.make_soup(self.base_url)

            # If we did not get an error
            if not bs.get('error'):

                # Scrape Ebay for a list of ten search result items
                rows = bs.find_all('div', class_ = "s-item__wrapper")[:10]
                
                # Loop through and scrape the list
                for parser in rows:     
                    # Calls parse_rows method to scrape the list in detail   
                    # Parse = String Configuration      
                    self.parse_rows(parser)

            # Error
            else:
                print(bs['error'])

        # Error handling
        except Exception as error:
            print(error)

        return self.queryset



    # Scrapes the list rows for Name, Link, Secondary Info, Price and Image
    def parse_rows(self, parser):
        
        # Get name of item
        name = parser.find('h3', class_="s-item__title")
        if name:
            name = name.text
        else:
            name = ' '

        # Get Link of item
        link = parser.find('a', class_="s-item__link")
        if link:
            # gets href for link instead of text
            link = link.get('href')
        else:
            link = ' '

        # Get secondary info of item (Brand new, new, old, etc...)
        secondary_info = parser.find('span', class_="SECONDARY_INFO")
        if secondary_info:
            secondary_info = secondary_info.text
        else:
            secondary_info = ' '

        # Get prices low and high of the item
        price = parser.find('span', class_="s-item__price")
        if price:
            price = price.text
        else:
            price = ' '

        # Get image of the item
        # Finds image and keeps it as a src
        image = parser.find('img', class_="s-item__image-img").get('src')

        # If Ebay displays default image
        if image == 'https://ir.ebaystatic.com/cr/v/c1/s_1x2.gif':

            # Click the item link and Go into the detail page to find the image 
            soup = self.make_soup(link)

            # Pass in a dictioary to find 'id' instead of 'class'
            image = soup.find('img', {'id': "icImg"}).get('src')

        # Create a dictionary of the searched Ebay item and append it to the Queryset for Django to use and display
        # dict = shortcut for making a dictionary
        self.queryset.append(dict(name=name,link=link,secondary_info=secondary_info,price=price,image=image))

        


    # Returns the data from Ebay
    def make_soup(self, url):
        # headers (Required from Ebay)
        headers = {'Accept': '*/*',
                   'Accept-Encoding': 'gzip, deflate, sdch',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'content-security-policy': "media-src 'self' *.ebaystatic.com; font-src 'self' *.ebaystatic.com",
                   'Cache-Control': 'max-age=0',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

        # Get url, headers and max load time is 15 seconds
        page = requests.get(url, headers=headers, timeout=15)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, "lxml")
        else:
            # Give an error message if page content cant be found
            soup = {'error': "We got status code %s" % page.status_code}
        return soup 