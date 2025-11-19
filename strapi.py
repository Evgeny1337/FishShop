import requests
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv(override=True)
SERVICE_URL = os.environ['SERVICE_URL']
HEADERS = {"Content-Type": "application/json"}


def get_image(img_url):
    response = requests.get(f"{SERVICE_URL}{img_url}", stream=True)
    return BytesIO(response.content)


def get_cart(tg_id):
    params = {'filters[tg_id][$eq]': tg_id}
    url = f"{SERVICE_URL}api/carts"
    response = requests.get(url, params=params)
    response.raise_for_status()
    carts_response = response.json()
    return carts_response['data'][0] if carts_response['data'] else None


def create_cart(tg_id):
    cart_data = {"data": {"tg_id": tg_id}}
    url = f"{SERVICE_URL}api/carts"
    response = requests.post(url, headers=HEADERS, json=cart_data)
    response.raise_for_status()
    created_cart = response.json()
    return created_cart


def get_cart_products(cart_id):
    params = {'filters[cart][documentId][$eq]': cart_id, 'populate': '*'}
    url = f"{SERVICE_URL}api/product-carts"
    response = requests.get(url, params=params)
    response.raise_for_status()
    product_carts_response = response.json()
    product_carts = product_carts_response['data']
    return [{'products': item['products'], 'amount': item['amount']} for item in product_carts]


def update_product_cart(product_cart_id, data):
    url = f"{SERVICE_URL}api/product-carts/{product_cart_id}"
    response = requests.put(url, headers=HEADERS, json=data)
    response.raise_for_status()
    updated_product_cart = response.json()
    return updated_product_cart


def create_product_cart(data):
    url = f"{SERVICE_URL}api/product-carts"
    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()
    created_product_cart = response.json()
    return created_product_cart


def find_product_cart(cart_id, product_id):
    params = {'filters[cart][documentId][$eq]': cart_id, 'filters[products][documentId]': product_id}
    url = f"{SERVICE_URL}api/product-carts"
    response = requests.get(url, params=params)
    response.raise_for_status()
    product_carts_response = response.json()
    return product_carts_response['data']


def delete_cart(cart_id):
    url = f"{SERVICE_URL}api/carts/{cart_id}"
    response = requests.delete(url)
    response.raise_for_status()
    return response


def update_cart(cart_id, data):
    url = f"{SERVICE_URL}api/carts/{cart_id}"
    response = requests.put(url, headers=HEADERS, json=data)
    response.raise_for_status()
    updated_cart = response.json()
    return updated_cart


def get_products():
    url = f"{SERVICE_URL}api/products"
    response = requests.get(url)
    response.raise_for_status()
    products_response = response.json()
    products_data = products_response['data']
    return [{'title': product['Title'], 'id': product['documentId']} for product in products_data]


def get_product_details(product_id):
    params = {'populate': '*'}
    url = f"{SERVICE_URL}api/products/{product_id}"
    response = requests.get(url, params=params)
    response.raise_for_status()
    product_response = response.json()
    return product_response['data']


def find_user(username, email):
    params = {'filters[username][$eq]': username, 'filters[email][$eq]': email}
    url = f"{SERVICE_URL}api/users/"
    response = requests.get(url, params=params)
    response.raise_for_status()
    users_response = response.json()
    return users_response


def create_user(user_data):
    url = f"{SERVICE_URL}api/users/"
    response = requests.post(url, headers=HEADERS, json=user_data)
    response.raise_for_status()
    created_user = response.json()
    return created_user