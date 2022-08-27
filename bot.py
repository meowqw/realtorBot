from distutils import extension
from distutils.errors import DistutilsFileError
from email.mime import message
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import config
from db import db, Users, Objects
from aiogram.types import ParseMode
import logging
import aiogram.utils.markdown as md
import datetime

KEYS = ['key']
OBJECTS = {}

logging.basicConfig(level=logging.INFO)

# bot init
bot = Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# form userForm
class userForm(StatesGroup):
    fullname = State()
    phone = State()
    experience = State()
    job = State()
    key = State()
    region = State()

# form objectsForm


class objectsForm(StatesGroup):
    region = State()
    city = State()
    area = State()
    address = State()
    street = State()
    rooms = State()
    stage = State()
    description = State()
    price = State()
    quadrature = State()
    property_type = State()
    ownership_type = State()
    phone = State()
    
class Filter(StatesGroup):
    city = State()
    area = State()
    rooms = State()
    price = State()


# user data
class UserData(StatesGroup):
    current_object = State()

# REGISTRATION


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    """START HANDLING"""

    # start fullname state
    await userForm.fullname.set()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['user']['start_registration'])
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['user']['enter_fullname'])


@dp.message_handler(state=userForm.fullname)
async def process_fullname(message: types.Message, state: FSMContext):
    """FULLNAME STATE"""

    async with state.proxy() as data:
        data['fullname'] = message.text

    # start phone state
    await userForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['user']['enter_phone'])


@dp.message_handler(state=userForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    """PHONE STATE"""

    async with state.proxy() as data:
        data['phone'] = message.text

    # start expirience state
    await userForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['user']['enter_experience'])


@dp.message_handler(state=userForm.experience)
async def process_experience(message: types.Message, state: FSMContext):
    """EXPERIENCE STATE"""

    async with state.proxy() as data:
        data['experience'] = message.text

    # start job state
    await userForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['user']['enter_job'])


@dp.message_handler(state=userForm.job)
async def process_job(message: types.Message, state: FSMContext):
    """JOB STATE"""

    async with state.proxy() as data:
        data['job'] = message.text

    # start key state
    await userForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['user']['enter_key'])


@dp.message_handler(lambda message: message.text not in KEYS, state=userForm.key)
async def process_check_key(message: types.Message):
    """CHECK KEY"""
    return await message.reply(config.OBJECT_TEXT['user']['exc_key'])


@dp.message_handler(lambda message: message.text in KEYS, state=userForm.key)
async def process_key(message: types.Message, state: FSMContext):
    """KEY STATE"""

    # start region state
    await userForm.next()
    # update key in state
    await state.update_data(key=message.text)
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['user']['enter_region'])


@dp.message_handler(state=userForm.region)
async def process_region(message: types.Message, state: FSMContext):
    """REGION STATE"""

    async with state.proxy() as data:
        data['region'] = message.text

        # save USER data in db
        user = Users(
            id=str(message.chat.id),
            login=message.chat.username,
            fullname=data['fullname'],
            phone=data['phone'],
            experience=data['experience'],
            job=data['job'],
            key=data['key'],
            region=data['region'])

        db.session.add(user)
        db.session.commit()

        # send user data
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text(config.OBJECT_TEXT['user']['finish_registration']),
                md.text('ФИО: ', md.bold(data['fullname'])),
                md.text('Номер: ', md.bold(data['phone'])),
                md.text('Стаж: ', md.bold(data['experience'])),
                md.text('Место работы: ', md.bold(data['job'])),
                md.text('Ключ: ', md.bold(data['key'])),
                md.text('Регион: ', md.bold(data['region'])),
                sep='\n',
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    # finish state
    await state.finish()

# CHECK AUTH USER

# main keyboard
buttons = [config.OBJECT_TEXT['main']['sale_btn'],
           config.OBJECT_TEXT['main']['feed_btn'],
           config.OBJECT_TEXT['main']['my_objects_btn'],
           config.OBJECT_TEXT['main']['notification_btn']]
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(*buttons)


@dp.message_handler(lambda message: Users.query.filter_by(id=message.chat.id).first() != None
                    and message.text not in [config.OBJECT_TEXT['main'][i] for i in config.OBJECT_TEXT['main']])
async def process_auth(message: types.Message):
    """USER AUTH"""

    await message.answer(config.OBJECT_TEXT['user']['login'], reply_markup=main_keyboard)


@dp.message_handler(lambda message: Users.query.filter_by(id=message.chat.id).first() == None
                    and message.text not in [config.OBJECT_TEXT['main'][i] for i in config.OBJECT_TEXT['main']])
async def process_not_auth(message: types.Message):
    """USER NOT AUTH"""
    markup = types.ReplyKeyboardRemove()

    await bot.send_message(
        message.chat.id, config.OBJECT_TEXT['user']['not_login'],
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN,
    )


# FUNCTIONS

@dp.message_handler(Text(equals=config.OBJECT_TEXT['main']['cancel_btn'], ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """CANCEL HANDLER"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['main']['cancel_ok'], reply_markup=main_keyboard)


@dp.message_handler(Text(equals=config.OBJECT_TEXT['main']['back_btn'], ignore_case=True), state='*')
async def back_handler(message: types.Message,  state: FSMContext):
    """BACK HANDLER"""

    await bot.send_message(message.chat.id, config.OBJECT_TEXT['main']['back_ok'], reply_markup=main_keyboard)

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
# ----------------- SALE --------------------

@dp.message_handler(Text(equals=config.OBJECT_TEXT['main']['sale_btn']))
async def function_sale(message: types.Message):
    """FUNCTION SALE (SALE STATE)"""

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(config.OBJECT_TEXT['main']['cancel_btn'])

    # start objects region state
    await objectsForm.region.set()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['start_add'], reply_markup=keyboard)
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_region'])


@dp.message_handler(state=objectsForm.region)
async def process_objects_region(message: types.Message, state: FSMContext):
    """OBJECTS REGION STATE"""

    async with state.proxy() as data:
        data['region'] = message.text

    # start objects city state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_city'])


@dp.message_handler(state=objectsForm.city)
async def process_objects_city(message: types.Message, state: FSMContext):
    """OBJECTS CITY STATE"""

    async with state.proxy() as data:
        data['city'] = message.text

    # start objects address state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_area'])
    
@dp.message_handler(state=objectsForm.area)
async def process_objects_area(message: types.Message, state: FSMContext):
    """OBJECTS AREA STATE"""

    async with state.proxy() as data:
        data['area'] = message.text

    # start objects area state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_address'])


@dp.message_handler(state=objectsForm.address)
async def process_objects_address(message: types.Message, state: FSMContext):
    """OBJECTS ADDRESS STATE"""

    async with state.proxy() as data:
        data['address'] = message.text

    # start objects street state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_street'])


@dp.message_handler(state=objectsForm.street)
async def process_objects_street(message: types.Message, state: FSMContext):
    """OBJECTS STREET STATE"""

    async with state.proxy() as data:
        data['street'] = message.text

    # start objects rooms state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_rooms'])
    
@dp.message_handler(lambda message: not message.text.isdigit(), state=objectsForm.rooms)
async def process_rooms_invalid(message: types.Message):
    return await message.reply(config.OBJECT_TEXT['objects']['exc_rooms'])

@dp.message_handler(lambda message: message.text.isdigit(), state=objectsForm.rooms)
async def process_objects_rooms(message: types.Message, state: FSMContext):
    """OBJECTS ROOMS STATE"""

    async with state.proxy() as data:
        data['rooms'] = message.text

    # start objects stage state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_stage'])


@dp.message_handler(lambda message: not message.text.isdigit(), state=objectsForm.stage)
async def process_stage_invalid(message: types.Message):
    return await message.reply(config.OBJECT_TEXT['objects']['exc_stage'])


@dp.message_handler(lambda message: message.text.isdigit(), state=objectsForm.stage)
async def process_objects_stage(message: types.Message, state: FSMContext):
    """OBJECTS STAGE STATE"""

    async with state.proxy() as data:
        data['stage'] = message.text

    # start objects description state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_description'])


@dp.message_handler(state=objectsForm.description)
async def process_objects_description(message: types.Message, state: FSMContext):
    """OBJECTS DESCRIPTION STATE"""

    async with state.proxy() as data:
        data['description'] = message.text

    # start objects price state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_price'])


@dp.message_handler(lambda message: not message.text.isdigit(), state=objectsForm.price)
async def process_price_invalid(message: types.Message):
    return await message.reply(config.OBJECT_TEXT['objects']['exc_price'])


@dp.message_handler(lambda message: message.text.isdigit(), state=objectsForm.price)
async def process_objects_price(message: types.Message, state: FSMContext):
    """OBJECTS PRICE STATE"""

    async with state.proxy() as data:
        data['price'] = message.text

    # start objects quadrature state
    await objectsForm.next()
    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_quadrature'])


property_type_keyboard = types.InlineKeyboardMarkup(
    resize_keyboard=True, selective=True)
property_type_btn_1 = types.InlineKeyboardButton(
    'Вторичка', callback_data='property_type_btn_1')
property_type_btn_2 = types.InlineKeyboardButton(
    'Первичка', callback_data='property_type_btn_2')
property_type_btn_3 = types.InlineKeyboardButton(
    'Новострой', callback_data='property_type_btn_3')
property_type_keyboard.add(
    property_type_btn_1, property_type_btn_2, property_type_btn_3)

ownership_type_keyboard = types.InlineKeyboardMarkup(
    resize_keyboard=True, selective=True)
ownership_type_btn_1 = types.InlineKeyboardButton(
    'Частная', callback_data='ownership_type_btn_1')
ownership_type_btn_2 = types.InlineKeyboardButton(
    'Государственная', callback_data='ownership_type_btn_2')
ownership_type_keyboard.add(ownership_type_btn_1, ownership_type_btn_2)


@dp.message_handler(lambda message: not message.text.replace(',', '.').replace('.', '').isdigit(), state=objectsForm.quadrature)
async def process_quadrature_invalid(message: types.Message):
    return await message.reply(config.OBJECT_TEXT['objects']['exc_quadrature'])


@dp.message_handler(lambda message: message.text.replace(',', '.').replace('.', '').isdigit(), state=objectsForm.quadrature)
async def process_objects_quadrature(message: types.Message, state: FSMContext):
    """OBJECTS QUADRATURE STATE"""

    async with state.proxy() as data:
        data['quadrature'] = message.text

    # start objects property type state
    await objectsForm.next()

    await bot.send_message(message.chat.id, config.OBJECT_TEXT['objects']['enter_property_type'], reply_markup=property_type_keyboard)


@dp.callback_query_handler(Text(startswith="property_type_btn_"), state=objectsForm.property_type)
async def callbacks_property_type(call: types.CallbackQuery, state: FSMContext):
    """CALLBACK PROPERTY TYPE"""
    action = call.data.split('_')[-1]

    if action == "1":
        p_type = 'Вторичка'
    elif action == "2":
        p_type = 'Первичка'
    elif action == "3":
        p_type = 'Новострой'

    async with state.proxy() as data:
        data['property_type'] = p_type

    # start objects ownership type type state
    await objectsForm.next()

    await call.answer()

    await bot.send_message(call.message.chat.id, p_type)
    await bot.send_message(call.message.chat.id, config.OBJECT_TEXT['objects']['enter_ownership_type'], reply_markup=ownership_type_keyboard)


@dp.callback_query_handler(Text(startswith="ownership_type_btn_"), state=objectsForm.ownership_type)
async def callbacks_ownership_type(call: types.CallbackQuery, state: FSMContext):
    """CALLBACK OWNERSHIP TYPE"""
    action = call.data.split('_')[-1]

    if action == "1":
        o_type = 'Частная'
    elif action == "2":
        o_type = 'Государственная'

    async with state.proxy() as data:
        data['ownership_type'] = o_type

    # start objects phone state
    await objectsForm.next()

    await call.answer()

    await bot.send_message(call.message.chat.id, o_type)
    await bot.send_message(call.message.chat.id, config.OBJECT_TEXT['objects']['enter_phone'])


@dp.message_handler(state=objectsForm.phone)
async def process_objects_phone(message: types.Message, state: FSMContext):
    """OBJECTS PHONE STATE AND SAVE STATE DATA IN DB OBJECTS"""

    async with state.proxy() as data:
        data['phone'] = message.text

        # save Objects data in db
        object = Objects(
            user=str(message.chat.id),
            region=data['region'],
            city=data['city'],
            area=data['area'],
            address=data['address'],
            street=data['street'],
            rooms = data['rooms'],
            stage=data['stage'],
            description=data['description'],
            price=data['price'],
            quadrature=data['quadrature'],
            property_type=data['property_type'],
            ownership_type=data['ownership_type'],
            phone=data['phone'])

        db.session.add(object)
        db.session.commit()

        # send object data
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text(config.OBJECT_TEXT['objects']['finish_add']),
                md.text('Регион: ', md.bold(data['region'])),
                md.text('Город: ', md.bold(data['city'])),
                md.text('Район: ', md.bold(data['area'])),
                md.text('Адрес: ', md.bold(data['address'])),
                md.text('Улица: ', md.bold(data['street'])),
                md.text('Кол-во комнат: ', md.bold(data['rooms'])),
                md.text('Этаж: ', md.bold(data['stage'])),
                md.text('Описание: ', md.bold(data['description'])),
                md.text('Цена: ', md.bold(data['price'] + ' р')),
                md.text('Квадратура: ', md.bold(data['quadrature'] + ' м2')),
                md.text('Тип недвижимости: ', md.bold(data['property_type'])),
                md.text('Тип собственности: ', md.bold(
                    data['ownership_type'])),
                md.text('Телефон: ', md.bold(data['phone'])),
                sep='\n',
            ),
            reply_markup=main_keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

    # finish state
    await state.finish()

# ----------------- FEED --------------------

@dp.message_handler(Text(equals=config.OBJECT_TEXT['main']['feed_btn']))
async def function_feed(message: types.Message):
    """FUNCTION FEED"""

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(config.OBJECT_TEXT['main']['back_btn'])

    await bot.send_message(message.chat.id, "Лента", reply_markup=keyboard)
    
    # filter switch
    filter_keyboard = types.InlineKeyboardMarkup(
        resize_keyboard=True, selective=True)
    
    filter_keyboard.add(*[
        types.InlineKeyboardButton(
            f'Да', callback_data=f'filter_yes'),
        types.InlineKeyboardButton(
            f'Нет', callback_data=f'filter_no')
    ])
    
    await bot.send_message(message.chat.id, "Применить фильтр к ленте", reply_markup=filter_keyboard)

def render_all_feed():
    """FEED. RENDER ALL OBJECTS"""
    feed_keyboard = types.InlineKeyboardMarkup(
        resize_keyboard=True, selective=True, row_width=1)
    my_objects = Objects.query.all()
    buttons = []
    for object in my_objects:
        buttons.append(types.InlineKeyboardButton(f'{object.region}, {object.address}, {object.street}, {object.price}',
                                                  callback_data=f'feed_object_{object.id}'))

    feed_keyboard.add(*buttons)
    return feed_keyboard

@dp.callback_query_handler(Text(startswith="filter_"))
async def callback_filter_switch(call: types.CallbackQuery):
    """CALLBACK FILTER SWITCH"""

    action = call.data.split('_')[-1]
        
    if action == 'yes':
        print('yes')
    elif action == 'no':
        # get objects without filter
        await bot.send_message(call.message.chat.id, "Все объекты", reply_markup=render_all_feed())
        
        
    
    
# -------------------- MY OBJECTS ------------------------

def render_all_objects(id):
    """RENDER ALL MY OBJECTS"""
    objects_keyboard = types.InlineKeyboardMarkup(
        resize_keyboard=True, selective=True, row_width=1)
    my_objects = Objects.query.filter_by(user=id).all()
    buttons = []
    for object in my_objects:
        buttons.append(types.InlineKeyboardButton(f'{object.region}, {object.address}, {object.street}, {object.price}',
                                                  callback_data=f'object_{object.id}'))

    objects_keyboard.add(*buttons)
    return objects_keyboard

@dp.message_handler(Text(equals=config.OBJECT_TEXT['main']['my_objects_btn']))
async def function_my_objects(message: types.Message):
    """FUNCTION MY OBJECTS"""

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(config.OBJECT_TEXT['main']['back_btn'])

    await bot.send_message(message.chat.id, config.OBJECT_TEXT['main']['my_objects_btn'], reply_markup=keyboard)
    objects_keyboard = render_all_objects(message.chat.id)
    
    msg = await bot.send_message(message.chat.id, "Все объекты", reply_markup=objects_keyboard)
    OBJECTS[message.chat.id] = {'object_list': msg}


@dp.callback_query_handler(Text(startswith="object_"))
async def callbacks_my_object(call: types.CallbackQuery):
    """CALLBACK MY OBJECT"""

    action = call.data.split('_')[-1]
    object = Objects.query.filter_by(id=int(action)).first()
    object_control_keyboard = types.InlineKeyboardMarkup(
        resize_keyboard=True, selective=True)

    if 'current_object' in OBJECTS[call.message.chat.id]:
        await OBJECTS[call.message.chat.id]['current_object'].delete()
        
    # add buttons
    object_control_keyboard.add(*[
        types.InlineKeyboardButton(
            f'Продлить', callback_data=f'extend_object_{object.id}'),
        types.InlineKeyboardButton(
            f'Удалить', callback_data=f'del_object_{object.id}')
    ])
    
    # send object data
    message_object_id = await bot.send_message(
        call.message.chat.id,
        md.text(
            md.text('Регион: ', md.bold(object.region)),
            md.text('Город: ', md.bold(object.city)),
            md.text('Район: ', md.bold(object.area)),
            md.text('Адрес: ', md.bold(object.address)),
            md.text('Улица: ', md.bold(object.street)),
            md.text('Кол-во комнат: ', md.bold(object.rooms)),
            md.text('Этаж: ', md.bold(object.stage)),
            md.text('Описание: ', md.bold(object.description)),
            md.text('Цена: ', md.bold(str(object.price) + ' р')),
            md.text('Квадратура: ', md.bold(
                str(object.quadrature) + ' м2')),
            md.text('Тип недвижимости: ', md.bold(object.property_type)),
            md.text('Тип собственности: ', md.bold(object.ownership_type)),
            md.text('Телефон: ', md.bold(object.phone)),
            md.text('Дейтвительно до: ', md.bold(str(object.date_end))),
            
            sep='\n',
        ),
        reply_markup=object_control_keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )

    # save current object
    OBJECTS[call.message.chat.id]['current_object'] = message_object_id

@dp.callback_query_handler(Text(startswith="del_object_"))
async def callback_delete_my_object(call: types.CallbackQuery):
    """CALLBACK DELETE OBJECT"""
    action = call.data.split('_')[-1]
    
    if 'current_object' in OBJECTS[call.message.chat.id]:
        await OBJECTS[call.message.chat.id]['current_object'].delete()
    
    # del rec DB
    Objects.query.filter_by(id=int(action)).delete()
    db.session.commit()
    
    # rerender my object form 
    await OBJECTS[call.message.chat.id]['object_list'].delete()
    objects_keyboard = render_all_objects(call.message.chat.id)
    
    msg = await bot.send_message(call.message.chat.id, "Все объекты", reply_markup=objects_keyboard)
    
    # save current object list
    OBJECTS[call.message.chat.id] = {'object_list': msg}
    

@dp.callback_query_handler(Text(startswith="extend_object_"))
async def callback_extend_my_object(call: types.CallbackQuery):
    """CALLBACK EXTEND OBJECT"""
    action = call.data.split('_')[-1]
    
    if 'current_object' in OBJECTS[call.message.chat.id]:
        await OBJECTS[call.message.chat.id]['current_object'].delete()
    
    # update rec DB
    object = Objects.query.filter_by(id=int(action)).first()
    object.date_end += datetime.timedelta(days=30)
    db.session.commit()
    
    del OBJECTS[call.message.chat.id]['current_object']
    
    

@dp.message_handler(Text(equals=config.OBJECT_TEXT['main']['notification_btn']))
async def function_notifications(message: types.Message):
    """FUNCTION NOTIFICATIONS"""

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(config.OBJECT_TEXT['main']['back_btn'])

    await message.reply("Уведомления", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
