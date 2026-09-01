import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()
security = HTTPBearer()
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class RegisterRequest(BaseModel):
	username: str
	email: str
	password: str


class LoginRequest(BaseModel):
	email: str
	password: str


def create_access_token(user_id: int) -> str:
	expires_at = datetime.now(timezone.utc) + timedelta(
		minutes=ACCESS_TOKEN_EXPIRE_MINUTES
	)
	payload = {"sub": str(user_id), "exp": expires_at}
	return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: Session = Depends(get_db),
) -> User:
	unauthorized = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Invalid or expired token",
		headers={"WWW-Authenticate": "Bearer"},
	)

	try:
		payload = jwt.decode(
			credentials.credentials,
			JWT_SECRET_KEY,
			algorithms=[JWT_ALGORITHM],
		)
		user_id = int(payload.get("sub", ""))
	except (JWTError, ValueError):
		raise unauthorized

	user = db.query(User).filter(User.id == user_id).first()
	if user is None or not user.is_active:
		raise unauthorized
	return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
	username = request.username.strip()
	email = request.email.strip().lower()

	if len(username) < 3:
		raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
	if len(request.password) < 8:
		raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
	if "@" not in email:
		raise HTTPException(status_code=400, detail="Enter a valid email address")
	if db.query(User).filter((User.username == username) | (User.email == email)).first():
		raise HTTPException(status_code=409, detail="Username or email is already registered")

	user = User(
		username=username,
		email=email,
		password_hash=password_hash.hash(request.password),
	)
	db.add(user)
	db.commit()
	db.refresh(user)

	return {"id": user.id, "username": user.username, "email": user.email}


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
	email = request.email.strip().lower()
	user = db.query(User).filter(User.email == email).first()

	if user is None or not password_hash.verify(request.password, user.password_hash):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect email or password",
		)

	return {
		"access_token": create_access_token(user.id),
		"token_type": "bearer",
		"user": {"id": user.id, "username": user.username, "email": user.email},
	}


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
	return {"id": user.id, "username": user.username, "email": user.email}
