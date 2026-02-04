import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from supabase import create_client
from dotenv import load_dotenv
import uvicorn
from fastapi import Header, HTTPException, Depends
import tempfile
import openai
from src.convert_to_raw_text import extract_text_from_file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Supabase env vars not loaded")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class LoginData(BaseModel):
    email: str
    username: str
    password: str


class SignupData(BaseModel):
    email: str
    username: str
    password: str


def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token).user
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/", response_class=HTMLResponse)
async def serve_login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
async def serve_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def serve_uploads(request: Request):
    return templates.TemplateResponse("upload_docs.html", {"request": request})
@app.post("/api/login")
async def login(data: LoginData):
    email = data.email
    password = data.password

    if len(password) < 6:
        return {"error": "Password must be at least 6 characters"}

    # Try login
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if result.user:
            return {
                "status": "logged_in",
                "user_id": result.user.id,
                "email": result.user.email,
                "display_name": result.user.user_metadata.get("display_name"),
                "access_token": result.session.access_token
            }
        # Invalid login (wrong password or no account)
        return {"error": "Invalid username/password"}
    except Exception as e:
        print("LOGIN ERROR:", e)
        return {"error": "Invalid username/password"}


@app.post("/api/signup")
async def signup(data: SignupData):
    email = data.email
    username = data.username
    password = data.password

    if len(password) < 6:
        return {"error": "Password must be at least 6 characters"}

    # Try signup
    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"display_name": username}
            }
        })
        if result.user:
            return {
                "status": "signed_up",
                "user_id": result.user.id,
                "email": result.user.email,
                "display_name": result.user.user_metadata.get("display_name"),
                "access_token": result.session.access_token
            }
        return {"error": "Signup failed"}
    except Exception as e:
        print("SIGNUP ERROR:", e)
        return {"error": str(e)}


@app.get("/api/me")
async def get_me(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token).user

        return {
            "user_id": user.id,
            "email": user.email,
            "display_name": user.user_metadata.get("display_name", "User")
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/api/upload")
async def upload_docs(
        request: Request,
        current_user=Depends(get_current_user)
):
    data = await request.form()
    uploaded_file = data['file']

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
        contents = await uploaded_file.read()
        temp_file.write(contents)

    try:
        file_extension = uploaded_file.filename.split('.')[-1]
        raw_text = extract_text_from_file(temp_path, file_extension)

        with open("prompt/topic_extraction_prompt.md", "r") as f:
            prompt_template = f.read()

        formatted_prompt = prompt_template.replace("{TEXT}", raw_text)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a topic extraction assistant."},
                {"role": "user", "content": formatted_prompt}
            ],
            max_tokens=20,
            temperature=0.0
        )

        topic_output = response['choices'][0]['message']['content'].strip()
        topic = topic_output.replace("Topic:", "").strip()

        print(f"Extracted Topic: {topic}")

        try:
            result = supabase.table("documents").insert({
                "user_id": current_user.id,
                "content": raw_text,
                "topic": topic
            }).execute()

            print(f"Saved to database: {result}")

        except Exception as db_error:
            print(f"Database error: {db_error}")

    finally:
        os.unlink(temp_path)

    return {
        "message": "File uploaded successfully",
        "topic": topic,
        "user_id": current_user.id,
        "saved_to_db": True
    }

@app.get("/api/get_topics")
async def get_topics(current_user=Depends(get_current_user)):
    result_topics = supabase.table("documents").select("topic").eq("user_id",current_user.id).execute()
    result_content = supabase.table("documents").select("content").eq("user_id",current_user.id).execute()
    print(result_topics)
    print(result_content)
    return {"result_topics" : result_topics.data, "result_content" : result_content.data}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/topics", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("topics.html", {"request": request})
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
