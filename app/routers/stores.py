'''
    Copyright: Alex Ken [2023]
'''
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Annotated
import asyncpg, uuid

from .utils import http_responses, http_exception

# data models
class NewStore(BaseModel):
    name: str
    description: str
    address: str

class Store(NewStore):
    id: uuid.UUID

class StoreUpdate(BaseModel):
    name: str | None
    description: str | None
    address: str | None

# router
router = APIRouter(prefix='/stores')

@router.get('/',
            response_model=list[Store],
            responses=http_responses([204]),
            description='Returns list of Stores.')
async def get_stores(request: Request,
                     skip: Annotated[int, Query(description='Rows to skip')] = 0,
                     limit: Annotated[int, Query(description='Maximum number of rows to return')] = 100):
    async with request.app.state.db.acquire() as con:
        records = await con.fetch('''
            SELECT * FROM stores
            ORDER BY name
            LIMIT $1
            OFFSET $2
            ''', limit, skip)
        if not records:
            raise http_exception(204)
        return [Store(**r) for r in records]

@router.get('/id/{id}',
            response_model=Store,
            responses=http_responses([204]),
            description='Returns Store by ID.')
async def get_store_by_id(request: Request, id: uuid.UUID):
    async with request.app.state.db.acquire() as con:
        record = await con.fetchrow('SELECT * FROM stores WHERE id = $1', id)
        if not record:
            raise http_exception(204)
        return Store(**record)

@router.get('/name/{name}',
            response_model=Store,
            responses=http_responses([204]),
            description='Returns Store by name.')
async def get_store_by_name(request: Request, name: str):
    async with request.app.state.db.acquire() as con:
        record = await con.fetchrow('SELECT * FROM stores WHERE name = $1', name)
        if not record:
            raise http_exception(204)
        return Store(**record)

@router.post('/create',
            response_model=Store,
            responses=http_responses([409]),
            description='Creates new Store.')
async def create_store(request: Request, store: NewStore):
    async with request.app.state.db.acquire() as con:
        try:
            record = await con.fetchrow('''
                INSERT INTO stores(id, name, description, address)
                VALUES($1, $2, $3, $4) RETURNING *
                ''', uuid.uuid4(), store.name, store.description, store.address)
            return Store(**record)
        except asyncpg.exceptions.UniqueViolationError:
            raise http_exception(409)

@router.put('/update/id/{id}',
            response_model=Store,
            responses=http_responses([204, 409]),
            description='Updates Store with provided data.')
async def update_store(request: Request, id: uuid.UUID, store: StoreUpdate):
    async with request.app.state.db.acquire() as con:
        try:
            record = await con.fetchrow('''
                UPDATE stores SET 
                name = COALESCE($2, name), 
                description = COALESCE($3, description)
                address = COALESCE($4, address)
                WHERE id = $1 RETURNING *
                ''', id, store.name, store.description, store.address)
            if not record:
                raise http_exception(204)
            return Store(**record)
        except asyncpg.exceptions.UniqueViolationError:
            raise http_exception(409)
        
@router.delete('/delete/id/{id}',
            response_model=Store,
            responses=http_responses([204, 400]),
            description='Deletes Store.')
async def delete_store_by_id(request: Request, id: uuid.UUID):
    async with request.app.state.db.acquire() as con:
        try:
            record = await con.fetchrow('''
                DELETE FROM stores WHERE id = $1 RETURNING *
                ''', id)
            if not record:
                raise http_exception(204)
            return Store(**record)
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise http_exception(400)
