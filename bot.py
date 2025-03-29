import logging
import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = ""  # Replace with your bot token
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# API URL
API_URL = "http://62.113.37.193/api"

# States
class ArticleForm(StatesGroup):
    title = State()
    content = State()
    image_url = State()

class DeleteArticle(StatesGroup):
    article_id = State()

# Start command
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Send welcome message and keyboard with options"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["📝 Add Article", "🗑 Delete Article", "📊 Statistics", "📋 List Articles"]
    keyboard.add(*buttons)
    
    await message.answer(
        "Welcome to the Articles Admin Bot!\n\n"
        "Use this bot to manage your articles website.\n"
        "Choose an option from the menu below:",
        reply_markup=keyboard
    )

# Add article command
@dp.message_handler(lambda message: message.text == "📝 Add Article", state="*")
async def add_article(message: types.Message):
    """Start the add article process"""
    await ArticleForm.title.set()
    await message.answer("Please enter the title of the article:")

@dp.message_handler(state=ArticleForm.title)
async def process_title(message: types.Message, state: FSMContext):
    """Process article title"""
    async with state.proxy() as data:
        data['title'] = message.text
    
    await ArticleForm.next()
    await message.answer("Now enter the content of the article:")

@dp.message_handler(state=ArticleForm.content)
async def process_content(message: types.Message, state: FSMContext):
    """Process article content"""
    async with state.proxy() as data:
        data['content'] = message.text
    
    await ArticleForm.next()
    await message.answer("Enter an image URL for the article (or send 'skip' to skip):")

@dp.message_handler(state=ArticleForm.image_url)
async def process_image_url(message: types.Message, state: FSMContext):
    """Process article image URL and submit article"""
    async with state.proxy() as data:
        if message.text.lower() == 'skip':
            data['image_url'] = None
        else:
            data['image_url'] = message.text
        
        # Submit article to API
        article_data = {
            "title": data['title'],
            "content": data['content'],
            "image_url": data['image_url']
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/articles", json=article_data) as response:
                if response.status == 200:
                    result = await response.json()
                    await message.answer(f"Article added successfully!\nID: {result['id']}\nTitle: {result['title']}")
                else:
                    await message.answer("Failed to add article. Please try again.")
    
    # Finish state
    await state.finish()

# Delete article command
@dp.message_handler(lambda message: message.text == "🗑 Delete Article", state="*")
async def delete_article(message: types.Message):
    """Start the delete article process"""
    # Get list of articles
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/articles") as response:
            if response.status == 200:
                articles = await response.json()
                
                if not articles:
                    await message.answer("No articles found to delete.")
                    return
                
                # Create inline keyboard with articles
                keyboard = InlineKeyboardMarkup(row_width=1)
                for article in articles:
                    button = InlineKeyboardButton(
                        f"{article['id']} - {article['title']}",
                        callback_data=f"delete_{article['id']}"
                    )
                    keyboard.add(button)
                
                await message.answer("Select an article to delete:", reply_markup=keyboard)
            else:
                await message.answer("Failed to fetch articles. Please try again.")

@dp.callback_query_handler(lambda c: c.data.startswith('delete_'))
async def process_delete_callback(callback_query: types.CallbackQuery):
    """Process delete article callback"""
    article_id = int(callback_query.data.split('_')[1])
    
    # Confirm deletion
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Yes, delete it", callback_data=f"confirm_delete_{article_id}"),
        InlineKeyboardButton("No, cancel", callback_data="cancel_delete")
    )
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"Are you sure you want to delete article #{article_id}?",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith('confirm_delete_'))
async def confirm_delete_article(callback_query: types.CallbackQuery):
    """Confirm and process article deletion"""
    article_id = int(callback_query.data.split('_')[2])
    
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/articles/{article_id}") as response:
            if response.status == 200:
                await bot.answer_callback_query(callback_query.id)
                await bot.send_message(
                    callback_query.from_user.id,
                    f"Article #{article_id} has been deleted successfully."
                )
            else:
                await bot.answer_callback_query(callback_query.id)
                await bot.send_message(
                    callback_query.from_user.id,
                    "Failed to delete article. Please try again."
                )

@dp.callback_query_handler(lambda c: c.data == "cancel_delete")
async def cancel_delete_article(callback_query: types.CallbackQuery):
    """Cancel article deletion"""
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "Article deletion cancelled."
    )

# Statistics command
@dp.message_handler(lambda message: message.text == "📊 Statistics", state="*")
async def show_statistics(message: types.Message):
    """Show website statistics"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/stats") as response:
            if response.status == 200:
                stats = await response.json()
                
                # Format statistics message
                stats_message = (
                    "📊 *Website Statistics*\n\n"
                    f"📝 Total Articles: *{stats['total_articles']}*\n"
                    f"👁 Total Views: *{stats['total_views']}*\n\n"
                    "🔝 *Most Viewed Articles:*\n"
                )
                
                for i, article in enumerate(stats['most_viewed'], 1):
                    stats_message += f"{i}. {article['title']} - *{article['views']}* views\n"
                
                await message.answer(stats_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await message.answer("Failed to fetch statistics. Please try again.")

# List articles command
@dp.message_handler(lambda message: message.text == "📋 List Articles", state="*")
async def list_articles(message: types.Message):
    """List all articles"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/articles") as response:
            if response.status == 200:
                articles = await response.json()
                
                if not articles:
                    await message.answer("No articles found.")
                    return
                
                # Format articles message
                articles_message = "📋 *All Articles:*\n\n"
                
                for article in articles:
                    created_at = article['created_at'].split('T')[0]  # Format date
                    articles_message += (
                        f"*{article['id']}. {article['title']}*\n"
                        f"📅 {created_at} | 👁 {article['views']} views\n\n"
                    )
                
                await message.answer(articles_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await message.answer("Failed to fetch articles. Please try again.")

# Run the bot
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
