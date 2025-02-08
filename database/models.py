# pylint: disable=too-few-public-methods
"""
This module contains the SQLAlchemy models for the database.
"""

from typing import List

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    MetaData,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, Mapped, relationship

meta = MetaData()
Base = declarative_base(metadata=meta)


class Listing(Base):
    """
    A search results table. It stores found cars.
    """

    __tablename__ = "listing"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    avto_id: Mapped[str] = Column(String(50), unique=True)
    url: Mapped[str] = Column(String(150), unique=True)
    accessed_time = Column(DateTime)
    prices: Mapped[List["Price"]] = relationship(lazy="selectin")


class Price(Base):
    """
    A table that stores the current and previous prices.
    """

    __tablename__ = "price"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    price: Mapped[int] = Column(Integer, unique=False)
    accessed_time = Column(DateTime)
    listing_id: Mapped[int] = Column(ForeignKey("listing.id"))
