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



# import traceback, csv, time, pathlib
# import requests  # ← 新增
# import json, os
# import gradio as gr
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi import FastAPI, Request,  Header, BackgroundTasks, HTTPException, status
# import google.generativeai as genai

# from linebot import LineBotApi, WebhookHandler
# from linebot.exceptions import InvalidSignatureError
# from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, AudioMessage

# # 設定 Google AI API 金鑰
# genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# # 設定生成文字的參數
# generation_config = genai.types.GenerationConfig(max_output_tokens=2048, temperature=0.2, top_p=0.5, top_k=16)

# # 使用模型
# model = genai.GenerativeModel('gemini-2.5-flash', system_instruction="你是一個小天使，請使用夢幻的場景描述做開頭，然後回答問題。") # 或是使用 "你是博通古今的萬應機器人！"
# # model = genai.GenerativeModel(
# #                               model_name="gemini-2.5-flash",
# #                               generation_config=generation_config
# # )

# # chat_session = model.start_chat(
# #                                 history=[
# #                                         {
# #                                           "role": "user",
# #                                           "parts": [
# #                                             "hi",
# #                                           ],
# #                                         },
# #                                         {
# #                                           "role": "model",
# #                                           "parts": [
# #                                             "Hi there! How can I help you today?\n",
# #                                           ],
# #                                         },
# #                                         ]
# #                                 )
# # 設定 Line Bot 的 API 金鑰和秘密金鑰
# line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
# line_handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

# # 設定是否正在與使用者交談
# working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

# # 建立 FastAPI 應用程式
# app = FastAPI()
# @app.get("/health")
# def health():
#     return "OK"

# @app.get("/diag")
# def diag():
#     return {
#         "model": "gemini-1.5-flash",
#         "has_google_key": bool(os.getenv("GOOGLE_API_KEY")),
#         "working_status": working_status
#     }
# @app.get("/test_llm")
# def test_llm():
#     try:
#         out = call_gemini_v1("用三點說明你是誰")
#         return {"ok": True, "text": out.strip()}
#     except Exception as e:
#         import traceback
#         return {"ok": False, "error": str(e), "trace": traceback.format_exc()}
# @app.get("/routes")
# def routes():
#     return [r.path for r in app.router.routes]




# # 設定 CORS，允許跨域請求
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 處理根路徑請求
# @app.get("/")
# def root():
#     return {"title": "Line Bot"}

# # 處理 Line Webhook 請求
# @app.post("/webhook")
# async def webhook(
#     request: Request,
#     background_tasks: BackgroundTasks,
#     x_line_signature=Header(None),
# ):
#     # 取得請求內容
#     body = await request.body()
#     try:
#         # 將處理 Line 事件的任務加入背景工作
#         background_tasks.add_task(
#             line_handler.handle, body.decode("utf-8"), x_line_signature
#         )
#     except InvalidSignatureError:
#         # 處理無效的簽章錯誤
#         raise HTTPException(status_code=400, detail="Invalid signature")
#     return "ok"

# # 處理文字訊息事件
# @line_handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     global working_status
    
#     # 檢查事件類型和訊息類型
#     if event.type != "message" or event.message.type != "text":
#         # 回覆錯誤訊息
#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(text="Event type error:[No message or the message does not contain text]")
#         )
        
#     # 檢查使用者是否輸入 "再見"
#     elif event.message.text == "再見":
#         # 回覆 "Bye!"
#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(text="Bye!")
#         )
#         return
       
#     # 檢查是否正在與使用者交談
#     elif working_status:
#         try: 
#             # 取得使用者輸入的文字
#             prompt = event.message.text
#             # 使用 Gemini 模型生成文字
#             # 10/22 11:００ 新增
#             try:
#                 out = call_gemini_v1(prompt).strip()
#                 if not out:
#                     out = "Gemini沒答案!請換個說法！"
#             except Exception:
#                 print("[GEMINI ERROR]", traceback.format_exc(), flush=True)
#                 out = "Gemini執行出錯!請換個說法！"
#             # 10/22 11:00 改為上段
#             # completion = model.generate_content(prompt, generation_config=generation_config)
#             # # response = chat_session.send_message(prompt)
#             # # 檢查生成結果是否為空
#             # if (completion.parts[0].text != None):
#             #     # 取得生成結果
#             #     out = completion.parts[0].text
#             # # if (response.text != None):
#             # #     # 取得生成結果
#             # #     out = response.text
#             # else:
#             #     out = "Gemini沒答案!請換個說法！"



                
#         except:
#             # 處理錯誤
#             out = "Gemini執行出錯!請換個說法！" 
  
#         # 回覆生成結果
#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(text=out))

# if __name__ == "__main__":
#     # 啟動 FastAPI 應用程式
#     uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)

# def call_gemini_v1(prompt: str) -> str:
#     url = "https://gemini.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
#     key = os.getenv("GOOGLE_API_KEY")
#     r = requests.post(
#         url,
#         params={"key": key},
#         json={"contents":[{"parts":[{"text": prompt}]}]},
#         timeout=20
#     )
#     r.raise_for_status()
#     data = r.json()
#     # 取第一個候選的第一段文字
#     return data["candidates"][0]["content"]["parts"][0]["text"]



# # # 設定生成文字的參數 #old
# # generation_config = genai.types.GenerationConfig(max_output_tokens=2048, temperature=0.2, top_p=0.5, top_k=16)

# # # 使用 Gemini-2.0-flash 模型 #old
# # model = genai.GenerativeModel('gemini-1.5-flash', system_instruction="你是一個小天使，請使用夢幻的場景描述做開頭，然後回答問題。")

# # ### new add
# # # Create the model
# # # model = genai.GenerativeModel
# # #   "gemini-2.0-flash",
# # #   generation_config=(
# # #   "temperature": 1,
# # #   "top_p": 0.95,
# # #   "top_k": 40
# # # ),
# # #   system_instruction="你是一個小天使，請使用夢幻的場景描述做開頭，然後回答問題。",
# # # }

# # chat_session = model.start_chat(
# #   history=[
# #   ])
# # ###


# # # 設定 Line Bot 的 API 金鑰和秘密金鑰
# # line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
# # line_handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

# # # 設定是否正在與使用者交談
# # working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

# # # 建立 FastAPI 應用程式
# # app = FastAPI()

# # # 設定 CORS，允許跨域請求
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # # 處理根路徑請求
# # @app.get("/")
# # def root():
# #     return {"title": "Line Bot"}

# # # 處理 Line Webhook 請求
# # @app.post("/webhook")
# # async def webhook(
# #     request: Request,
# #     background_tasks: BackgroundTasks,
# #     x_line_signature=Header(None),
# # ):
# #     # 取得請求內容
# #     body = await request.body()
# #     try:
# #         # 將處理 Line 事件的任務加入背景工作
# #         background_tasks.add_task(
# #             line_handler.handle, body.decode("utf-8"), x_line_signature
# #         )
# #     except InvalidSignatureError:
# #         # 處理無效的簽章錯誤
# #         raise HTTPException(status_code=400, detail="Invalid signature")
# #     return "ok"

# # # 處理文字訊息事件
# # @line_handler.add(MessageEvent, message=TextMessage)
# # def handle_message(event):
# #     global working_status
    
# #     # 檢查事件類型和訊息類型
# #     if event.type != "message" or event.message.type != "text":
# #         # 回覆錯誤訊息
# #         line_bot_api.reply_message(
# #             event.reply_token,
# #             TextSendMessage(text="Event type error:[No message or the message does not contain text]")
# #         )
        
# #     # 檢查使用者是否輸入 "再見"
# #     elif event.message.text == "再見":
# #         # 回覆 "Bye!"
# #         line_bot_api.reply_message(
# #             event.reply_token,
# #             TextSendMessage(text="Bye!")
# #         )
# #         return
       
# #     # 檢查是否正在與使用者交談
# #     elif working_status:
# #         try: 
# #             # 取得使用者輸入的文字
# #             prompt = event.message.text
# #             # 使用 Gemini 模型生成文字
# #             completion = model.generate_content(prompt, generation_config=generation_config) # old
# #             response = chat_session.send_message(prompt, generation_config=generation_config)
# #             # completion = chat_session.send_message(prompt, generation_config=generation_config)
# #             # 檢查生成結果是否為空
# #             if (completion.parts[response].text != None):
# #                 # 取得生成結果
# #                 out = completion.parts[response].text
# #             else:
# #                 # 回覆 "Gemini沒答案!請換個說法！"
# #                 out = "Gemini沒答案!請換個說法！"
# #         except:
# #             # 處理錯誤
# #             out = "Gemini執行出錯!請換個說法！" 
  
# #         # 回覆生成結果
# #         line_bot_api.reply_message(
# #             event.reply_token,
# #             TextSendMessage(text=out))

# # if __name__ == "__main__":
# #     # 啟動 FastAPI 應用程式
# #     uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)

# # 註解說明：
# # import 導入必要的套件
# # genai.configure 設定 Google AI API 金鑰
# # generation_config 設定文字生成參數
# # model 設定使用的 Gemini 模型
# # line_bot_api 和 line_handler 設定 Line Bot API 和 webhook 處理器
# # working_status 設定是否正在與使用者交談
# # app 建立 FastAPI 應用程式
# # app.add_middleware 設定 CORS
# # @app.get("/") 處理根路徑請求
# # @app.post("/webhook") 處理 Line Webhook 請求
# # @line_handler.add(MessageEvent, message=TextMessage) 處理文字訊息事件
# # if __name__ == "__main__": 啟動 FastAPI 應用程式
# # 程式碼功能說明：
# # 程式碼首先會導入必要的套件，並設定 Google AI API 金鑰、文字生成參數、Gemini 模型以及 Line Bot API。
# # 接著會建立 FastAPI 應用程式，並設定 CORS。
# # 程式碼會定義兩個函數：
# # root() 處理根路徑請求，返回一個簡單的 JSON 訊息。
# # webhook() 處理 Line Webhook 請求，將處理 Line 事件的任務加入背景工作，並處理無效的簽章錯誤。
# # 程式碼還定義一個函數 handle_message() 來處理文字訊息事件，它會檢查事件類型和訊息類型，並根據使用者輸入執行不同的動作：
# # 如果使用者輸入 "再見"，回覆 "Bye!"。
# # 如果正在與使用者交談，則會使用 Gemini 模型生成文字，並將結果回覆給使用者。
# # 最後，程式碼會啟動 FastAPI 應用程式，開始監聽 HTTP 請求。
# # 程式碼運行方式：
# # 將程式碼存為 main.py 文件。
# # 在環境變數中設定 GOOGLE_API_KEY、CHANNEL_ACCESS_TOKEN 和 CHANNEL_SECRET。
# # 執行 uvicorn main:app --host 0.0.0.0 --port 7860 --reload 命令啟動 FastAPI 應用程式。
# # 使用 Line 帳戶與 Line Bot 進行對話。
# # 注意：
# # 程式碼中使用 os.environ["GOOGLE_API_KEY"]、os.environ["CHANNEL_ACCESS_TOKEN"] 和 os.environ["CHANNEL_SECRET"] 來存取環境變數，需要先在環境變數中設定這些值。
# # 程式碼中使用 uvicorn 執行 FastAPI 應用程式，需要先安裝 uvicorn 套件。
# # 程式碼中使用 google.generativeai 套件，需要先安裝 google-generativeai 套件。
# # 程式碼中使用 linebot 套件，需要先安裝 linebot 套件。