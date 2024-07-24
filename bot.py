import asyncio
import logging

from aiogram import Dispatcher, Bot
from openai import AsyncClient

import assistant_handler
from config import load_config


async def main():
    logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

    config = load_config()

    client = AsyncClient(api_key=config.open_ai_key)
    assistant = await client.beta.assistants.retrieve(config.assistant_id)

    dp = Dispatcher()
    dp['open_ai_client'] = client
    dp['assistant'] = assistant
    dp.include_routers(
        assistant_handler.router
    )
    bot = Bot(token=config.tg_token)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
