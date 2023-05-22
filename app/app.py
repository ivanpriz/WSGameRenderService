import asyncio
import json

import aio_pika

from app.rabbit import Rabbit, RPCServer
from app.config import Config
from app.renderer import Renderer
from app.utils.logging import get_logger
from app.schemas import Command, Message


class App:
    logger = get_logger("App")

    def __init__(self):
        self.rabbit = Rabbit(Config.RABBITMQ_URI)
        self.renderer = Renderer()
        self.messages_exchange = None
        self.rendered_boards_exchange = None

    async def _on_decoded_msg(self, msg: str):
        result, msgs = self.renderer.process_command(Command.from_json(msg))
        self.logger.debug("Command result: %s", result.to_json())
        self.logger.debug("Logs: %s", msgs)
        await asyncio.gather(
            *[
                asyncio.create_task(
                    self.rabbit.publish_to_exchange(
                        self.messages_exchange,
                        "",
                        msg.to_json(),
                    ),
                ) for msg in msgs
            ]
        )
        self.logger.debug("Logs sent to %s", self.messages_exchange.name)
        await self.rabbit.publish_to_exchange(
            self.rendered_boards_exchange,
            "",
            result.to_json()
        )
        self.logger.debug("Render result sent to %s", self.rendered_boards_exchange.name)

    async def _callback(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process(requeue=False):
            payload = message.body.decode()
            await self._on_decoded_msg(payload)

    async def _on_start(self):
        await self.rabbit.connect()
        await self.rabbit.create_channel()
        self.messages_exchange = await self.rabbit.declare_exchange(
            Config.MESSAGES_EXCHANGE,
            _type=aio_pika.ExchangeType.FANOUT,
        )
        self.logger.debug("Messages exchange declared with name %s", Config.MESSAGES_EXCHANGE)
        self.boards_to_render_queue = await self.rabbit.declare_queue(
            Config.BOARDS_TO_RENDER_QUEUE,
            durable=True
        )
        self.logger.debug("Boards to render queue declared %s", Config.BOARDS_TO_RENDER_QUEUE)
        self.rendered_boards_exchange = await self.rabbit.declare_exchange(
            Config.RENDERED_BOARDS_EXCHANGE,
            _type=aio_pika.ExchangeType.FANOUT,
        )
        self.logger.debug("Rendered boards exchange declared %s", Config.RENDERED_BOARDS_EXCHANGE)

    async def _run(self):
        asyncio.create_task(self.boards_to_render_queue.consume(self._callback))

    async def start(self):
        await self._on_start()
        self.logger.debug("App started!")
        await self._run()
