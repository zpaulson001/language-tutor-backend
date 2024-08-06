from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session
from . import crud, db_models, schemas
from .database import SessionLocal, engine
import jwt

import os
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

db_models.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/")
async def get_token(email: EmailStr, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=email)
    if user:
        payload = {"sub": user.email, "exp": datetime.utcnow() + timedelta(hours=1)}

        access_token = jwt.encode(payload, os.getenv("SECRET"), algorithm="HS256")

        print(
            f"Sending magic link http://localhost:3000/tada?token={access_token} to {user.email}"
        )
    return {"message": "Email sent"}


@app.get("/users", response_model=list[schemas.User])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db=db)
    return users


@app.post("/create_user", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)
