'''
    Copyright: Alex Ken [2023]
'''
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Annotated
import asyncpg, uuid

from .utils import http_responses, http_exception

# data models
class NewItem(BaseModel):
    name: str
    description: str

class Item(NewItem):
    id: uuid.UUID

class ItemUpdate(BaseModel):
    name: str | None
    description: str | None

# router
router = APIRouter(prefix='/items')

@router.get('/',
            response_model=list[Item],
            responses=http_responses([204]),
            description='Returns list of Items.')
async def get_items(request: Request,
                    skip: Annotated[int, Query(description='Rows to skip')] = 0,
                    limit: Annotated[int, Query(description='Maximum number of rows to return')] = 100):
    async with request.app.state.db.acquire() as con:
        records = await con.fetch('''
            SELECT * FROM items
            ORDER BY name
            LIMIT $1
            OFFSET $2
            ''', limit, skip)
        if not records:
            raise http_exception(204)
        return [Item(**r) for r in records]

@router.get('/id/{id}',
            response_model=Item,
            responses=http_responses([204]),
            description='Returns Item by ID.')
async def get_item_by_id(request: Request, id: uuid.UUID):
    async with request.app.state.db.acquire() as con:
        record = await con.fetchrow('SELECT * FROM items WHERE id = $1', id)
        if not record:
            raise http_exception(204)
        return Item(**record)

@router.get('/name/{name}',
            response_model=Item,
            responses=http_responses([204]),
            description='Returns Item by name.')
async def get_item_by_name(request: Request, name: str):
    async with request.app.state.db.acquire() as con:
        record = await con.fetchrow('SELECT * FROM items WHERE name = $1', name)
        if not record:
            raise http_exception(204)
        return Item(**record)

@router.post('/create',
            response_model=Item,
            responses=http_responses([409]),
            description='Creates new Item.')
async def create_item(request: Request, item: NewItem):
    async with request.app.state.db.acquire() as con:
        try:
            record = await con.fetchrow('''
                INSERT INTO items(id, name, description)
                VALUES($1, $2, $3) RETURNING *
                ''', uuid.uuid4(), item.name, item.description)
            return Item(**record)
        except asyncpg.exceptions.UniqueViolationError:
            raise http_exception(409)

@router.put('/update/id/{id}',
            response_model=Item,
            responses=http_responses([204, 409]),
            description='Updates Item with provided data.')
async def update_item(request: Request, id: uuid.UUID, item: ItemUpdate):
    async with request.app.state.db.acquire() as con:
        try:
            record = await con.fetchrow('''
                UPDATE items SET 
                name = COALESCE($2, name), 
                description = COALESCE($3, description)
                WHERE id = $1 RETURNING *
                ''', id, item.name, item.description)
            if not record:
                raise http_exception(204)
            return Item(**record)
        except asyncpg.exceptions.UniqueViolationError:
            raise http_exception(409)

@router.delete('/delete/id/{id}',
            response_model=Item,
            responses=http_responses([204, 400]),
            description='Deletes Item.')
async def delete_item_by_id(request: Request, id: uuid.UUID):
    async with request.app.state.db.acquire() as con:
        try:
            record = await con.fetchrow('''
                DELETE FROM items WHERE id = $1 RETURNING *
                ''', id)
            if not record:
                raise http_exception(204)
            return Item(**record)
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise http_exception(400)
