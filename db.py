# db.py
import sqlite3
from datetime import date, datetime, timedelta

def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT, requests INTEGER DEFAULT 0, 
                  last_request_date TEXT, notifications INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users 
                 (user_id INTEGER PRIMARY KEY, reason TEXT, ban_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS channels 
                 (channel_id INTEGER PRIMARY KEY, name TEXT, link TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys 
                 (key TEXT PRIMARY KEY, requests INTEGER DEFAULT 0, added_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (setting_key TEXT PRIMARY KEY, value TEXT)''')  # INTEGER → TEXT ga o‘zgartirildi
    c.execute('''CREATE TABLE IF NOT EXISTS bot_info 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS premium_users 
                 (user_id INTEGER PRIMARY KEY, start_date TEXT, end_date TEXT)''')
    conn.commit()
    conn.close()
    add_bot_info()
    set_default_settings()

def add_user(user_id, username):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, join_date, requests, notifications) VALUES (?, ?, datetime('now'), 0, 1)",
              (user_id, username))
    conn.commit()
    conn.close()

def set_notifications(user_id, status):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET notifications = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

def get_notifications(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT notifications FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 1

def add_premium_user(user_id):
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO premium_users (user_id, start_date, end_date) VALUES (?, ?, ?)",
              (user_id, str(start_date), str(end_date)))
    conn.commit()
    conn.close()

def remove_premium_user(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM premium_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_premium(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT start_date, end_date FROM premium_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        end_date = datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() > end_date:
            remove_premium_user(user_id)
            return False
        return result
    return False

def get_premium_info(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT start_date, end_date FROM premium_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else None

def get_premium_users():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, start_date, end_date FROM premium_users")
    users = c.fetchall()
    conn.close()
    return users

def increment_request(user_id):
    today = str(date.today())
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET requests = requests + 1, last_request_date = ? WHERE user_id = ?", (today, user_id))
    conn.commit()
    conn.close()

def get_user_requests_today(user_id):
    today = str(date.today())
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT requests FROM users WHERE user_id = ? AND last_request_date = ?", (user_id, today))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_user_count():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_requests():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT SUM(requests) FROM users")
    total = c.fetchone()[0] or 0
    conn.close()
    return total

def ban_user(user_id, reason="Sabab ko'rsatilmagan"):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO banned_users (user_id, reason, ban_date) VALUES (?, ?, datetime('now'))",
              (user_id, reason))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, reason FROM banned_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else None

def get_all_users():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

def add_channel(channel_id, name, link):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO channels (channel_id, name, link) VALUES (?, ?, ?)",
              (channel_id, name, link))
    conn.commit()
    conn.close()

def remove_channel(channel_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT channel_id, name, link FROM channels")
    channels = c.fetchall()
    conn.close()
    return channels

def add_api_key(key):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO api_keys (key, requests, added_date) VALUES (?, 0, datetime('now'))", (key,))
    conn.commit()
    conn.close()

def remove_api_key(key):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM api_keys WHERE key = ?", (key,))
    conn.commit()
    conn.close()

def get_api_keys():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT key, requests, added_date FROM api_keys")
    keys = c.fetchall()
    conn.close()
    return keys

def increment_key_request(key):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE api_keys SET requests = requests + 1 WHERE key = ?", (key,))
    conn.commit()
    conn.close()

def get_least_used_key():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT key FROM api_keys ORDER BY requests ASC LIMIT 1")
    key = c.fetchone()
    conn.close()
    return key[0] if key else None

def set_daily_limit(limit):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (setting_key, value) VALUES ('daily_limit', ?)", (str(limit),))
    conn.commit()
    conn.close()

def get_daily_limit():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE setting_key = 'daily_limit'")
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result else 5

def add_bot_info():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bot_info (key, value) VALUES (?, ?)", ("nomi", "BgRemover"))
    c.execute("INSERT OR IGNORE INTO bot_info (key, value) VALUES (?, ?)", ("ishga_tushgan_sana", str(datetime.now())))
    c.execute("INSERT OR IGNORE INTO bot_info (key, value) VALUES (?, ?)", ("versiya", "1.0"))
    c.execute("INSERT OR IGNORE INTO bot_info (key, value) VALUES (?, ?)", ("ishlab_chiqaruvchi", "@pyfotuz"))
    conn.commit()
    conn.close()

def get_bot_info():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT key, value FROM bot_info")
    info = c.fetchall()
    conn.close()
    return dict(info)

def set_default_settings():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO settings (setting_key, value) VALUES ('daily_limit', '5')")
    c.execute("INSERT OR IGNORE INTO settings (setting_key, value) VALUES ('start_message', NULL)")
    c.execute("INSERT OR IGNORE INTO settings (setting_key, value) VALUES ('about_button_name', '🌐 Bot Haqida')")
    c.execute("INSERT OR IGNORE INTO settings (setting_key, value) VALUES ('about_button_url', 'https://example.com')")
    conn.commit()
    conn.close()

def set_start_message(message_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (setting_key, value) VALUES ('start_message', ?)", (str(message_id),))
    conn.commit()
    conn.close()

def get_start_message():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE setting_key = 'start_message'")
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result and result[0] else None

def set_about_button(name, url):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (setting_key, value) VALUES ('about_button_name', ?)", (name,))
    c.execute("INSERT OR REPLACE INTO settings (setting_key, value) VALUES ('about_button_url', ?)", (url,))
    conn.commit()
    conn.close()

def get_about_button():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE setting_key = 'about_button_name'")
    name = c.fetchone()
    c.execute("SELECT value FROM settings WHERE setting_key = 'about_button_url'")
    url = c.fetchone()
    conn.close()
    return (name[0] if name else "🌐 Bot Haqida", url[0] if url else "https://example.com")