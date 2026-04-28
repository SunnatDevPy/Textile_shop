from datetime import datetime

from sqlalchemy import BigInteger, delete as sqlalchemy_delete, DateTime, update as sqlalchemy_update, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, selectinload

from config import conf


class Base(AsyncAttrs, DeclarativeBase):

    @declared_attr
    def __tablename__(self) -> str:
        __name = self.__name__[:1]
        for i in self.__name__[1:]:
            if i.isupper():
                __name += '_'
            __name += i
        __name = __name.lower()

        if __name.endswith('y'):
            __name = __name[:-1] + 'ie'
        return __name + 's'


class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    async def execute(self, *args, **kwargs):
        """
        Har qanday SQL execute xatoliklarida sessionni "failed transaction"
        holatida qoldirmaslik uchun rollback qilamiz.
        """
        try:
            return await self._session.execute(*args, **kwargs)
        except Exception:
            await self._session.rollback()
            raise

    def init(self):
        self._engine = create_async_engine(conf.db.db_url)
        self._session = sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)()

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # async def drop_all(self):
    #     async with self._engine.begin() as conn:
    #         await conn.run_sync(Base.metadata.drop_all)


db = AsyncDatabaseSession()
db.init()


# ----------------------------- ABSTRACTS ----------------------------------
class AbstractClass:
    @staticmethod
    async def commit():
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def create(cls, **kwargs):
        obj = cls(**kwargs)
        db.add(obj)
        await cls.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def update(cls, id_, **kwargs):
        query = (
            sqlalchemy_update(cls)
            .where(cls.id == id_)
            .values(**kwargs)
            .returning(cls)
        )
        result = await db.execute(query)
        await cls.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def get_or_none(cls, _id: int, *, relationship=None):
        query = select(cls).where(cls.id == _id)

        if relationship is not None:
            # relationship может быть одним relationship или списком
            if isinstance(relationship, (list, tuple)):
                query = query.options(*(selectinload(r) for r in relationship))
            else:
                query = query.options(selectinload(relationship))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get(cls, _id, *, relationship=None):
        query = select(cls).where(cls.id == _id)
        if relationship:
            query = query.options(selectinload(relationship))
        return (await db.execute(query)).scalar()

    @classmethod
    async def count(cls):
        query = select(func.count()).select_from(cls)
        return (await db.execute(query)).scalar()

    @classmethod
    async def delete(cls, id_):
        query = sqlalchemy_delete(cls).where(cls.id == id_)
        await db.execute(query)
        await cls.commit()

    @classmethod
    async def filters(cls, criteria, *, relationship=None, columns=None):
        if columns:
            query = select(*columns)
        else:
            query = select(cls)

        query = query.where(criteria)

        if relationship:
            query = query.options(selectinload(relationship))
        return (await db.execute(query)).scalars()

    @classmethod
    async def filter(cls, criteria, *, relationship=None, columns=None):
        if columns:
            query = select(*columns)
        else:
            query = select(cls)

        query = query.where(criteria)

        if relationship:
            query = query.options(selectinload(relationship))
        return (await db.execute(query)).scalar()

    @classmethod
    async def all(cls):
        return (await db.execute(select(cls))).scalars().all()

    @classmethod
    async def get_order_items(cls, order_id):
        return (await db.execute(select(cls).where(cls.order_id == order_id))).scalars().all()

    @classmethod
    async def search(cls, name, category_id=None):
        if category_id:
            return (await db.execute(
                select(cls).where(cls.category_id == category_id, cls.name_uz.ilike(f"%{name}%")))).scalars().all()
        else:
            return (await db.execute(select(cls).where(cls.name_uz.ilike(f"%{name}%")))).scalars().all()


# def run_async(self, func, *args, **kwargs):
#     return asyncio.run(func(*args, **kwargs))

# def convert_uzs(self, amount: int):
#     return amount * current_price
#
# def convert_usd(self, amount: int):
#     return amount // current_price


class BaseModel(Base, AbstractClass):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    def __str__(self):
        return f"{self.id}"


class CreatedBaseModel(BaseModel):
    __abstract__ = True
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
