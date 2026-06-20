from faststream import FastStream

from app.consumers.payment_consumer import router
from app.core.rabbitmq import broker

app = FastStream(broker)
broker.include_router(router)

# async def main():
#     app = FastStream(broker)
#     # await broker.connect()
#     # await declare_topology()
#     broker.include_router(router)
#     await app.run()
#
# if __name__ == "__main__":
#     asyncio.run(main())
