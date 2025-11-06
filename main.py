import os, traceback
from fastapi import FastAPI, Request, Header, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from llm import call_llm, list_model_ids, MODEL_ID

# ---- 基本護欄與友善降級訊息 ----
MAX_INPUT_LEN = 800
FALLBACKS = {
    "TIMEOUT": "我想太久了，先給你短答～可以換個說法或等我再試一次 ✨",
    "QUOTA_EXCEEDED": "今天有點忙（額度滿了），等一下再問我一次好嗎？",
    "MODEL_NOT_FOUND": "目前模型設定怪怪的，我會請管理者檢查一下。",
    "PERMISSION_DENIED_API_OR_KEY": "金鑰或權限可能有誤，我會請管理者處理。",
    "BAD_REQUEST_PAYLOAD": "我不太確定你的說法格式，能換個方式描述嗎？",
    "EMPTY_RESPONSE": "我暫時沒有好答案，能否換個問法？",
    "GOOGLE_API_ERROR": "和模型連線遇到小狀況，我們再試試看。",
    "_DEFAULT": "剛剛卡住了，我們再試一次吧 🙏"
}

# ---- 環境變數 ----
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

# ---- LINE SDK ----
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(CHANNEL_SECRET)
# 修正拼字 + 兼容舊變數名
working_status = os.getenv("DEFAULT_TALKING", os.getenv("DEFALUT_TALKING", "true")).lower() == "true"

# ---- FastAPI App 與 CORS ----
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

    # 只收文字
    if event.type != "message" or event.message.type != "text":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="目前只接受文字訊息喔～"))
        return

    # 基本護欄：空白/長度
    user_text = (event.message.text or "").strip()
    if not user_text:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="可以再多說一點嗎？"))
        return

    if len(user_text) > MAX_INPUT_LEN:
        user_text = user_text[:MAX_INPUT_LEN] + "…（已截斷過長訊息）"

    # 簡單指令例
    if user_text == "再見":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Bye!"))
        return

    if not working_status:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="我現在休息一下，等等再聊～"))
        return

    # 呼叫 LLM + 友善降級
    try:
        out = call_llm(user_text) or "EMPTY_RESPONSE"
        if out == "EMPTY_RESPONSE":
            raise RuntimeError("EMPTY_RESPONSE")
    except Exception as e:
        label = str(e)
        # 依錯誤標籤選擇 fallback（TIMEOUT / QUOTA_EXCEEDED / …）
        msg = next((v for k, v in FALLBACKS.items() if k != "_DEFAULT" and label.startswith(k)), FALLBACKS["_DEFAULT"])
        print("[LLM ERROR]", label, flush=True)
        out = msg

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=out))
