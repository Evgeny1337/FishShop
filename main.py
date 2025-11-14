import os
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackQueryHandler, CommandHandler, MessageHandler
from dotenv import load_dotenv
import strapi

_database = None


def create_product_text(products):
    if not products:
        return "\nТовары в корзине отсутствуют"
    text = "\n"
    for product in products:
        product_data = product['products'][0]
        text += f"{product_data['Title']} {product['amount']}\n"
    return text


def create_products_keyboard():
    products = strapi.get_products()
    keyboard = [[InlineKeyboardButton(p['title'], callback_data=p['id'])] for p in products]
    keyboard.append([InlineKeyboardButton('🛒 Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(keyboard)


def create_back_keyboard(product_id):
    keyboard = [
        [InlineKeyboardButton('Добавить в корзину', callback_data=f'put_{product_id}')],
        [InlineKeyboardButton('🛒 Корзина', callback_data='cart')],
        [InlineKeyboardButton('Назад', callback_data='back')],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_cart_keyboard():
    keyboard = [
        [InlineKeyboardButton('Оплатить корзину', callback_data='buy')],
        [InlineKeyboardButton('Очистить корзину', callback_data='clear')],
        [InlineKeyboardButton('В меню', callback_data='back')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_or_create_cart(tg_id):
    cart = strapi.get_cart(tg_id)
    if not cart:
        cart = strapi.create_cart(tg_id)['data']
    return cart


def get_cart_products(tg_id):
    cart = get_or_create_cart(tg_id)
    cart_id = cart['documentId']
    return strapi.get_cart_products(cart_id)


def put_product_in_basket(update, product_id):
    tg_id = update.chat_id
    cart = get_or_create_cart(tg_id)
    cart_id = cart['documentId']

    product_cart_data = strapi.find_product_cart(cart_id, product_id)

    amount = product_cart_data[0]['amount'] + 1 if product_cart_data else 1
    data = {'data': {"cart": cart_id, "products": [product_id], "amount": amount}}

    if product_cart_data:
        strapi.update_product_cart(product_cart_data[0]['documentId'], data)
    else:
        strapi.create_product_cart(data)


def clear_products_cart(update):
    tg_id = update.effective_chat.id
    cart = get_or_create_cart(tg_id)
    cart_id = cart['documentId']

    strapi.delete_cart(cart_id)
    get_or_create_cart(tg_id)


def set_user_in_cart(update):
    tg_id = update.effective_chat.id
    db = get_database_connection()
    user_name = db.get('name')
    user_email = db.get('email')

    cart = get_or_create_cart(tg_id)
    cart_id = cart['documentId']

    user_data = strapi.find_user(user_name, user_email)

    if not user_data:
        user_data = {
            "email": user_email,
            "username": user_name,
            "confirmed": True,
            "blocked": False,
            "role": 1,
            "password": 'Evgeny-8426'
        }
        user = strapi.create_user(user_data)

        cart_data = {"data": {"users_permissions_users": user['id']}}
        strapi.update_cart(cart_id, cart_data)


def get_product_details(product_id):
    product_data = strapi.get_product_details(product_id)
    img_url = product_data['Picture']['formats']['medium']['url']
    img = strapi.get_image(img_url)
    return {
        "description": f"{product_data['Title']} - {product_data['Price']}р.\n{product_data['Description']}",
        "img": img
    }


def callback_cart(update, context):
    update.callback_query.message.delete()
    if update.callback_query.data == 'back':
        update.callback_query.message.reply_text(text='Привет!', reply_markup=create_products_keyboard())
        return 'HANDLE_MENU'
    if update.callback_query.data == 'clear':
        clear_products_cart(update)
        products = get_cart_products(update.callback_query.message.chat.id)
        update.callback_query.message.reply_text(text=create_product_text(products),
                                                 reply_markup=create_cart_keyboard())
        return 'HANDLE_CART'
    if update.callback_query.data == 'buy':
        update.callback_query.message.reply_text(text="Введите свою почту")
        return 'WAITING_EMAIL'


def callback_product(update, context):
    if update.callback_query.data == 'back':
        update.callback_query.message.delete()
        update.callback_query.message.reply_text(text='Привет!', reply_markup=create_products_keyboard())
        return 'HANDLE_MENU'
    if update.callback_query.data.startswith('put'):
        update.callback_query.message.delete()
        product_id = update.callback_query.data.split('_')[1]
        put_product_in_basket(update.callback_query.message, product_id)
        update.callback_query.message.reply_text(text='Привет!', reply_markup=create_products_keyboard())
        return 'HANDLE_MENU'
    if update.callback_query.data == 'cart':
        update.callback_query.message.delete()
        products = get_cart_products(update.callback_query.message.chat.id)
        update.callback_query.message.reply_text(text=create_product_text(products),
                                                 reply_markup=create_cart_keyboard())
        return 'HANDLE_CART'


def handle_email(update, context):
    db = get_database_connection()
    update.message.delete()
    if not update.message.text:
        update.message.reply_text(text='Введите свою почту')
        return 'WAITING_EMAIL'
    db.set('email', update.message.text)
    update.message.reply_text(text="Введите свое имя")
    return 'WRITE_NAME'


def handle_name(update, context):
    db = get_database_connection()
    update.message.delete()
    if not update.message.text:
        update.message.reply_text(text='Введите свое имя')
        return 'WRITE_NAME'
    db.set('name', update.message.text)
    set_user_in_cart(update)
    update.message.reply_text(text='С вами свяжется продавец', reply_markup=create_products_keyboard())
    return 'HANDLE_MENU'


def button(update, context):
    query = update.callback_query
    query.answer()
    tg_id = update.effective_chat.id
    if query.data == 'cart':
        query.message.delete()
        products = get_cart_products(tg_id)
        query.message.reply_text(text=create_product_text(products), reply_markup=create_cart_keyboard())
        return 'HANDLE_CART'

    product_data = get_product_details(query.data)
    query.message.delete()
    context.bot.send_photo(chat_id=tg_id, photo=product_data['img'], caption=product_data['description'],
                           reply_markup=create_back_keyboard(query.data))
    return 'HANDLE_DESCRIPTION'


def start(update, context):
    tg_id = update.effective_chat.id
    get_or_create_cart(tg_id)
    update.message.reply_text(text='Привет!', reply_markup=create_products_keyboard())
    return 'HANDLE_MENU'


def handle_users_reply(update, context):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id)

    states_functions = {
        'START': start,
        'HANDLE_MENU': button,
        'HANDLE_DESCRIPTION': callback_product,
        'HANDLE_CART': callback_cart,
        'WAITING_EMAIL': handle_email,
        'WRITE_NAME': handle_name
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_host = os.getenv('DATABASE_HOST')
        database_port = int(os.getenv('DATABASE_PORT'))
        _database = redis.Redis(host=database_host, port=database_port, db=0, decode_responses=True)
    return _database


def main():
    load_dotenv(override=True)
    token = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()