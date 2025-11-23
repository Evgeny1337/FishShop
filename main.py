import os
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, CallbackQueryHandler, CommandHandler, MessageHandler
from dotenv import load_dotenv
import strapi

DATABASE = None


def create_product_text(products):
    if not products:
        return "\nТовары в корзине отсутствуют"
    text = "\n"
    for product in products:
        product_data = product['products'][0]
        text += f"{product_data['Title']} {product['amount']}\n"
    return text


def create_products_keyboard(service_url):
    products = strapi.get_products(service_url)
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


def create_cart(tg_id, service_url):
    cart = strapi.create_cart(tg_id, service_url)['data']
    return cart


def get_cart_products(tg_id, service_url):
    cart = strapi.get_cart(tg_id, service_url)
    if not cart:
        cart = create_cart(tg_id, service_url)
    cart_id = cart['documentId']
    return strapi.get_cart_products(cart_id, service_url)


def put_product_in_basket(update, product_id, service_url):
    tg_id = update.chat_id
    cart = strapi.get_cart(tg_id, service_url)
    if not cart:
        cart = create_cart(tg_id, service_url)
    cart_id = cart['documentId']

    product_cart_data = strapi.find_product_cart(cart_id, product_id, service_url)

    amount = product_cart_data[0]['amount'] + 1 if product_cart_data else 1
    data = {'data': {"cart": cart_id, "products": [product_id], "amount": amount}}

    if product_cart_data:
        strapi.update_product_cart(product_cart_data[0]['documentId'], data, service_url)
    else:
        strapi.create_product_cart(data, service_url)


def clear_products_cart(update, service_url):
    tg_id = update.effective_chat.id
    cart = strapi.get_cart(tg_id, service_url)
    if not cart:
        cart = create_cart(tg_id,service_url)
    cart_id = cart['documentId']

    strapi.delete_cart(cart_id, service_url)
    create_cart(tg_id, service_url)


def set_user_in_cart(update, user_password, service_url, db):
    tg_id = update.effective_chat.id
    user_name = db.get('name')
    user_email = db.get('email')

    cart = strapi.get_cart(tg_id, service_url)
    if not cart:
        cart = create_cart(tg_id, service_url)
    cart_id = cart['documentId']

    user_data = strapi.find_user(user_name, user_email, service_url)
    if not user_data:
        user_data = {
            "email": user_email,
            "username": user_name,
            "confirmed": True,
            "blocked": False,
            "role": 1,
            "password": user_password
        }
        user = strapi.create_user(user_data, service_url)

        cart_data = {"data": {"users_permissions_users": user['id']}}
        strapi.update_cart(cart_id, cart_data, service_url)


def get_product_details(product_id, service_url):
    product_data = strapi.get_product_details(product_id, service_url)
    img_url = product_data['Picture']['formats']['medium']['url']
    img = strapi.get_image(img_url, service_url)
    return {
        "description": f"{product_data['Title']} - {product_data['Price']}р.\n{product_data['Description']}",
        "img": img
    }


def handle_cart_actions(update, context):
    update.callback_query.message.delete()
    service_url = context.bot_data['service_url']
    if update.callback_query.data == 'back':
        update.callback_query.message.reply_text(text='Привет!', reply_markup=create_products_keyboard(service_url))
        return 'HANDLE_MENU'
    if update.callback_query.data == 'clear':
        clear_products_cart(update,service_url)
        products = get_cart_products(update.callback_query.message.chat.id,service_url)
        update.callback_query.message.reply_text(text=create_product_text(products),
                                                 reply_markup=create_cart_keyboard())
        return 'HANDLE_CART'
    if update.callback_query.data == 'buy':
        update.callback_query.message.reply_text(text="Введите свою почту")
        return 'WAITING_EMAIL'


def handle_product_actions(update, context):
    service_url = context.bot_data['service_url']
    if update.callback_query.data == 'back':
        update.callback_query.message.delete()
        update.callback_query.message.reply_text(text='Привет!', reply_markup=create_products_keyboard(service_url))
        return 'HANDLE_MENU'
    if update.callback_query.data.startswith('put'):
        product_id = update.callback_query.data.split('_')[1]
        put_product_in_basket(update.callback_query.message, product_id, service_url)
        update.callback_query.answer("Товар добавлен в корзину")
        return 'HANDLE_DESCRIPTION'
    if update.callback_query.data == 'cart':
        update.callback_query.message.delete()
        products = get_cart_products(update.callback_query.message.chat.id, service_url)
        update.callback_query.message.reply_text(text=create_product_text(products),
                                                 reply_markup=create_cart_keyboard())
        return 'HANDLE_CART'


def handle_email(update, context):
    db = context.bot_data['db_connection']
    update.message.delete()
    if not update.message.text:
        update.message.reply_text(text='Введите свою почту')
        return 'WAITING_EMAIL'
    db.set('email', update.message.text)
    update.message.reply_text(text="Введите свое имя")
    return 'WRITE_NAME'


def handle_name(update, context):
    db = context.bot_data['db_connection']
    service_url = context.bot_data['service_url']
    update.message.delete()
    if not update.message.text:
        update.message.reply_text(text='Введите свое имя')
        return 'WRITE_NAME'
    db.set('name', update.message.text)
    user_password = context.bot_data['user_password']
    set_user_in_cart(update,user_password,service_url, db)
    update.message.reply_text(text='С вами свяжется продавец', reply_markup=create_products_keyboard(service_url))
    return 'HANDLE_MENU'


def handle_menu_selection(update, context):
    query = update.callback_query
    query.answer()
    tg_id = update.effective_chat.id
    service_url = context.bot_data['service_url']
    if query.data == 'cart':
        query.message.delete()
        products = get_cart_products(tg_id,service_url)
        query.message.reply_text(text=create_product_text(products), reply_markup=create_cart_keyboard())
        return 'HANDLE_CART'

    product_data = get_product_details(query.data, service_url)
    query.message.delete()
    context.bot.send_photo(chat_id=tg_id, photo=product_data['img'], caption=product_data['description'],
                           reply_markup=create_back_keyboard(query.data))
    return 'HANDLE_DESCRIPTION'


def start(update, context):
    service_url = context.bot_data['service_url']
    tg_id = update.effective_chat.id
    cart = strapi.get_cart(tg_id,service_url)
    if not cart:
        create_cart(tg_id, service_url)
    update.message.reply_text(text='Привет!', reply_markup=create_products_keyboard(service_url))
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
        'HANDLE_MENU': handle_menu_selection,
        'HANDLE_DESCRIPTION': handle_product_actions,
        'HANDLE_CART': handle_cart_actions,
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
    global DATABASE
    if DATABASE is None:
        database_host = os.environ['DATABASE_HOST']
        database_port = int(os.environ['DATABASE_PORT'])
        DATABASE = redis.Redis(host=database_host, port=database_port, db=0, decode_responses=True)
    return DATABASE


def main():
    load_dotenv(override=True)
    token = os.environ['TELEGRAM_TOKEN']
    updater = Updater(token)
    db_connection = get_database_connection()
    dispatcher = updater.dispatcher
    dispatcher.bot_data['service_url'] = os.environ['SERVICE_URL']
    dispatcher.bot_data['user_password'] = os.getenv('USER_PASSWORD','6379')
    dispatcher.bot_data['db_connection'] = db_connection
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()