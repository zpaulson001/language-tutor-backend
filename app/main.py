from datetime import datetime, timedelta, timezone
import json
from groq import Groq
from redis import Redis
from fastapi import FastAPI, Depends, HTTPException, Request, Response
import spacy
from spacy.language import Language
from sqlalchemy.orm import Session
from . import crud, db_models, schemas
from .database import SessionLocal, engine
import uuid
import jwt
import pinyin

import os
from dotenv import load_dotenv

load_dotenv()

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

    payload = {"sub": user.id, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}

    access_token = jwt.encode(payload, os.getenv("SECRET"), algorithm="HS256")

    # TODO - Add actual email service
    print(
        f"Sending magic link: {os.getenv("FRONTEND_URL")}/tada/{access_token} to {user.email}"
    )
    return {"message": "Email sent"}


@app.post("/tada/{token}")
def login(token: str, response: Response, rc: Redis = Depends(get_rc)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET"), algorithms=["HS256"])

        user_id  = payload["sub"]

        session_id = str(uuid.uuid4())

        rc.set(f"session:{session_id}", user_id)

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
def read_user(
    session_id: str = Depends(get_session_id),
    rc: Redis = Depends(get_rc),
):
    user_id = rc.get(f"session:{session_id}")
    if not user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"user_id": user_id}


@app.post("/logout")
def logout(session_id: str = Depends(get_session_id), rc: Redis = Depends(get_rc)):
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


@app.post("/story")
def generate_story( story_request: schemas.StoryGenerate,
    nlp: Language = Depends(get_nlp),
    rc: Redis = Depends(get_rc),
):

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"You are a language tutor helping a student learning Chinese through stories. Your student is {story_request.level} level.  Your job is to take the given prompt and generate a short story using simplified Chinese characters. Don't include any English or any translation.",
            },
            {"role": "user", "content": story_request.story_prompt},
        ],
        model="llama-3.1-70b-versatile",
    )

    message = chat_completion.choices[0].message.content

    doc = nlp(message)

    words = []

    for token in doc:
        response = {
            "token": token.text,
            "is_word": token.is_alpha,
            "ent_type": token.ent_type_,
            "meaning": None,
            "pinyin": None,
        }

        if token.is_alpha:
            result = rc.get(f"dict:{token.text}")
            jsonResult = json.loads(result) if result else None
            if jsonResult:
                response["meaning"] = jsonResult["english"]
                response["pinyin"] = pinyin.get(token.text)

        words.append(response)

    return words
