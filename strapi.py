import requests
from io import BytesIO

HEADERS = {"Content-Type": "application/json"}


def get_image(img_url, service_url):
    response = requests.get(f"{service_url}{img_url}", stream=True)
    response.raise_for_status()
    return BytesIO(response.content)


def get_cart(tg_id, service_url):
    params = {'filters[tg_id][$eq]': tg_id}
    url = f"{service_url}api/carts"
    response = requests.get(url, params=params)
    response.raise_for_status()
    carts_response = response.json()
    return carts_response['data'][0] if carts_response['data'] else None


def create_cart(tg_id, service_url):
    cart_creation_payload = {"data": {"tg_id": tg_id}}
    url = f"{service_url}api/carts"
    response = requests.post(url, headers=HEADERS, json=cart_creation_payload)
    response.raise_for_status()
    created_cart = response.json()
    return created_cart


def get_cart_products(cart_id, service_url):
    params = {'filters[cart][documentId][$eq]': cart_id, 'populate': '*'}
    url = f"{service_url}api/product-carts"
    response = requests.get(url, params=params)
    response.raise_for_status()
    product_carts_response = response.json()
    cart_items = product_carts_response['data']
    return [{'products': item['products'], 'amount': item['amount']} for item in cart_items]


def update_product_cart(product_cart_id, update_payload, service_url):
    url = f"{service_url}api/product-carts/{product_cart_id}"
    response = requests.put(url, headers=HEADERS, json=update_payload)
    response.raise_for_status()
    updated_product_cart = response.json()
    return updated_product_cart


def create_product_cart(product_cart_payload, service_url):
    url = f"{service_url}api/product-carts"
    response = requests.post(url, headers=HEADERS, json=product_cart_payload)
    response.raise_for_status()
    created_product_cart = response.json()
    return created_product_cart


def find_product_cart(cart_id, product_id, service_url):
    params = {'filters[cart][documentId][$eq]': cart_id, 'filters[products][documentId]': product_id}
    url = f"{service_url}api/product-carts"
    response = requests.get(url, params=params)
    response.raise_for_status()
    product_carts_response = response.json()
    return product_carts_response['data']


def delete_cart(cart_id, service_url):
    url = f"{service_url}api/carts/{cart_id}"
    response = requests.delete(url)
    response.raise_for_status()
    return response


def update_cart(cart_id, cart_update_payload, service_url):
    url = f"{service_url}api/carts/{cart_id}"
    response = requests.put(url, headers=HEADERS, json=cart_update_payload)
    response.raise_for_status()
    updated_cart = response.json()
    return updated_cart


def get_products(service_url):
    url = f"{service_url}api/products"
    response = requests.get(url)
    response.raise_for_status()
    products_response = response.json()
    products_list = products_response['data']
    return [{'title': product['Title'], 'id': product['documentId']} for product in products_list]


def get_product_details(product_id, service_url):
    params = {'populate': '*'}
    url = f"{service_url}api/products/{product_id}"
    response = requests.get(url, params=params)
    response.raise_for_status()
    product_response = response.json()
    return product_response['data']


def find_user(username, email, service_url):
    params = {'filters[username][$eq]': username, 'filters[email][$eq]': email}
    url = f"{service_url}api/users/"
    response = requests.get(url, params=params)
    response.raise_for_status()
    users_response = response.json()
    return users_response


def create_user(user_registration_info, service_url):
    url = f"{service_url}api/users/"
    response = requests.post(url, headers=HEADERS, json=user_registration_info)
    response.raise_for_status()
    created_user = response.json()
    return created_user