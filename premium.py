# premium.py
import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from datetime import datetime
from config import ADMIN_ID, ADMIN_GROUP
from db import add_premium_user, is_premium, get_premium_info, ban_user, remove_premium_user
from keyboards import get_premium_info_keyboard, get_payment_keyboard, get_cheque_keyboard, get_premium_status_keyboard

async def handle_premium_purchase(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if premium_info := is_premium(user_id):
        end_date = datetime.strptime(premium_info[1], "%Y-%m-%d %H:%M:%S.%f")
        days_left = (end_date - datetime.now()).days
        text = (f"<b>❝💎 Siz Premium Foydalanuvchisiz!❞</b>\n\n"
                f"⋅ Tugash sanasi: {premium_info[1]}\n"
                f"⋅ Qolgan kunlar: {days_left} kun")
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_premium_status_keyboard())
    else:
        text = (f"""
<b>💎 Premium Tarif</b>

"Narxi: 50,000 UZS/oy
"<b>Afzalliklar:</b>

- Cheksiz kunlik so'rovlar
- Reklamalarsiz
- Bot yanada tezkor
- Kanallarga obuna shart emas

<blockquote>🙂 Premium sotib olish orqali bizning loyihalar rivojlanishi uchun hissa qo'shgan bo'lasiz</blockquote>""")
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_premium_info_keyboard())
    await callback.answer()

async def handle_payment_proceed(callback: types.CallbackQuery):
    card_number = "9860170110460087"  # Karta raqamini o‘zgartiring
    text = (f"""
<b>💳 To'lov</b>

Quyidagi karta raqamiga to'lov qiling:
<code>{card_number}</code>

<blockquote>❗️ Eslatma: To'lov belgilangan summadan kam yoki ko'p bo'lsa donat hisobida qanul qilinib qaytarib berilmaydi</blockquote>""")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_payment_keyboard(card_number))
    await callback.answer()

async def handle_payment_done(callback: types.CallbackQuery):
    text = "<b>📸 Iltimos, to'lov chek rasmini yuboring.</b>"
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

async def process_cheque(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Ismsiz"
    caption = (f"<b>💸 To'lov Cheki</b>\n"
               f"Foydalanuvchi ID: {user_id}\n"
               f"Username: @{username}\n"
               f"Sana: {message.date}")
    
    cheque_messages = {}
    for chat_id in [ADMIN_ID, ADMIN_GROUP]:
        try:
            forwarded = await message.forward(chat_id)
            sent = await message.bot.send_message(chat_id, caption, parse_mode="HTML", 
                                                reply_markup=get_cheque_keyboard(user_id))
            cheque_messages[chat_id] = {"forwarded": forwarded.message_id, "sent": sent.message_id}
        except Exception as e:
            logging.error(f"Chek yuborish xatosi {chat_id}: {e}")
    
    await state.update_data(cheque_messages=cheque_messages)
    await state.finish()

async def handle_cheque_action(callback: types.CallbackQuery, state: FSMContext):
    action, user_id = callback.data.split("_")[0], int(callback.data.split("_")[-1])
    chat_id = callback.message.chat.id
    
    data = await state.get_data()
    cheque_messages = data.get("cheque_messages", {})
    
    if action == "accept":
        add_premium_user(user_id)
        premium_info = get_premium_info(user_id)
        text = f"<b>✅ To'lov qabul qilindi.</b>\nFoydalanuvchi: {user_id}"
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.bot.send_message(
            user_id,
            f"<b>🎉 Siz Premium sotib oldingiz!</b>\n"
            f"Boshlangan: {premium_info[0]}\n"
            f"Tugaydi: {premium_info[1]}",
            parse_mode="HTML",
            disable_notification=False,
            protect_content=True
        )
        other_chat_id = ADMIN_GROUP if chat_id == ADMIN_ID else ADMIN_ID
        if other_chat_id in cheque_messages:
            try:
                await callback.bot.edit_message_text(
                    text, other_chat_id, cheque_messages[other_chat_id]["sent"], parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Tugmalarni olib tashlash xatosi {other_chat_id}: {e}")
    
    elif action == "reject":
        text = f"<b>❌ To'lov rad etildi.</b>\nFoydalanuvchi: {user_id}"
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.bot.send_message(
            user_id,
            "<b>❌ To'lov rad etildi.</b>\nIltimos, qayta urinib ko'ring.",
            parse_mode="HTML"
        )
        other_chat_id = ADMIN_GROUP if chat_id == ADMIN_ID else ADMIN_ID
        if other_chat_id in cheque_messages:
            try:
                await callback.bot.edit_message_text(
                    text, other_chat_id, cheque_messages[other_chat_id]["sent"], parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Tugmalarni olib tashlash xatosi {other_chat_id}: {e}")
    
    elif action == "ban":
        ban_user(user_id, "To'lov bilan bog'liq muammo")
        text = f"<b>🚫 Foydalanuvchi ban olindi.</b>\nFoydalanuvchi: {user_id}"
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.bot.send_message(
            user_id,
            "<b>⛔ Siz ban oldingiz.</b>\nSabab: To'lov bilan bog'liq muammo.",
            parse_mode="HTML"
        )
        other_chat_id = ADMIN_GROUP if chat_id == ADMIN_ID else ADMIN_ID
        if other_chat_id in cheque_messages:
            try:
                await callback.bot.edit_message_text(
                    text, other_chat_id, cheque_messages[other_chat_id]["sent"], parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Tugmalarni olib tashlash xatosi {other_chat_id}: {e}")
    
    await callback.answer()