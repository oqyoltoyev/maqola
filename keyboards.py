# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard(about_button_name="＃ Bot Haqida", about_button_url="https://example.com"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💎 Premium", callback_data="buy_premium"),
        InlineKeyboardButton("🔔 Bildirishnomalar", callback_data="notifications")
    )
    keyboard.add(
        InlineKeyboardButton(about_button_name, url=about_button_url)
    )
    return keyboard

def get_notifications_keyboard(is_premium=False, notifications_status=1):
    keyboard = InlineKeyboardMarkup(row_width=2)
    status_text = "Yoniq" if notifications_status else "O‘chiq"
    keyboard.add(
        InlineKeyboardButton(f"✅ Yoqish ({status_text})", callback_data="notifications_on"),
        InlineKeyboardButton(f"❌ O‘chirish ({status_text})", callback_data="notifications_off")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="home")
    )
    return keyboard

def get_premium_status_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="home")
    )
    return keyboard

def get_main_admin_menu():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")
    )
    keyboard.add(
        InlineKeyboardButton("📺 Kanallar", callback_data="admin_channels"),
        InlineKeyboardButton("🔑 API Kalitlari", callback_data="admin_keys")
    )
    keyboard.add(
        InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin_settings"),
        InlineKeyboardButton("📢 E'lon", callback_data="admin_broadcast")
    )
    return keyboard

def get_user_management_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🚫 Ban", callback_data="admin_ban"),
        InlineKeyboardButton("✅ Bandan Chiqarish", callback_data="admin_unban")
    )
    keyboard.add(
        InlineKeyboardButton("💎 Premium Foydalanuvchilar", callback_data="admin_premium_users"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")
    )
    return keyboard

def get_premium_users_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🚫 Ban", callback_data="admin_ban_premium"),
        InlineKeyboardButton("❌ Premiumni Olib Tashlash", callback_data="admin_remove_premium")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_users")
    )
    return keyboard

def get_channel_management_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Qo'shish", callback_data="admin_add_channel"),
        InlineKeyboardButton("➖ O'chirish", callback_data="admin_remove_channel")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")
    )
    return keyboard

def get_key_management_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Qo'shish", callback_data="admin_add_key"),
        InlineKeyboardButton("➖ O'chirish", callback_data="admin_remove_key")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")
    )
    return keyboard

def get_settings_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("〥 Kunlik Limit", callback_data="admin_set_limit"),
        InlineKeyboardButton("〥 Start Habari", callback_data="admin_set_start_message")
    )
    keyboard.add(
        InlineKeyboardButton("〥 Bot Haqida Tugmasi", callback_data="admin_set_about_button"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")
    )
    return keyboard

def get_back_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back"))

def get_home_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("🏠 Bosh Sahifa", callback_data="home"))

def get_user_profile_button(user_id):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("👤 Profil", url=f"tg://user?id={user_id}")
    )

def get_subscription_keyboard(channels):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for _, name, link in channels:
        keyboard.add(InlineKeyboardButton(f"{name} ga Obuna Bo'lish", url=link))
    keyboard.add(InlineKeyboardButton("✅ Obunani Tekshirish", callback_data="check_subscription"))
    return keyboard

def get_premium_info_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("💳 Sotib Olish", callback_data="proceed_payment"))
    return keyboard

def get_payment_keyboard(card_number):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("✅ To'lov Qildim", callback_data="payment_done"))
    return keyboard

def get_cheque_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("✅ Qabul Qilish", callback_data=f"accept_premium_{user_id}"),
        InlineKeyboardButton("❌ Rad Etish", callback_data=f"reject_premium_{user_id}"),
        InlineKeyboardButton("🚫 Ban", callback_data=f"ban_premium_{user_id}")
    )
    return keyboard