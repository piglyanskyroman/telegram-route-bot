import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Данные о маршрутах по районам
ROUTE_DATA = {
    "Западный": ["1201", "1202", "1203", "1204", "1205", "1206", "1207", "1208", "1209", "1210",
                 "1301", "1302", "1303", "1304", "1305", "1306", "1307", "1308", "1309", "1310",
                 "1401", "1402", "1403", "1404", "1405", "1406", "1407", "1408", "1409", "1410", "1411",
                 "1501", "1502", "1503", "1504", "1505", "1506", "1507", "1508"],

    "Ленина": ["2101", "2102", "2103", "2104", "2105", "2106", "2107", "2108", "2109", "2110"],

    "Каменка+Военвед": ["2111", "4301", "4302", "4303", "4304", "4305", "4306", "4307", "4308"],

    "Александровка": ["3101", "3102", "3103", "3104", "3105", "3106", "3107", "3108"],

    "Темерник+Чкаловский": ["3201", "3202", "3203", "3204", "3205", "3206", "3207", "3208",
                            "3209", "3210", "3211", "3212", "3213"],

    "Северный район": ["4101", "4102", "4103", "4104", "4105", "4106", "4107", "4108", "4109", "4110",
                       "4201", "4202", "4203", "4204", "4205", "4206", "4207", "4208", "4209", "4210",
                       "4211", "4212", "4213", "4214", "4215"],

    "Суворовский": ["4401", "4402", "4403", "4404", "4405", "4406"],

    "Левенцовка": ["1101", "1102", "1103", "1104", "1105", "1106", "1107", "1108", "1109", "1120"],

    "Центр": ["2201", "2202", "2203", "2204", "2205", "2206", "2207", "2208", "2209", "2210",
              "2211", "2212", "2213", "2214", "2215"],

    "Сельмаш": ["2301", "2302"],

    "Красный Аксай": ["2303", "2304"]
}

# Данные о количестве ящиков и подъездов
ROUTE_STATS = {
    "1201": {"boxes": 2286, "entrances": 28},
    "1202": {"boxes": 1971, "entrances": 46},
    "1203": {"boxes": 2080, "entrances": 44},
    # ... (вставьте ВСЮ вашу статистику из предыдущего кода)
    # Для экономии места оставлю только несколько примеров
    "1120": {"boxes": 2184, "entrances": 39}
}

# Безопасный список разрешенных расширений файлов
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF'}

class RouteBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_district, pattern="^district_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_route, pattern="^route_"))
        self.application.add_handler(CallbackQueryHandler(self.handle_back, pattern="^back_to_"))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = []
        for district in ROUTE_DATA.keys():
            keyboard.append([InlineKeyboardButton(district, callback_data=f"district_{district}")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(
                "🚍 Бот карт маршрутов\n\nВыберите район:",
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                "🚍 Бот карт маршрутов\n\nВыберите район:",
                reply_markup=reply_markup
            )

    async def handle_district(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        district = query.data.replace("district_", "")
        context.user_data['current_district'] = district

        routes = ROUTE_DATA[district]
        keyboard = []

        for i in range(0, len(routes), 4):
            row = []
            for route in routes[i:i + 4]:
                row.append(InlineKeyboardButton(route, callback_data=f"route_{route}"))
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("⬅️ Назад к районам", callback_data="back_to_districts")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📍 Район: {district}\nВыберите номер маршрута:",
            reply_markup=reply_markup
        )

    async def handle_route(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        route_number = query.data.replace("route_", "")
        context.user_data['current_route'] = route_number

        try:
            # Получаем статистику
            route_stats = ROUTE_STATS.get(route_number, {})
            boxes = route_stats.get("boxes", "данные обновляются")
            entrances = route_stats.get("entrances", "данные обновляются")

            stats_message = (
                f"🗺️ Маршрут №{route_number}\n"
                f"📦 Ящиков: {boxes}\n"
                f"🚪 Подъездов: {entrances}\n"
                f"📍 Район: {context.user_data.get('current_district', '')}"
            )

            # Пытаемся найти фото
            photo_found = False
            for ext in ALLOWED_EXTENSIONS:
                photo_path = f"photos/{route_number}{ext}"
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as photo:
                        await context.bot.send_photo(
                            chat_id=query.message.chat_id,
                            photo=photo,
                            caption=stats_message,
                            protect_content=True
                        )
                    photo_found = True
                    break

            if not photo_found:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"❌ Фото для маршрута {route_number} не найдено\n\n{stats_message}"
                )

            # Кнопки навигации
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к маршрутам", 
                                    callback_data=f"district_{context.user_data.get('current_district', '')}")],
                [InlineKeyboardButton("🏠 Начальное меню", callback_data="back_to_districts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Выберите действие:",
                reply_markup=reply_markup
            )

        except Exception as e:
            logging.error(f"Error: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Ошибка при загрузке фото"
            )

    async def handle_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_districts":
            await self.start(update, context)

    def run(self):
        """Запуск бота"""
        print("🚀 Бот запущен в облаке Railway!")
        self.application.run_polling()

# Создаем папку для фото если её нет
os.makedirs("photos", exist_ok=True)

# Запуск бота
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не установлен!")
        exit(1)
    
    bot = RouteBot(BOT_TOKEN)
    bot.run()