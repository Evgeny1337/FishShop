import requests
from io import BytesIO

_base_url = "http://localhost:1337/"
_headers = {"Content-Type": "application/json"}


def strapi_request(method, endpoint, data=None, params=None):
    url = f"{_base_url}{endpoint}"
    if method == 'GET':
        response = requests.get(url, params=params)
    elif method == 'POST':
        response = requests.post(url, headers=_headers, json=data)
    elif method == 'PUT':
        response = requests.put(url, headers=_headers, json=data)
    elif method == 'DELETE':
        response = requests.delete(url)
    response.raise_for_status()
    return response.json() if method != 'DELETE' else response


def get_image(img_url):
    response = requests.get(f"{_base_url}{img_url}", stream=True)
    return BytesIO(response.content)


def get_cart(tg_id):
    params = {'filters[tg_id][$eq]': tg_id}
    data = strapi_request('GET', 'api/carts', params=params)
    return data['data'][0] if data['data'] else None


def create_cart(tg_id):
    data = {"data": {"tg_id": tg_id}}
    return strapi_request('POST', 'api/carts', data=data)


def get_cart_products(cart_id):
    params = {'filters[cart][documentId][$eq]': cart_id, 'populate': '*'}
    product_carts = strapi_request('GET', 'api/product-carts', params=params)['data']
    return [{'products': item['products'], 'amount': item['amount']} for item in product_carts]


def update_product_cart(product_cart_id, data):
    return strapi_request('PUT', f"api/product-carts/{product_cart_id}", data=data)


def create_product_cart(data):
    return strapi_request('POST', 'api/product-carts', data=data)


def find_product_cart(cart_id, product_id):
    params = {'filters[cart][documentId][$eq]': cart_id, 'filters[products][documentId]': product_id}
    return strapi_request('GET', 'api/product-carts', params=params)['data']


def delete_cart(cart_id):
    return strapi_request('DELETE', f"api/carts/{cart_id}")


def update_cart(cart_id, data):
    return strapi_request('PUT', f"api/carts/{cart_id}", data=data)


def get_products():
    products_data = strapi_request('GET', 'api/products')['data']
    return [{'title': product['Title'], 'id': product['documentId']} for product in products_data]


def get_product_details(product_id):
    return strapi_request('GET', f'api/products/{product_id}?populate=*')['data']


def find_user(username, email):
    params = {'filters[username][$eq]': username, 'filters[email][$eq]': email}
    return strapi_request('GET', 'api/users/', params=params)


def create_user(user_data):
    return strapi_request('POST', 'api/users/', data=user_data)