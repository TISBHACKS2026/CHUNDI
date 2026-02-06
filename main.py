import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from supabase import create_client
from dotenv import load_dotenv
from fastapi import Header, HTTPException, Depends
import tempfile
import uuid
import uvicorn
from src.convert_to_raw_text import extract_text_from_file
from src.scrape_web import browse_allowed_sources
from datetime import datetime, timedelta

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

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


class ChatMessage(BaseModel):
    topic_id: str | None = None
    chat_id: str | None = None
    message: str


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
    return templates.TemplateResponse("starter.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def serve_signup(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
async def serve_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def serve_signup(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def serve_uploads(request: Request):
    return templates.TemplateResponse("upload_docs.html", {"request": request})


@app.post("/api/login")
async def login(data: LoginData):
    email = data.email
    password = data.password

    if len(password) < 6:
        return {"error": "Password must be at least 6 characters"}


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


@app.post("/api/update-profile")
async def update_profile(data: dict, authorization: str = Header(None)):
    try:
        if not authorization:
            return {"error": "Missing authentication token"}

        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token).user
        if not user:
            return {"error": "Invalid token"}

        display_name = data.get("display_name", "").strip()
        if not display_name:
            return {"error": "Display name cannot be empty"}

        print(f"Updating display name for user {user.id} to: {display_name}")
        result = supabase.auth.update_user({
            "data": {"display_name": display_name}
        })
        if result and hasattr(result, 'user') and result.user:
            print(f"Successfully updated display name in auth system")
            return {"success": True, "display_name": display_name}
        else:
            print(f"Auth update returned: {result}")
            return {"error": "Failed to update profile in authentication system"}

    except Exception as e:
        print(f"Update profile error: {e}")
        error_msg = str(e)
        if "session" in error_msg.lower() or "jwt" in error_msg.lower():
            return {"error": "Session expired. Please log out and log in again."}
        return {"error": "Failed to update profile. Please try again."}


@app.get("/api/me")
async def get_me(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token).user

        display_name = user.user_metadata.get("display_name", "User")
        if not display_name or display_name == "User":
            display_name = user.email.split('@')[0]

        return {
            "user_id": user.id,
            "email": user.email,
            "display_name": display_name
        }
    except Exception as e:
        print(f"Get me error: {e}")
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

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": "You are a topic extraction assistant."
                },
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ],
        )

        topic_output = response.output_text.strip()

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


@app.post("/api/chat/send")
async def send_chat_message(
        chat_data: ChatMessage,
        current_user=Depends(get_current_user)
):
    chat_id = chat_data.chat_id or str(uuid.uuid4())

    document_content = ""
    if chat_data.topic_id:
        doc = (
            supabase.table("documents")
            .select("content")
            .eq("id", chat_data.topic_id)
            .eq("user_id", current_user.id)
            .execute()
        )
        if doc.data:
            document_content = doc.data[0]["content"]

    res = (
        supabase.table("allowed_sources")
        .select("domain")
        .eq("user_id", current_user.id)
        .execute()
    )

    ALLOWED_DOMAINS = [r["domain"] for r in res.data]

    domain_selection_prompt = f"""
You may request information from EXACTLY ONE of the following allowed domains:

{", ".join(ALLOWED_DOMAINS)}

If external information is useful, respond ONLY in valid JSON:

{{
  "domain": "<one allowed domain>",
  "query": "<search query>"
}}

If no external information is needed, respond with:

{{ "domain": null }}
"""

    selection = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": domain_selection_prompt},
            {"role": "user", "content": chat_data.message}
        ],
    )

    import json
    try:
        decision = json.loads(selection.output_text)
    except Exception:
        decision = {"domain": None}

    chosen_domain = decision.get("domain")
    query = decision.get("query", chat_data.message)

    if chosen_domain not in ALLOWED_DOMAINS:
        chosen_domain = None
    web_context = ""
    if chosen_domain:
        web_context = browse_allowed_sources(
            query=query,
            forced_domain=chosen_domain,
            max_pages_per_domain=2
        )

    with open("prompt/prompt.md") as f:
        tutor_prompt = f.read()

    history = (
        supabase.table("chat_messages")
        .select("role, content")
        .eq("user_id", current_user.id)
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)
        .limit(12)
        .execute()
    )

    messages = [
        {
            "role": "system",
            "content": "You are an AI tutor following the specified framework."
        },
        {
            "role": "system",
            "content": f"""
DOCUMENT CONTEXT:
{document_content[:2000] if document_content else "None"}

EXTERNAL REFERENCE MATERIAL:
{web_context[:2000] if web_context else "None"}

INSTRUCTIONS:
{tutor_prompt}
"""
        }
    ]

    for m in history.data or []:
        messages.append({"role": m["role"], "content": m["content"]})

    messages.append({"role": "user", "content": chat_data.message})

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=messages,
    )

    ai_text = response.output_text.strip()

    supabase.table("chat_messages").insert([
        {
            "user_id": current_user.id,
            "topic_id": chat_data.topic_id,
            "chat_id": chat_id,
            "role": "user",
            "content": chat_data.message
        },
        {
            "user_id": current_user.id,
            "topic_id": chat_data.topic_id,
            "chat_id": chat_id,
            "role": "assistant",
            "content": ai_text
        }
    ]).execute()

    return {
        "chat_id": chat_id,
        "ai_response": ai_text
    }


@app.get("/api/chat/list/{topic_id}")
async def list_chats(topic_id: str, current_user=Depends(get_current_user)):
    result = (
        supabase.table("chat_messages")
        .select("chat_id, created_at")
        .eq("user_id", current_user.id)
        .eq("topic_id", topic_id)
        .order("created_at", desc=True)
        .execute()
    )

    chats = list({row["chat_id"] for row in result.data})
    return {"chats": chats}


@app.get("/api/chat/history/{chat_id}")
async def get_chat_history(chat_id: str, current_user=Depends(get_current_user)):
    """Get all messages from a specific chat session"""
    try:
        result = (
            supabase.table("chat_messages")
            .select("role, content, created_at")
            .eq("user_id", current_user.id)
            .eq("chat_id", chat_id)
            .order("created_at", desc=False)
            .execute()
        )

        messages = [
            {
                "role": msg["role"],
                "content": msg["content"],
                "is_user": msg["role"] == "user"
            }
            for msg in result.data
        ]

        return {"messages": messages}
    except Exception as e:
        print(f"Chat history error: {e}")
        return {"messages": []}


@app.get("/api/chat/topics")
async def get_chat_topics(current_user=Depends(get_current_user)):
    result = supabase.table("documents").select("id, topic").eq("user_id", current_user.id).execute()
    return {"topics": result.data}


@app.get("/api/get_topics")
async def get_topics(current_user=Depends(get_current_user)):
    result_topics = supabase.table("documents").select("topic").eq("user_id", current_user.id).execute()
    result_content = supabase.table("documents").select("content").eq("user_id", current_user.id).execute()
    print(result_topics)
    print(result_content)
    return {"result_topics": result_topics.data, "result_content": result_content.data}


@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user=Depends(get_current_user)):
    try:
        chat_result = (
            supabase.table("chat_messages")
            .select("chat_id")
            .eq("user_id", current_user.id)
            .execute()
        )
        unique_chats = len(set(row["chat_id"] for row in chat_result.data))

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        week_result = (
            supabase.table("chat_messages")
            .select("id")
            .eq("user_id", current_user.id)
            .gte("created_at", week_ago)
            .execute()
        )
        week_count = len(week_result.data)

        return {
            "chat_count": unique_chats,
            "week_count": week_count
        }
    except Exception as e:
        print(f"Stats error: {e}")
        return {
            "chat_count": 0,
            "week_count": 0
        }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/topics", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("topics.html", {"request": request})


@app.get("/sources", response_class=HTMLResponse)
async def sources(request: Request):
    return templates.TemplateResponse("add_sources.html", {"request": request})

@app.get("/api/sources")
async def get_sources(current_user=Depends(get_current_user)):
    res = (
        supabase.table("allowed_sources")
        .select("id, domain")
        .eq("user_id", current_user.id)
        .execute()
    )
    return {"sources": res.data}


@app.post("/api/sources")
async def add_source(data: dict, current_user=Depends(get_current_user)):
    domain = data.get("domain", "").strip().lower()

    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="Invalid domain")

    supabase.table("allowed_sources").insert({
        "user_id": current_user.id,
        "domain": domain
    }).execute()

    return {"success": True}


@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: str, current_user=Depends(get_current_user)):
    supabase.table("allowed_sources") \
        .delete() \
        .eq("id", source_id) \
        .eq("user_id", current_user.id) \
        .execute()

    return {"success": True}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
