import asyncio

from app import App


async def main():
    app = App()
    await app.start()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
