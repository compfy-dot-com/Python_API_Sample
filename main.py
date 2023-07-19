'''
    Copyright: Alex Ken [2023]
'''
from fastapi import FastAPI
import asyncpg

from .routers import items, stores, stock

# App description
description = '''
### CRUD and application API for a database emulating item stock in multiple stores.
'''

# FastAPI application
app = FastAPI(
    title="Test App for FastAPI with asyncpg",
    description=description,
    version="0.0.1",
    contact={
        "name": "Alex Ken",
        "email": "a.ken@compfy.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# add routers
app.include_router(items.router)
app.include_router(stores.router)
app.include_router(stock.router)

@app.on_event('startup')
async def on_startup():
    app.state.db = await asyncpg.create_pool(user='postgres', host='127.0.0.1', database='test')

@app.on_event('shutdown')
async def on_shutdown():
    await app.state.db.close()

