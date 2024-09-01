from datetime import datetime, timedelta
import redis
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from . import crud, db_models, schemas
from .database import SessionLocal, engine
import uuid
import jwt

import os
from dotenv import load_dotenv

load_dotenv()


rc = redis.Redis(
    host=os.getenv("UPSTASH_HOST"),
    password=os.getenv("UPSTASH_PASSWORD"),
    port=6379,
    ssl=True,
)


app = FastAPI()

db_models.Base.metadata.create_all(bind=engine)


# Dependency - DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency - Reids Client
def get_rc():
    rc = Redis(
        host="localhost",
        port=6379,
    )
    try:
        yield rc
    finally:
        rc.close()


def get_nlp():
    nlp = spacy.load("zh_core_web_sm")
    yield nlp


# Dependency to check for the session_id cookie
def get_session_id(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None:
        raise HTTPException(status_code=400, detail="Session ID cookie not set")
    return session_id


@app.get("/")
async def root():
    return {"message": "Look out world 👀"}


@app.post("/login")
def get_token(request_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=request_data.email)
    if not user:
        new_user = schemas.UserCreate(email=request_data.email)
        user = crud.create_user(db, new_user)

    payload = {"sub": user.id, "exp": datetime.utcnow() + timedelta(hours=12)}

    access_token = jwt.encode(payload, os.getenv("SECRET"), algorithm="HS256")

    # TODO - Add actual email service
    print(
        f"Sending magic link http://localhost:5173/tada/{access_token} to {user.email}"
    )
    return {"message": "Email sent"}


@app.post("/tada/{token}")
def login(token: str, response: Response, rc: Redis = Depends(get_rc)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET"), algorithms=["HS256"])

        payload["sub"]

        session_id = str(uuid.uuid4())

        rc.set(f"session:{session_id}", payload["sub"])

        response.set_cookie(key="session_id", value=session_id, httponly=True)

        return {"session_id": session_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/users", response_model=list[schemas.User])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db=db)
    return users


@app.get("/auth")
def read_user(session_id: str = Depends(get_session_id), db: Session = Depends(get_db)):
    user_id = rc.get(f"session:{session_id}")
    return {"user_id": user_id}


@app.post("/logout")
def logout(session_id: str = Depends(get_session_id)):
    result = rc.delete(f"session:{session_id}")
    if result == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Logged out successfully"}


@app.post("/user", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)
