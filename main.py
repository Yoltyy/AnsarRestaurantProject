import asyncio
import logging
import handlers
from bot import router, rest_fsm, bot, dp

logging.basicConfig(level=logging.INFO)

async def main():
    dp.include_router(router)
    dp.include_router(rest_fsm)

    await bot.delete_webhook(drop_pending_updates=True)
    print('Бот запущен')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())