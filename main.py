# bot.py
import logging
import asyncio
import aiofiles
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import ChatTypeFilter
import requests
import os
from config import TOKEN, ADMIN_ID, BASE_CHANNEL
from db import (init_db, add_user, increment_request, get_user_requests_today, get_user_count, 
               get_total_requests, ban_user, unban_user, is_banned, get_all_users, add_channel, 
               remove_channel, get_channels, add_api_key, remove_api_key, get_api_keys, 
               increment_key_request, get_least_used_key, set_daily_limit, get_daily_limit, 
               get_bot_info, is_premium, set_notifications, get_notifications, get_premium_users, 
               remove_premium_user, set_start_message, get_start_message, set_about_button, get_about_button)
from keyboards import (get_start_keyboard, get_main_admin_menu, get_back_button, get_home_button,
                      get_user_profile_button, get_subscription_keyboard, get_channel_management_keyboard, 
                      get_key_management_keyboard, get_user_management_keyboard, get_settings_keyboard,
                      get_notifications_keyboard, get_premium_users_keyboard)
from premium import (handle_premium_purchase, handle_payment_proceed, handle_payment_done, 
                    process_cheque, handle_cheque_action)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class AdminStates(StatesGroup):
    ban_user = State()
    ban_reason = State()
    unban_user = State()
    broadcast = State()
    add_channel_name = State()
    add_channel_link = State()
    remove_channel = State()
    add_key = State()
    remove_key = State()
    set_limit = State()
    ban_premium = State()
    ban_premium_reason = State()
    remove_premium = State()
    set_start_message = State()
    set_about_button = State()

class UserStates(StatesGroup):
    waiting_for_cheque = State()

init_db()

async def check_subscription(user_id):
    if is_premium(user_id):
        return True
    channels = get_channels()
    if not channels:
        return True
    for channel_id, _, _ in channels:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logging.error(f"{user_id} uchun {channel_id} kanalida obuna tekshirish xatosi: {e}")
            return False
    return True

@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Ismsiz"
    
    if banned := is_banned(user_id):
        await message.answer(f"<b>⛔ Siz chopilgansiz.</b>\nSabab: {banned[1]}", parse_mode="HTML")
        return
    
    add_user(user_id, username)
    start_message_id = get_start_message()
    about_button_name, about_button_url = get_about_button()
    
    if start_message_id:
        try:
            await bot.copy_message(user_id, ADMIN_ID, start_message_id, reply_markup=get_start_keyboard(about_button_name, about_button_url))
        except Exception as e:
            logging.error(f"Start habarini ko‘chirish xatosi: {e}")
            await message.answer("<b>⚠️ Miyya biroz charchadiov</b>", parse_mode="HTML")
            await send_default_start_message(message, about_button_name, about_button_url)
    else:
        await send_default_start_message(message, about_button_name, about_button_url)

async def send_default_start_message(message: types.Message, about_button_name, about_button_url):
    user_id = message.from_user.id
    text = (f"""
<b>Hush ko'rdik mehmon 😉</b>

<i>🪓 Men sizga rasmingizni orqa fonini chopib tashlashda yordam beraman 
shunchaki rasm yuborib sinab ko'rishingiz mumkin </i>

<blockquote>Unutmang kunlik limit{get_daily_limit()} ta halos</blockquote>

""")
    if user_id == ADMIN_ID:
        text += "\n\n<b>🔧 Admin:</b> /admin buyrug'i bilan boshqaruv paneliga kiring."
    await message.answer(text, parse_mode="HTML", reply_markup=get_start_keyboard(about_button_name, about_button_url))

@dp.message_handler(lambda message: message.chat.type != types.ChatType.PRIVATE)
async def restrict_group(message: types.Message):
    await message.answer(f"""
<b>⚠️ Bu bot faqat shaxsiy chatda ishlaydi.
Gruppada ishlatib mazgimi qotirmela</b>""", parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "check_subscription")
async def process_subscription_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(user_id):
        await bot.edit_message_text(
            "<b>✊🏻 Addushi yurakdasiz obuna bo'ldingiz</b>",
            callback.message.chat.id, callback.message.message_id,
            parse_mode="HTML", reply_markup=get_home_button()
        )
    else:
        await callback.answer("Iltimos, kanallarga obuna bo'ling.", show_alert=True)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "home")
async def process_home(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    about_button_name, about_button_url = get_about_button()
    start_message_id = get_start_message()
    
    if start_message_id:
        try:
            await bot.copy_message(callback.message.chat.id, ADMIN_ID, start_message_id, 
                                 reply_markup=get_start_keyboard(about_button_name, about_button_url))
            await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except Exception as e:
            logging.error(f"Start habarini ko‘chirish xatosi: {e}")
            await send_default_home_message(callback, about_button_name, about_button_url)
    else:
        await send_default_home_message(callback, about_button_name, about_button_url)
    await callback.answer()

async def send_default_home_message(callback: types.CallbackQuery, about_button_name, about_button_url):
    user_id = callback.from_user.id
    text = (f"""
<b>Yana bir bor salom radno'y</b>

<i>Shunchaki biror bir rasim yuboring men u rasmning orqa fo'nini uchirvoraman ...</i>

<blockquote>Kuniga - {get_daily_limit()} ta so'rov yuboro'ras, cho'chimasdan</blockquote>
""")
    if user_id == ADMIN_ID:
        text += "\n\n<b>Xojaka</b> /admin buyrug'i bilan kiriniloradi "
    await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                              parse_mode="HTML", reply_markup=get_start_keyboard(about_button_name, about_button_url))

@dp.callback_query_handler(lambda c: c.data == "notifications")
async def process_notifications(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_premium(user_id):
        notifications_status = get_notifications(user_id)
        await bot.edit_message_text(
            "<b>🔔 Bildirishnomalarni Sozlash</b>\nReklama xabarlarini boshqarish:",
            callback.message.chat.id, callback.message.message_id,
            parse_mode="HTML", reply_markup=get_notifications_keyboard(is_premium=True, notifications_status=notifications_status)
        )
    else:
        await handle_premium_purchase(callback)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data in ["notifications_on", "notifications_off"])
async def toggle_notifications(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_premium(user_id):
        await handle_premium_purchase(callback)
        return
    
    current_status = get_notifications(user_id)
    new_status = 1 if callback.data == "notifications_on" else 0
    
    if current_status == new_status:
        alert_text = "Allaqachon yoniq!" if new_status else "Allaqachon o‘chiq!"
        await callback.answer(alert_text, show_alert=True)
    else:
        set_notifications(user_id, new_status)
        text = "<b>✅ Bildirishnomalar yoqildi.</b>" if new_status else "<b>❌ Bildirishnomalar o‘chirildi.</b>"
        await bot.edit_message_text(
            text, callback.message.chat.id, callback.message.message_id,
            parse_mode="HTML", reply_markup=get_notifications_keyboard(is_premium=True, notifications_status=new_status)
        )
    await callback.answer()

@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("<b>San admin massan san Xtoyliksan 🇨🇳😅</b>", parse_mode="HTML")
        return
    await message.answer(f"""
<b>Tuzimila akatoy 😄</b>

Admin panelniyam yororgansizda oma 😅""", parse_mode="HTML", reply_markup=get_main_admin_menu())

@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), content_types=['photo'])
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if banned := is_banned(user_id):
        await message.answer(f"<b>⛔ Siz chopilgansiz.</b>\nSabab: {banned[1]}", parse_mode="HTML")
        return
    
    if not await check_subscription(user_id):
        channels = get_channels()
        await message.answer("<b>😊 Botdan foydalanish uchun atiga shu kanalga obuna bo'ling</b>\n\n<blockquote>Shu ozgina kanalgayam obuna bo'lomasez yashame qo'yorin</blockquote>", 
                           parse_mode="HTML", reply_markup=get_subscription_keyboard(channels))
        return
    
    if not is_premium(user_id):
        daily_limit = get_daily_limit()
        today_requests = get_user_requests_today(user_id)
        if today_requests >= daily_limit:
            about_button_name, about_button_url = get_about_button()
            await message.answer(f"""
<b>⛔ Yaqinm limitiz tugab qoldida.</b>
Limitni cheksiz qilish uchun Premium sotib oling!""",
                parse_mode="HTML", reply_markup=get_start_keyboard(about_button_name, about_button_url)
            )
            return
    
    processing_msg = await message.answer("<b>✨ Qayta ishlanmoqda...</b>", parse_mode="HTML")
    
    photo = message.photo[-1]
    file_path = f"temp_{user_id}.jpg"
    try:
        await photo.download(destination_file=file_path)
        
        caption = (f"<b>👤 Foydalanuvchi ID:</b> {user_id}\n"
                   f"<b>Foydalanuvchi nomi:</b> @{message.from_user.username or 'Ismsiz'}\n"
                   f"<b>Sana:</b> {message.date}")
        async with aiofiles.open(file_path, 'rb') as photo_file:
            await bot.send_photo(BASE_CHANNEL, photo_file, caption=caption,
                               parse_mode="HTML", reply_markup=get_user_profile_button(user_id))
        
        api_key = get_least_used_key()
        if not api_key:
            await bot.edit_message_text(f"""
<b>⚠️😎 Ozgina prablema chiqb qoldide </b>

@pyfotuz - ga yozin hal qvoradi..""", 
                                      processing_msg.chat.id, processing_msg.message_id, parse_mode="HTML")
            os.remove(file_path)
            return
        
        async with aiofiles.open(file_path, 'rb') as photo_file:
            file_content = await photo_file.read()
        
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': ('image.jpg', file_content)},
            data={'size': 'auto'},
            headers={'X-Api-Key': api_key}
        ))
        
        if response.status_code == 200:
            output_path = f"output_{user_id}.png"
            async with aiofiles.open(output_path, 'wb') as out:
                await out.write(response.content)
            
            await message.delete()
            media = types.MediaGroup()
            media.attach_photo(types.InputFile(file_path), "<b>📸 Asl Rasm</b>", parse_mode="HTML")
            media.attach_photo(types.InputFile(output_path), "<b>✅ Tayyor Rasm</b>", parse_mode="HTML")
            await bot.send_media_group(message.chat.id, media, caption=f"""
<b>😊 Rasimingiz tayyor - yana rasm tashlaysizmi ?</b>

<blockquote>Bilaman hali ham pyfot.uz haqida bilmaysiz 😒</blockquote>""")
            
            await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
            os.remove(output_path)
            increment_request(user_id)
            increment_key_request(api_key)
        else:
            await bot.edit_message_text(f"<b>❌ Xatolik:</b> {response.text}", 
                                      processing_msg.chat.id, processing_msg.message_id, parse_mode="HTML")
    except Exception as e:
        logging.error(f"{user_id} uchun rasm qayta ishlash xatosi: {e}")
        await bot.edit_message_text("<b>⚠️ Qayta ishlashda xatolik.</b> Qayta urinib ko'ring.", 
                                  processing_msg.chat.id, processing_msg.message_id, parse_mode="HTML")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@dp.callback_query_handler(lambda c: c.data == "buy_premium")
async def buy_premium(callback: types.CallbackQuery):
    await handle_premium_purchase(callback)

@dp.callback_query_handler(lambda c: c.data == "proceed_payment")
async def proceed_payment(callback: types.CallbackQuery):
    await handle_payment_proceed(callback)

@dp.callback_query_handler(lambda c: c.data == "payment_done")
async def payment_done(callback: types.CallbackQuery, state: FSMContext):
    await handle_payment_done(callback)
    await UserStates.waiting_for_cheque.set()

@dp.message_handler(content_types=['photo'], state=UserStates.waiting_for_cheque)
async def handle_cheque(message: types.Message, state: FSMContext):
    await process_cheque(message, state)

@dp.callback_query_handler(lambda c: c.data.startswith(("accept_premium", "reject_premium", "ban_premium")))
async def cheque_action(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(" San admin massan , sen xitoyliksan 🇨🇳😅", show_alert=True)
        return
    await handle_cheque_action(callback, state)

@dp.callback_query_handler(lambda c: c.data.startswith("admin_"))
async def process_admin_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(" San admin massan , sen xitoyliksan🇨🇳😅", show_alert=True)
        return
    
    action = callback.data.split("_")[1]
    
    try:
        if action == "stats":
            user_count = get_user_count()
            total_requests = get_total_requests()
            bot_info = get_bot_info()
            text = (f"<b>📊 Statistika</b>\n\n"
                    f"👥 Foydalanuvchilar: {user_count}\n"
                    f"📈 So'rovlar: {total_requests}\n"
                    f"<b>Bot Haqida:</b>\n"
                    f"Nomi: {bot_info['nomi']}\n"
                    f"Ishga tushgan: {bot_info['ishga_tushgan_sana']}\n"
                    f"Versiya: {bot_info['versiya']}\n"
                    f"Ishlab chiqaruvchi: {bot_info['ishlab_chiqaruvchi']}")
            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                      parse_mode="HTML", reply_markup=get_back_button())
        
        elif action == "users":
            await bot.edit_message_text("<b>👥 Foydalanuvchilarni Boshqarish</b>", callback.message.chat.id, 
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_user_management_keyboard())
        
        elif action == "ban":
            await bot.edit_message_text("<b>🚫 Ban qilish uchun foydalanuvchi ID sini kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.ban_user.set()
        
        elif action == "unban":
            await bot.edit_message_text("<b>✅ Bandan chiqarish uchun foydalanuvchi ID sini kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.unban_user.set()
        
        elif action == "premium" and callback.data == "admin_premium_users":
            premium_users = get_premium_users()
            text = "<b>💎 Premium Foydalanuvchilar:</b>\n\n"
            if premium_users:
                for user_id, start_date, end_date in premium_users:
                    text += f"ID: {user_id} | Boshlangan: {start_date} | Tugaydi: {end_date}\n"
            else:
                text += "Hozircha premium foydalanuvchilar yo‘q."
            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                      parse_mode="HTML", reply_markup=get_premium_users_keyboard())
        
        elif action == "ban" and callback.data == "admin_ban_premium":
            await bot.edit_message_text("<b>🚫 Premium foydalanuvchini ban qilish uchun ID kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.ban_premium.set()
        
        elif action == "remove" and callback.data == "admin_remove_premium":
            await bot.edit_message_text("<b>❌ Premium holatini olib tashlash uchun ID kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.remove_premium.set()
        
        elif action == "broadcast":
            await bot.edit_message_text("<b>📢 E'lon xabarini kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.broadcast.set()
        
        elif action == "channels":
            channels = get_channels()
            text = "<b>📺 Kanallar:</b>\n" + "\n".join([f"{name}: {link}" for _, name, link in channels]) or "Kanal yo'q."
            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                      parse_mode="HTML", reply_markup=get_channel_management_keyboard())
        
        elif action == "add" and callback.data == "admin_add_channel":
            await bot.edit_message_text("<b>➕ Kanal nomini kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.add_channel_name.set()
        
        elif action == "remove" and callback.data == "admin_remove_channel":
            channels = get_channels()
            text = "<b>➖ O'chirish uchun kanal ID sini kiriting:</b>\n" + "\n".join([f"ID: {cid} - {name}" for cid, name, _ in channels])
            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                      parse_mode="HTML", reply_markup=get_channel_management_keyboard())
            await AdminStates.remove_channel.set()
        
        elif action == "keys":
            keys = get_api_keys()
            text = "<b>🔑 API Kalitlari:</b>\n" + "\n".join([f"{key}: {req} so'rov ({date})" for key, req, date in keys]) or "Kalit yo'q."
            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                      parse_mode="HTML", reply_markup=get_key_management_keyboard())
        
        elif action == "add" and callback.data == "admin_add_key":
            await bot.edit_message_text("<b>➕ API kalitini kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.add_key.set()
        
        elif action == "remove" and callback.data == "admin_remove_key":
            keys = get_api_keys()
            text = "<b>➖ O'chirish uchun kalitni kiriting:</b>\n" + "\n".join([f"{key}: {req} so'rov" for key, req, _ in keys])
            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                      parse_mode="HTML", reply_markup=get_key_management_keyboard())
            await AdminStates.remove_key.set()
        
        elif action == "settings":
            limit = get_daily_limit()
            about_button_name, about_button_url = get_about_button()
            start_message_id = get_start_message()
            text = (f"<b>⚙️ Sozlamalar</b>\n\n"
                    f"➛ Kunlik Limit: {limit} so'rov/kun\n"
                    f"➛ Start Habari: {'O‘rnatilgan' if start_message_id else 'Default'}\n"
                    f"➛ Bot Haqida Tugmasi: {about_button_name} ({about_button_url})")
            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id,
                                      parse_mode="HTML", reply_markup=get_settings_keyboard())
        
        elif action == "set" and callback.data == "admin_set_limit":
            await bot.edit_message_text("<b>📏 Yangi kunlik limitni kiriting:</b>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.set_limit.set()
        
        elif action == "set" and callback.data == "admin_set_start_message":
            await bot.edit_message_text("<b>✍️ Yangi /start habarini yuboring:</b>\nXabarni shu chatga yuboring.", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.set_start_message.set()
        
        elif action == "set" and callback.data == "admin_set_about_button":
            await bot.edit_message_text("<b>🔗 Bot Haqida tugmasi uchun nom va URL kiriting:</b>\nMasalan: 'Bot Haqida' https://example.com", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_back_button())
            await AdminStates.set_about_button.set()
        
        elif action == "back":
            await bot.edit_message_text("<b>ッ Salom jiar ✌🏻</b>\n\n<i>Bugun nimalar qib tashimizi oshna</i>", callback.message.chat.id,
                                      callback.message.message_id, parse_mode="HTML", reply_markup=get_main_admin_menu())
            await state.finish()
    except Exception as e:
        logging.error(f"Admin tugmasi xatosi: {e}")
        await bot.send_message(callback.message.chat.id, "<b>⚠️ Xatolik yuz berdi.</b>", parse_mode="HTML", reply_markup=get_back_button())
        await state.finish()
    await callback.answer()

@dp.message_handler(state=AdminStates.ban_user)
async def process_ban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(ban_user_id=user_id)
        await bot.send_message(message.chat.id, f"<b>🚫 {user_id} ni ban qilish sababini kiriting:</b>", 
                             parse_mode="HTML", reply_markup=get_back_button())
        await AdminStates.ban_reason.set()
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Noto'g'ri ID.</b> Qayta urinib ko'ring.", parse_mode="HTML", reply_markup=get_back_button())
        await state.finish()

@dp.message_handler(state=AdminStates.ban_reason)
async def process_ban_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("ban_user_id")
    reason = message.text
    ban_user(user_id, reason)
    await bot.send_message(message.chat.id, f"<b>✅ {user_id} ban qilindi.</b>\nSabab: {reason}", 
                         parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.ban_premium)
async def process_ban_premium(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(ban_user_id=user_id)
        await bot.send_message(message.chat.id, f"<b>🚫 {user_id} ni ban qilish sababini kiriting:</b>", 
                             parse_mode="HTML", reply_markup=get_back_button())
        await AdminStates.ban_premium_reason.set()
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Noto'g'ri ID.</b> Qayta urinib ko'ring.", parse_mode="HTML", reply_markup=get_back_button())
        await state.finish()

@dp.message_handler(state=AdminStates.ban_premium_reason)
async def process_ban_premium_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("ban_user_id")
    reason = message.text
    ban_user(user_id, reason)
    remove_premium_user(user_id)
    await bot.send_message(message.chat.id, f"<b>✅ {user_id} ban qilindi va premium olib tashlandi.</b>\nSabab: {reason}", 
                         parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.remove_premium)
async def process_remove_premium(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        remove_premium_user(user_id)
        await bot.send_message(message.chat.id, f"<b>✅ {user_id} dan premium holati olib tashlandi.</b>", 
                             parse_mode="HTML", reply_markup=get_back_button())
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Noto'g'ri ID.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Premium olib tashlash xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Xatolik yuz berdi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.unban_user)
async def process_unban(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        unban_user(user_id)
        await bot.send_message(message.chat.id, f"<b>✅ {user_id} bandan chiqarildi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Noto'g'ri ID.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Bandan chiqarish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Bandan chiqarishda xatolik.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    users = get_all_users()
    success_count = 0
    failed_count = 0
    
    for user_id in users:
        try:
            if not is_banned(user_id):
                if is_premium(user_id) and get_notifications(user_id) == 1:
                    await bot.copy_message(user_id, message.chat.id, message.message_id)
                    success_count += 1
                elif not is_premium(user_id) and await check_subscription(user_id):
                    await bot.copy_message(user_id, message.chat.id, message.message_id)
                    success_count += 1
                else:
                    failed_count += 1
        except Exception as e:
            logging.error(f"{user_id} ga e'lon yuborish xatosi: {e}")
            failed_count += 1
    
    await bot.send_message(message.chat.id, f"<b>📢 E'lon yuborildi!</b>\n\n‣ ✅ Yuborildi: {success_count}\n‣ ❌ Xatolik: {failed_count}", 
                         parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.add_channel_name)
async def process_add_channel_name(message: types.Message, state: FSMContext):
    channel_name = message.text.strip()
    await state.update_data(channel_name=channel_name)
    await bot.send_message(message.chat.id, f"<b>➕ '{channel_name}' uchun kanal ID va havolasini kiriting</b> (masalan, -1001234567890 https://t.me/Kanal):", 
                         parse_mode="HTML", reply_markup=get_back_button())
    await AdminStates.add_channel_link.set()

@dp.message_handler(state=AdminStates.add_channel_link)
async def process_add_channel_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_name = data.get("channel_name")
    try:
        channel_id, link = message.text.strip().split(" ", 1)
        channel_id = int(channel_id)
        add_channel(channel_id, channel_name, link)
        await bot.send_message(message.chat.id, f"<b>✅ '{channel_name}' kanali qo'shildi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Noto'g'ri format.</b> ID va Havola kiriting", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Kanal qo'shish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Kanal qo'shishda xatolik.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.remove_channel)
async def process_remove_channel(message: types.Message, state: FSMContext):
    try:
        channel_id = int(message.text)
        remove_channel(channel_id)
        await bot.send_message(message.chat.id, f"<b>✅ {channel_id} kanali o'chirildi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Noto'g'ri ID.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Kanal o'chirish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Kanal o'chirishda xatolik.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.add_key)
async def process_add_key(message: types.Message, state: FSMContext):
    key = message.text.strip()
    try:
        add_api_key(key)
        await bot.send_message(message.chat.id, "<b>✅ Kalit qo'shildi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Kalit qo'shish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Kalit qo'shishda xatolik.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.remove_key)
async def process_remove_key(message: types.Message, state: FSMContext):
    key = message.text.strip()
    try:
        remove_api_key(key)
        await bot.send_message(message.chat.id, "<b>✅ Kalit o'chirildi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Kalit o'chirish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Kalit o'chirishda xatolik.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.set_limit)
async def process_set_limit(message: types.Message, state: FSMContext):
    try:
        limit = int(message.text)
        if limit < 1:
            raise ValueError
        set_daily_limit(limit)
        await bot.send_message(message.chat.id, f"<b>✅ Kunlik limit {limit} ga o'rnatildi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Musbat son kiriting.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Limit o'rnatish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Limit o'rnatishda xatolik.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.set_start_message)
async def process_set_start_message(message: types.Message, state: FSMContext):
    try:
        set_start_message(message.message_id)
        await bot.send_message(message.chat.id, "<b>✅ Start habari o‘rnatildi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Start habarini o‘rnatish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Xatolik yuz berdi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

@dp.message_handler(state=AdminStates.set_about_button)
async def process_set_about_button(message: types.Message, state: FSMContext):
    try:
        name, url = message.text.strip().split(" ", 1)
        set_about_button(name, url)
        await bot.send_message(message.chat.id, f"<b>✅ Bot Haqida tugmasi o‘rnatildi:</b> {name} ({url})", 
                             parse_mode="HTML", reply_markup=get_back_button())
    except ValueError:
        await bot.send_message(message.chat.id, "<b>❌ Noto‘g‘ri format.</b> Nom va URL ni kiriting.", parse_mode="HTML", reply_markup=get_back_button())
    except Exception as e:
        logging.error(f"Bot Haqida tugmasini o‘rnatish xatosi: {e}")
        await bot.send_message(message.chat.id, "<b>❌ Xatolik yuz berdi.</b>", parse_mode="HTML", reply_markup=get_back_button())
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)