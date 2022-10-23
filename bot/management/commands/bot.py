import logging

from django.core.management.base import BaseCommand
from django.db.models import Q
from telegram import Bot, ReplyKeyboardRemove, Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackContext, MessageHandler, Filters, \
    CallbackQueryHandler
from telegram.utils.request import Request

from bot.models import Category, Room, Person, Fuckup, RoomRequest

REGISTER, MENU, BUTTON, NEW_FUCKUP, FUCKUP, ROOMS_SETTINGS, ROOMS_HANDLER, ROOMS, CREATE_ROOM, SHOW_FUCKUPS, \
FUCKUPS_HANDLER, CATEGORY_HANDLER, NEW_CATEGORY, DELETE_CATEGORY, CREATE_REQUEST = range(
    15)

logger = logging.getLogger(__name__)


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f'Произошла ошибка {e}'
            print(error_message)
            assert e

    return inner()


# Обрабатываем команду /cancel если пользователь отменил разговор
def cancel(update, _):
    # определяем пользователя
    user = update.message.from_user
    # Пишем в журнал о том, что пользователь не разговорчивый
    logger.info("Пользователь %s отменил разговор.", user.first_name)
    # Отвечаем на отказ поговорить
    update.message.reply_text(
        'Мое дело предложить - Ваше отказаться'
        ' Будет скучно - пиши.',
        reply_markup=ReplyKeyboardRemove()
    )
    # Заканчиваем разговор.
    return ConversationHandler.END


# функция начала полльзования точки входа в разговор
def start(update: Update, context: CallbackContext) -> None:
    try:
        Person.objects.get(tg_id=update.message.chat_id)

        reply_keyboard = [['Новая запись', 'Категории'], ['Посмотреть записи', 'Настройки комнат']]
        # Создаем простую клавиатуру для ответа
        markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        update.message.reply_text(
            'Привет, помечай тут всё, а я буду разбираться',
            reply_markup=markup_key, )
        return MENU
    except:
        update.message.reply_text(
            'Вы не зарегистрированы\n'
            'Введите ник: ',
        )
        return REGISTER


def register(update: Update, context: CallbackContext) -> None:
    username = update.message.text
    print(username)
    Person.objects.create(tg_id=update.message.chat_id, username=update.message.text)
    update.message.reply_text(
        'Нажми /start повторно'
    )

    return ConversationHandler.END


def menu(update: Update, context: CallbackContext) -> None:
    ReplyKeyboardRemove()
    reply_keyboard = [['Новая запись', 'Категории'], ['Посмотреть записи', 'Настройки комнат']]

    # Создаем простую клавиатуру для ответа
    markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    update.message.reply_text('Что будем делать?', reply_markup=markup_key)

    return BUTTON


def button(update: Update, context: CallbackContext) -> None:
    if update.message.text == 'Новая запись':
        update.message.reply_text('Введи содержание: ')
        return NEW_FUCKUP

    elif update.message.text == 'Посмотреть записи':
        user = Person.objects.get(tg_id=update.message.chat_id)
        fuckups = Fuckup.objects.filter(room_id=user.current_room_id)

        if fuckups.count() == 0:
            update.message.reply_html('<b>Тут пусто(</b>')
            return MENU

        else:
            update.message.reply_text('Вот списочек:')
            for fuckup in fuckups:
                buttons = [[]]
                if fuckup.status:
                    buttons[0].append(
                        InlineKeyboardButton("Вернуть ❌", callback_data=str(fuckup.id) + '|0x|del|0x|' + str(
                            update.message.chat_id)))
                else:
                    buttons[0].append(
                        InlineKeyboardButton("Решено ✅", callback_data=str(fuckup.id) + '|0x|cho|0x|' + str(
                            update.message.chat_id)))
                reply_markup = InlineKeyboardMarkup(buttons)

                update.message.reply_text(f'{fuckup.content}', reply_markup=reply_markup)

            return BUTTON

    elif update.message.text == 'Категории':
        buttons = [
            [InlineKeyboardButton("Показать", callback_data='sho')],
            [InlineKeyboardButton("Добавить", callback_data='add')],
            [InlineKeyboardButton("Удалить", callback_data='del')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(f'Что делать?', reply_markup=reply_markup)

        return CATEGORY_HANDLER

    elif update.message.text == 'Настройки комнат':
        # Удаляем клавиатуру главного меню
        ReplyKeyboardRemove()

        # Создаем простую клавиатуру для ответа
        reply_keyboard = [['Комнаты', 'Создать'], ['Пригласить', 'Назад']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        update.message.reply_text('Что будем делать?', reply_markup=markup_key)

        return ROOMS


def new_fuckup(update: Update, context: CallbackContext) -> None:
    buttons = []
    count = Category.objects.all().count()
    for i in range(count):
        buttons.append(list())
    print(buttons)
    c = 0
    for cat in Category.objects.all():
        buttons[c].append(
            InlineKeyboardButton(cat.tittle, callback_data=str(
                cat.tittle + "|0x|" + update.message.text + "|0x|" + str(update.message.chat_id))))
        c += 1

    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_html('Категория:', reply_markup=reply_markup)

    return FUCKUP


def fuckup(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    variant = query.data.split('|0x|')
    category_tittle = variant[0]
    content = variant[1]
    user_id = int(variant[2])

    person = Person.objects.get(tg_id=user_id)
    category = Category.objects.get(tittle=category_tittle)

    query.answer()
    Fuckup.objects.create(room_id=person.current_room_id, category=category, content=content, author=person)

    query.edit_message_text(text=f"Добавлено!")

    # было ConversationHandler.END
    return MENU


def category_handler(update: Update, context: CallbackContext) -> None:
    """
    свои категории для каждой комнаты
    """
    query = update.callback_query
    variant = query.data
    if variant == "sho":
        buttons = []
        count = Category.objects.all().count()
        for i in range(count):
            buttons.append(list())
        c = 0
        for cat in Category.objects.all():
            buttons[c].append(
                InlineKeyboardButton(cat.tittle, callback_data=str(
                    cat.tittle + "|0x|" + query.message.text + "|0x|" + str(query.message.chat_id))))
            c += 1

        reply_markup = InlineKeyboardMarkup(buttons)
        query.message.edit_text('Категории:', reply_markup=reply_markup)

        return BUTTON
    elif variant == "add":
        query.message.edit_text('Название новой категории')
        return NEW_CATEGORY

    elif variant == "del":
        categorys = Category.objects.all()
        query.message.edit_text('Категории для удаления:')
        buttons = [[]]
        for category in categorys:
            buttons = [[]]
            buttons[0].append(
                InlineKeyboardButton("Удалить ❌", callback_data=str(category.id)))

            reply_markup = InlineKeyboardMarkup(buttons)

            query.message.reply_text(f'{category.tittle}', reply_markup=reply_markup)
        return DELETE_CATEGORY
    return BUTTON


def new_category(update: Update, context: CallbackContext) -> None:
    try:
        tittle = update.message.text
        person = Person.objects.get(tg_id=update.message.chat_id)
        Category.objects.get_or_create(tittle=tittle, room_id=person.current_room_id)
        update.message.reply_text('Категория добавлена')
    except Exception as e:
        update.message.reply_html(f'Ошибка: {e}')
    return BUTTON


def delete_category_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    variant = query.data
    category_id = int(variant[0])

    query.answer()
    try:
        Category.objects.get(id=category_id).delete()
        query.edit_message_text(text='Категория удалена')
    except Exception as e:
        query.edit_message_text(text=f'Ошибка {e}')

    return BUTTON


def rooms(update: Update, context: CallbackContext) -> None:
    """
    если одна комната ожидает ответа не идёт далльше
    """
    action = update.message.text
    if action == 'Комнаты':
        roms = Room.objects.filter(Q(admins__tg_id=update.message.chat_id) | Q(persons__tg_id=update.message.chat_id))

        update.message.reply_html('Комнаты:')

        for room in roms:
            user = Person.objects.get(tg_id=update.message.chat_id)
            buttons = [[]]
            if user.current_room_id == room.id:
                buttons[0].append(InlineKeyboardButton("Удалить ❌", callback_data=str(room.id) + '|0x|del|0x|' + str(
                    update.message.chat_id)))
            else:
                buttons[0].append(InlineKeyboardButton("Выбрать ✅", callback_data=str(room.id) + '|0x|cho|0x|' + str(
                    update.message.chat_id)))
            reply_markup = InlineKeyboardMarkup(buttons)
            update.message.reply_text(f'{room.tittle}\n'
                                      f'Администраторов: {room.admins.count()}\n'
                                      f'Пользователей: {room.persons.count()}',
                                      reply_markup=reply_markup)
        if roms.count() == 0:
            return ROOMS_SETTINGS
        return ROOMS_HANDLER

    elif action == 'Создать':
        update.message.reply_html('Введи название комнаты:')
        return CREATE_ROOM

    elif action == 'Пригласить':
        update.message.reply_html('Введи ник пользователя:')
        return CREATE_REQUEST

    elif action == 'Назад':
        ReplyKeyboardRemove()
        reply_keyboard = [['Новая запись', 'Категории'], ['Посмотреть записи', 'Настройки комнат']]

        # Создаем простую клавиатуру для ответа
        markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        update.message.reply_text('Что будем делать?', reply_markup=markup_key)

        return BUTTON


def create_room(update: Update, context: CallbackContext) -> None:
    try:
        person = Person.objects.get(tg_id=update.message.chat_id)
        tittle = update.message.text
        room = Room.objects.create(tittle=tittle)
        room.admins.add(person)
        room.save()
    except Exception as e:
        update.message.reply_html(f'Ошибка: {e}')

    return MENU


def rooms_handler(update: Update, context: CallbackContext) -> None:
    """
    при удалении много комнат в фильтре

    """
    query = update.callback_query
    variant = query.data.split('|0x|')
    room_id = int(variant[0])
    chat_id = int(variant[2])
    print()
    query.answer(variant[1])

    if variant[1] == 'del':
        roms = -1
        try:
            roms = Room.objects.get(Q(admins__tg_id=chat_id) & Q(id=room_id))
        except:
            query.message.reply_text(text=f"У тебя нет таких прав!")
            return BUTTON

        if room_id == roms.id:
            p = Room.objects.get(id=room_id)
            p.delete()

            s = Person.objects.get(tg_id=chat_id)
            s.current_room_id = 0
            s.save()

        return BUTTON
    elif variant[1] == 'cho':
        person = Person.objects.get(tg_id=chat_id)
        person.current_room_id = room_id
        person.save()
        return MENU
    else:
        print('kkkkk')
        return MENU


def create_request(update: Update, context: CallbackContext) -> None:
    request_user = update.message.text
    try:
        required_user = Person.objects.get(username=request_user)
        user = Person.objects.get(tg_id=update.message.chat_id)
        RoomRequest.objects.create(room_id=user.current_room_id, required_user=required_user)
    except Exception as e:
        update.message.reply_text(f'Ошибка {e}')
    return MENU


class Command(BaseCommand):
    help = 'Телеграмм бот'

    def handle(self, *args, **options):
        # Correct connection
        request = Request(
            connect_timeout=0.5,
            read_timeout=1.0,
        )
        bot = Bot(
            request=request,
            token='5560031406:AAFuMHPplebg8q4MHJ5Ndla8_ZfO4sd-LCY',
        )
        print(bot.get_me())

        # Updaters
        updater = Updater(
            bot=bot,
            use_context=True,
        )

        # start_handler = CommandHandler("start", start)
        # updater.dispatcher.add_handler(start_handler)

        start_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                REGISTER: [MessageHandler(Filters.text, register)],

            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        updater.dispatcher.add_handler(start_handler)

        fuckup_handler = ConversationHandler(
            # точка входа в разговор
            entry_points=[
                CommandHandler('menu', menu),
                MessageHandler(Filters.regex('^(Новая запись|Категории|Настройки комнат|Посмотреть записи)$'), button)],
            # варианты использованию
            states={
                # работа с меню
                MENU: [MessageHandler(Filters.regex('^(Назад|Меню)$'), menu)],
                BUTTON: [MessageHandler(Filters.regex('^(Новая запись|Категории|Настройки комнат|Посмотреть записи)$'),
                                        button)],
                # работа с заметками
                NEW_FUCKUP: [MessageHandler(Filters.text, new_fuckup)],
                FUCKUP: [CallbackQueryHandler(fuckup)],
                # работа с комнатами
                ROOMS_SETTINGS: [MessageHandler(Filters.regex('^(Назад|Комнаты|Создать|Пригласить)$'), rooms)],
                ROOMS: [MessageHandler(Filters.text, rooms)],
                ROOMS_HANDLER: [CallbackQueryHandler(rooms_handler)],
                # работа с категориями
                CATEGORY_HANDLER: [CallbackQueryHandler(category_handler)],
                CREATE_ROOM: [MessageHandler(Filters.text, create_room)],
                NEW_CATEGORY: [MessageHandler(Filters.text, new_category)],
                DELETE_CATEGORY: [CallbackQueryHandler(delete_category_handler)],
                #
                CREATE_REQUEST: [MessageHandler(Filters.text, create_request)],
            },
            # точка выхода из разговора
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        updater.dispatcher.add_handler(fuckup_handler)

        # Pulling bot
        updater.start_polling()
        updater.idle()
