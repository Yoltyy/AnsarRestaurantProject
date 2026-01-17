import os
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

router = Router()
rest_fsm = Router()

token = os.getenv('API')

bot = Bot(token=token)
dp = Dispatcher(storage=MemoryStorage())