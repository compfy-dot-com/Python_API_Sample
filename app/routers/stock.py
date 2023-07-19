from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Annotated
import asyncpg, uuid

from .utils import http_responses, http_exception

# data models
class Stock(BaseModel):
    item_id: uuid.UUID
    store_id: uuid.UUID
    available: int
    sold: int
    price: float

class StockChange(BaseModel):
    item_id: uuid.UUID
    store_id: uuid.UUID
    available: int | None
    sold: int | None
    price: float | None

class StockReport(Stock):
    item: str
    store: str

# rounter
router = APIRouter(prefix='/stock')

@router.get('/',
            response_model=list[StockReport],
            responses=http_responses([204]),
            description='Returns stock records.')
async def get_stock(request: Request,
                    skip: Annotated[int, Query(description='Rows to skip')] = 0,
                    limit: Annotated[int, Query(description='Maximum number of rows to return')] = 100):
    async with request.app.state.db.acquire() as con:
        records = await con.fetch('''
            SELECT items.name AS item, stores.name AS store, stock.*
            FROM stock
            JOIN items ON items.id=stock.item_id
            JOIN stores ON stores.id=stock.store_id
            ORDER BY item
            LIMIT $1
            OFFSET $2
            ''', limit, skip)
        if not records:
            raise http_exception(204)
        return [StockReport(**r) for r in records]

@router.get('/items/id/{id}',
            response_model=list[StockReport],
            responses=http_responses([204]),
            description='Returns item stock records by item ID.')
async def get_stock_by_item_id(request: Request, 
                               id: uuid.UUID,
                               skip: Annotated[int, Query(description='Rows to skip')] = 0,
                               limit: Annotated[int, Query(description='Maximum number of rows to return')] = 100):
    async with request.app.state.db.acquire() as con:
        records = await con.fetch('''
            SELECT items.name AS item, stores.name AS store, stock.*
            FROM stock
            JOIN items ON items.id=stock.item_id
            JOIN stores ON stores.id=stock.store_id
            WHERE stock.item_id = $1
            ORDER BY stores.name
            LIMIT $2
            OFFSET $3
            ''', id, limit, skip)
        if not records:
            raise http_exception(204)
        return [StockReport(**r) for r in records]

@router.get('/items/name/{name}',
            response_model=list[StockReport],
            responses=http_responses([204]),
            description='Returns item stock records by item name.')
async def get_stock_by_item_name(request: Request,
                                 name: str,
                                 skip: Annotated[int, Query(description='Rows to skip')] = 0,
                                 limit: Annotated[int, Query(description='Maximum number of rows to return')] = 100):
    async with request.app.state.db.acquire() as con:
        records = await con.fetch('''
            SELECT items.name AS item, stores.name AS store, stock.*
            FROM stock
            JOIN items ON items.id=stock.item_id
            JOIN stores ON stores.id=stock.store_id
            WHERE stock.name = $1
            ORDER BY stores.name
            LIMIT $2
            OFFSET $3
            ''', name, limit, skip)
        if not records:
            raise http_exception(204)
        return [StockReport(**r) for r in records]

@router.post('/add',
            response_model=Stock,
            responses=http_responses([400, 409]),
            description='''
                Creates a stock record or add/subtracts quantities in an existing record.
                Can also set new "price" if provided.
                The "available" and "sold", if provided, can be positive or negative increments.
                ''')
async def change_stock(request: Request, stock: StockChange):
    async with request.app.state.db.acquire() as con:
        async with con.transaction():
            try:
                record = await con.fetchrow('''
                    INSERT INTO stock AS s (item_id, store_id, available, sold, price) 
                    VALUES($1, $2, GREATEST(COALESCE($3, 0), 0), GREATEST(COALESCE($4, 0), 0), GREATEST(COALESCE($5, 0), 0))
                    ON CONFLICT (item_id, store_id) DO UPDATE SET
                    available = GREATEST(s.available + COALESCE($3, 0), 0),
                    sold = GREATEST(s.sold + COALESCE($4, 0), 0),
                    price = GREATEST(COALESCE($5, s.price), 0)
                    RETURNING *
                    ''', stock.item_id, stock.store_id, stock.available, stock.sold, stock.price)
                return Stock(**record)
            except (asyncpg.exceptions.CheckViolationError,
                    asyncpg.exceptions.NotNullViolationError,
                    asyncpg.exceptions.ForeignKeyViolationError) as e:
                raise http_exception(400, repr(e))
