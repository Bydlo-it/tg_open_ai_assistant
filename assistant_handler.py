import logging
import re

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionMiddleware
from openai import AsyncClient
from openai.pagination import AsyncCursorPage
from openai.types.beta import Assistant
from openai.types.beta.threads import Message as OpenAiMessage, TextContentBlock

router = Router()
router.message.middleware(ChatActionMiddleware())

logger = logging.getLogger(__name__)

user_threads = {}


class AssistantState(StatesGroup):
    idle = State()
    running = State()


@router.message(Command('start'))
async def on_start_command(message: Message, state: FSMContext, assistant: Assistant):
    await state.set_state(AssistantState.idle)
    await message.answer(f"{assistant.name} готов к работе. Задайте вопрос!")


@router.message(AssistantState.running)
async def on_text_message(message: Message):
    await message.answer("Подождите, предыдущий запрос еще в работе!")


@router.message(F.text)
async def on_text_message(message: Message,
                          state: FSMContext,
                          open_ai_client: AsyncClient,
                          assistant: Assistant):
    try:
        await state.set_state(AssistantState.running)

        user_id = message.from_user.id
        if user_id in user_threads:
            thread_id = user_threads[user_id]
        else:
            thread = await open_ai_client.beta.threads.create()
            user_threads[user_id] = thread.id
            thread_id = thread.id

        question = await open_ai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message.text
        )

        run = await open_ai_client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant.id
        )

        if run.status == 'completed':
            answers: AsyncCursorPage[Message] = await open_ai_client.beta.threads.messages.list(
                thread_id=thread_id,
                run_id=run.id
            )

            for answer in answers.data:  # type: OpenAiMessage
                for cont in answer.content:
                    if isinstance(cont, TextContentBlock):
                        text = cont.text
                        await message.answer(text=re.sub(r'(\*{2,}|_{2,}|`{2,}|~{2,}|【.*?†source】)', '', text.value))
                        # await message.answer(text=re.sub(r'(\*{2,}|_{2,}|`{2,}|~{2,})', '', text.value))

    except Exception:
        logger.exception("Ошибка запроса")
        await message.answer("Хм, что-то пошло не так. Давайте попробуем еще раз!")
    finally:
        await state.set_state(AssistantState.idle)
