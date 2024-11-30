import requests
from bs4 import BeautifulSoup

def get_products_from_page(url):
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve data from {url}")
        return []

    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    products = []

    for product in soup.find_all(class_='uss_eshop_item'):
        title = product.find(class_='uss_shop_name').get_text(strip=True)
        price = product.find(class_='actual_price').get_text(strip=True)
        products.append((title, price))

    return products


def scrape_products(base_url):
    all_products = []
    max_pages = int(BeautifulSoup(requests.get(base_url).text, 'html.parser').find(class_='uss_last').get_text(strip=True))

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        products = get_products_from_page(url)
        if not products:
            break
        all_products.extend(products)

    return all_products