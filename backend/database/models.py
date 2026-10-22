from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    Boolean,
    ForeignKey,
    UniqueConstraint,
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

    bio = Column(String(280), nullable=True)

    is_public = Column(Boolean, nullable=False, default=False)

    show_lists = Column(Boolean, nullable=False, default=True)

    scheduled_watches = relationship(
        "ScheduledWatch",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    watch_history = relationship(
        "WatchHistory",
        back_populates="user"
    )

    movie_lists = relationship(
        "MovieList",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    streaming_services = relationship(
        "UserStreamingService",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class StreamingService(Base):
    __tablename__ = "streaming_services"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(80), nullable=False)
    logo_key = Column(String(80), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    watchmode_name = Column(String(80), nullable=True)

    users = relationship(
        "UserStreamingService",
        back_populates="service",
        cascade="all, delete-orphan"
    )

    availability = relationship(
        "MovieStreamingAvailability",
        back_populates="service",
        cascade="all, delete-orphan"
    )


class UserStreamingService(Base):
    __tablename__ = "user_streaming_services"
    __table_args__ = (
        UniqueConstraint("user_id", "service_id", name="uq_user_streaming_service"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("streaming_services.id"), nullable=False, index=True)

    user = relationship("User", back_populates="streaming_services")
    service = relationship("StreamingService", back_populates="users")


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

    watchmode_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    watchmode_checked_at = Column(
        DateTime,
        nullable=True,
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

    availability = relationship(
        "MovieStreamingAvailability",
        back_populates="movie",
        cascade="all, delete-orphan"
    )


class MovieStreamingAvailability(Base):
    __tablename__ = "movie_streaming_availability"
    __table_args__ = (
        UniqueConstraint("movie_id", "service_id", name="uq_movie_streaming_service"),
    )

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("streaming_services.id"), nullable=False, index=True)

    leaving_date = Column(Date, nullable=True)
    checked_at = Column(DateTime, default=datetime.now, nullable=False)

    movie = relationship("Movie", back_populates="availability")
    service = relationship("StreamingService", back_populates="availability")


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

    is_favorite = Column(
        Boolean,
        nullable=False,
        default=False
    )

    user = relationship(
        "User",
        back_populates="watch_history"
    )

    movie = relationship(
        "Movie",
        back_populates="watches"
    )

    list_memberships = relationship(
        "ListMembership",
        back_populates="watch",
        cascade="all, delete-orphan"
    )


class ScheduledWatch(Base):
    __tablename__ = "scheduled_watches"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", "scheduled_date", name="uq_scheduled_watch"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)
    scheduled_date = Column(Date, nullable=False, index=True)
    note = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="scheduled_watches")
    movie = relationship("Movie")


class MovieList(Base):
    __tablename__ = "movie_lists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(80), nullable=False)

    user = relationship("User", back_populates="movie_lists")
    memberships = relationship("ListMembership", back_populates="movie_list", cascade="all, delete-orphan")


class ListMembership(Base):
    __tablename__ = "list_memberships"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("movie_lists.id"), nullable=False, index=True)
    watch_id = Column(Integer, ForeignKey("watch_history.id"), nullable=False, index=True)
    position = Column(Integer, nullable=True)

    movie_list = relationship("MovieList", back_populates="memberships")
    watch = relationship("WatchHistory", back_populates="list_memberships")