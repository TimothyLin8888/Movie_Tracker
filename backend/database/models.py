from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    Boolean,
    ForeignKey
)

from sqlalchemy.orm import relationship

from database.database import Base

from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )

    watch_history = relationship(
        "WatchHistory",
        back_populates="user"
    )


class Movie(Base):
    __tablename__ = "movies"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    imdb_id = Column(
        String,
        index=True
    )

    tmdb_id = Column(
        Integer,
        index=True
    )

    media_type = Column(String)

    title = Column(String)

    release_date = Column(Date)

    imdb_rating = Column(Float)

    runtime = Column(Integer)

    genres = Column(String)

    director = Column(String)

    original_language = Column(String)

    poster_path = Column(String)

    overview = Column(String)

    favorite_movie = Column(
        Boolean,
        default=False
    )

    watches = relationship(
        "WatchHistory",
        back_populates="movie"
    )


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    movie_id = Column(
        Integer,
        ForeignKey("movies.id"),
        nullable=False,
        index=True
    )

    watch_date = Column(
        Date,
        nullable=False
    )

    personal_rating = Column(
        Integer
    )

    user = relationship(
        "User",
        back_populates="watch_history"
    )

    movie = relationship(
        "Movie",
        back_populates="watches"
    )