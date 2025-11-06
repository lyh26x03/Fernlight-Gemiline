import os, traceback
from fastapi import FastAPI, Request, Header, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ✨ 新增：只從 llm.py 匯入
from llm import call_llm, list_model_ids, MODEL_ID

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(CHANNEL_SECRET)
working_status = os.getenv("DEFALUT_TALKING", "true").lower() == "true"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return "OK"

@app.get("/diag")
def diag():
    return {
        "model": MODEL_ID,
        "has_google_key": bool(GOOGLE_API_KEY),
        "working_status": working_status
    }

@app.get("/list_models")
def list_models():
    try:
        return {"ids": list_model_ids()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test_llm")
def test_llm():
    try:
        txt = call_llm("用三點說明你是誰")
        return {"ok": True, "text": txt}
    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks, x_line_signature=Header(None)):
    body = await request.body()
    try:
        background_tasks.add_task(line_handler.handle, body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "ok"

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.type != "message" or event.message.type != "text":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="只接受文字訊息"))
        return

    if event.message.text.strip() == "再見":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Bye!"))
        return

    if working_status:
        try:
            out = call_llm(event.message.text) or "Gemini沒答案!請換個說法！"
        except Exception:
            print("[LLM ERROR]", traceback.format_exc(), flush=True)
            out = "Gemini執行出錯!請換個說法！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=out))
