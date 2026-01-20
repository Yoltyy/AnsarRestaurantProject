import asyncio
import logging
from bot import bot, dp, router, rest_fsm
from utils.middleware import PaymentCheckMiddleware

logging.basicConfig(level=logging.INFO)

async def main():
    import handlers
    from database import init_db

    init_db()

    dp.update.outer_middleware(PaymentCheckMiddleware())

    dp.include_router(router)
    dp.include_router(rest_fsm)

    await bot.delete_webhook(drop_pending_updates=True)
    print('Бот запущен')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())