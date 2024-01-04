from bs4 import BeautifulSoup
from urllib import request
from slugify import slugify
import json
import random
import re

BASE_URL = "https://www.perfume24x7.com"

CATEGORY_IDS = list(range(100, 127))
CONCENTRATION_IDS = list(range(50, 54))

def save_json(filename, data):
    try:
        with open(f"data/{filename}", "w", encoding='utf8') as file:
            json.dump(data, file, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing to {filename}: {e}")

def read_json(filename):
    try:
        with open(f"data/{filename}", "r", encoding='utf8') as file:
            return json.load(file)
    except IOError as e:
        print(f"Error reading {filename}: {e}")

def format_image_path(path):
    if path.startswith("/"):
        return f"https:{path}"
    return path

def get_soup(url):
    try:
        html = request.urlopen(url).read()
        soup = BeautifulSoup(html, "html.parser")
        return soup
    except Exception as e:
        print(f"Error getting soup from {url}: {e}")

def find_element_by_class(soup, tag, class_name):
    try:
        return soup.find(tag, class_=class_name)
    except Exception as e:
        print(f"Error finding {tag} with class {class_name}: {e}")

def find_elements_by_class(soup, tag, class_name):
    try:
        return soup.find_all(tag, class_=class_name)
    except Exception as e:
        print(f"Error finding {tag} with class {class_name}: {e}")

def find_element_by_selector(soup, selector):
    try:
        return soup.select_one(selector)
    except Exception as e:
        print(f"Error finding {selector}: {e}")

def find_elements_by_selector(soup, selector):
    try:
        return soup.select(selector)
    except Exception as e:
        print(f"Error finding {selector}: {e}")

def find_element_by_atrribute(soup, tag, class_, attribute, value):
    try:
        return soup.find(tag, class_= class_, attrs={attribute: value})
    except Exception as e:
        print(f"Error finding {tag} with {attribute}={value}: {e}")

def get_text(element):
    try:
        return element.get_text(strip=True)
    except Exception as e:
        print(f"Error getting text from {element}: {e}")

def get_html(element):
    try:
        return element.decode_contents()
    except Exception as e:
        print(f"Error getting html from {element}: {e}")


def get_random_price(size_name):
    match = re.search(r'(\d+)\s*ml', size_name)
    if match:
        min_price = int(match.group(1))
        max_price = 6 * int(match.group(1))
    else:
        min_price = 100
        max_price = 1500

    if "refillable" in size_name.lower():
        max_price = max_price * 1.5

    return round(random.uniform(min_price, max_price), 2)

def scrape_perfume_data():
    brand_soup = get_soup(f"{BASE_URL}/collections")
    brand_link_elements = find_elements_by_class(brand_soup, 'a', 'logo-bar__link')

    brands, images, products, sizes, quantities = [], [], [], [], []
    brand_id, image_id, product_id, size_id, quantity_id = 1000, 1000, 1000, 100, 100

    brand_instance = {
        "id": None,
        "name": None,
        "slug": None,
    }

    image_instance = {
        "id": None,
        "product_id": None,
        "category_id": None,
        "brand_id": None,
        "path": None,
        "main": None,
    }

    product_instance = {
        "id": None,
        "name": None,
        "slug": None,
        "description": None,
        "brand_id": None,
        "concentration_id": None,
        "categories": None, # json array of category ids
    }

    size_instance = {
        "id": None,
        "name": None,
    }

    quantity_instance = {
        "id": None,
        "product_id": None,
        "size_id": None,
        "quantity": None,
        "price": None,
    }

    for brandLinkElement in brand_link_elements:
        if brand_id == 1030:
            brand_id += 1
            continue
        brand_instance["id"] = brand_id

        # Image of brand
        image_instance["id"] = image_id
        image_instance["brand_id"] = brand_id
        image_instance["path"] = format_image_path(find_element_by_class(brandLinkElement, 'img', 'logo-bar__image')['src'])
        image_instance["main"] = True
        
        # Append image to images
        images.append(image_instance.copy()); image_id += 1; image_instance.clear()

        product_soup = get_soup(f"{BASE_URL}{brandLinkElement['href']}")

        brand_instance["name"] = get_text(find_element_by_class(product_soup, 'h1', 'section-header__title'))
        brand_instance["slug"] = slugify(brand_instance["name"])

        product_links = find_elements_by_class(product_soup, 'a', 'grid-product__link')

        for product_link in product_links:
            
            product_detail_soup = get_soup(f"{BASE_URL}{product_link['href']}")

            product_instance["id"] = product_id
            product_instance["name"] = get_text(find_element_by_class(product_detail_soup, 'h1', 'product-single__title'))
            product_instance["slug"] = slugify(f"{product_instance['name']} p.{product_id}")
            product_instance["description"] = get_html(find_elements_by_selector(product_detail_soup, 'div.product-block div.rte')[1])
            product_instance["brand_id"] = brand_id
            product_instance["concentration_id"] = next((item['id'] for item in read_json('concentrations.json') if item['name'].lower() in product_instance["name"].lower()), random.choice(CONCENTRATION_IDS))

            # Randomly select 1-5 categories
            product_instance["categories"] = random.sample(CATEGORY_IDS, random.randint(1, 5))

            # Image of product
            image_instance["id"] = image_id
            image_instance["product_id"] = product_id
            image_instance["path"] = format_image_path(find_element_by_selector(product_detail_soup, 'div.image-wrap > image-element > img')['src'])
            image_instance["main"] = True
            images.append(image_instance.copy()); image_id += 1

            for index, item in enumerate(find_elements_by_class(product_detail_soup, 'a', 'product__thumb')):
                image_instance["id"] = image_id
                if index > 0:
                    image_instance["path"] = format_image_path(item['href'])
                    image_instance["main"] = False

                # Append image to images
                images.append(image_instance.copy()); image_id += 1

            image_instance.clear()
        
            # Quantity of product
            quantity_instance["id"] = quantity_id
            quantity_instance["product_id"] = product_id
            quantity_instance["quantity"] = random.randint(1, 100)

            field_element = find_element_by_atrribute(product_detail_soup, 'fieldset', 'variant-input-wrap', 'name', 'Size')

            if field_element is not None:
                for size_element in find_elements_by_selector(field_element, 'div.variant-input > label.variant__button-label'):
                    size_instance["id"] = size_id
                    quantity_instance["id"] = quantity_id
                    size = get_text(size_element).lower()
                    if 'ml' in size:
                        size_instance["name"] = re.sub(r'(\d+)(ml)', r'\1 \2', size)
                    else:
                        size_instance["name"] = '100 ml'
                    if not any(item["name"] == size_instance["name"] for item in sizes):
                        quantity_instance["size_id"] = size_id
                        sizes.append(size_instance.copy()); size_id += 1
                    else:
                        quantity_instance["size_id"] = next((item['id'] for item in sizes if item['name'] == size_instance["name"]))
                    quantity_instance["price"] = get_random_price(size_instance["name"])
                    quantities.append(quantity_instance.copy()); quantity_id += 1
                   
            else:
                size_instance["id"] = size_id
                match = re.search(r'(\d+)\s*ml', product_instance["name"].lower())
                if match:
                    quantity = match.group(1)
                    size_instance["name"] = f"{quantity} ml"  # Format with a space between quantity and unit
                else:
                    size_instance["name"] = "100 ml"  # Default value if no match is found

                if not any(item["name"] == size_instance["name"] for item in sizes):
                    quantity_instance["size_id"] = size_id
                    sizes.append(size_instance.copy()); size_id += 1; 
                else:
                    quantity_instance["size_id"] = next((item['id'] for item in sizes if item['name'] == size_instance["name"]))
                
                quantity_instance["price"] = get_random_price(size_instance["name"])
                quantities.append(quantity_instance.copy()); quantity_id += 1; quantity_instance.clear()

            # clear
            # Append product to products
            size_instance.clear()
            products.append(product_instance.copy()); product_id += 1; product_instance.clear()

        # Append brand to brands
        brands.append(brand_instance.copy()); brand_id += 1; brand_instance.clear()

    save_json("brands.json", brands)
    save_json("images.json", images)
    save_json("products.json", products)
    save_json("sizes.json", sizes)
    save_json("quantities.json", quantities)

if __name__ == "__main__":
    scrape_perfume_data()