from environs import Env

env = Env()
env.read_env()


class Config:
    RABBITMQ_URI = env("RABBITMQ_URI")
    RENDER_BOARD_QUEUE = env("RENDER_BOARD_QUEUE")
    MESSAGES_QUEUE = env("MESSAGES_QUEUE")
    LOGGER_FORMAT_DEBUG = env("LOGGER_FORMAT_DEBUG", None)
    LOGGER_FORMAT_INFO = env("LOGGER_FORMAT_INFO", None)
