import asyncio
import json

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

    async def on_decoded_msg(self, msg: str):
        result, msgs = self.renderer.process_command(Command.from_json(msg))
        print(f"Command result: {result.to_json()}")
        print(msgs)
        await asyncio.gather(
            *[
                asyncio.create_task(
                    self.rabbit.publish_to_queue(Config.MESSAGES_QUEUE, msg.to_json())
                ) for msg in msgs
            ]
        )
        return result.to_json()

    async def _on_start(self):
        await self.rabbit.connect()
        await self.rabbit.create_channel()
        await self.rabbit.declare_queue(Config.MESSAGES_QUEUE)

        self.render_board_server = RPCServer(
            rabbit=self.rabbit,
            queue_to_consume_name=Config.RENDER_BOARD_QUEUE,
            on_decoded_msg=self.on_decoded_msg
        )

    async def _run(self):
        asyncio.create_task(self.render_board_server.run())

    async def start(self):
        await self._on_start()
        self.logger.debug("App started!")
        await self._run()
