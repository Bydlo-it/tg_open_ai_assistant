from dataclasses import dataclass

from environs import Env


@dataclass
class Config:
    tg_token: str
    open_ai_key: str
    assistant_id: str


def load_config():
    env = Env()
    env.read_env()

    return Config(
        tg_token=env('TG_TOKEN'),
        open_ai_key=env('OPENAI_API_KEY'),
        assistant_id=env('ASSISTANT_ID')
    )
