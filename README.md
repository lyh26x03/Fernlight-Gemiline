Fernlight: Gemiline · LINE Bot (FastAPI × Google Gemini)

一個溫柔的小天使 LINE 機器人：用 FastAPI 做 webhook、Google Gemini 生成回覆，部署在 Hugging Face Spaces。
目標很務實：穩、清楚、好維運；先把基礎打好，再慢慢長大。

特色 Highlights

核心聊天：中文優先，帶有「小天使」人設（system instruction）。

護欄 (Guardrails)：

合理溫度/長度設定、請求逾時（timeout）、錯誤保底訊息。

僅處理文字訊息，其他事件會回固定提示。

觀測 (Observability)：/health、/diag、/routes 方便排錯；stdout 結構化 log。

降級 (Degradation)：LLM 出錯時回覆親切的 fallback 文案，不讓對話中斷。

測試 (Quick tests)：/test_llm 可快速驗證 key/模型/網路是否可用。

註：本專案仍在持續補強測試覆蓋率、指標監測與自動化部署。

架構 Architecture
LINE User ──(Webhook)──> FastAPI (/webhook)
                          │
                          ├── llm.py (Google Generative AI SDK)
                          │     └─ 使用 gemini-2.5-flash、超時與錯誤保護
                          │
                          └── /health /diag /routes /test_llm
Secrets: GOOGLE_API_KEY / CHANNEL_ACCESS_TOKEN / CHANNEL_SECRET
Deploy: Hugging Face Spaces（可搭 GitHub Actions 自動推送）

環境變數
變數	說明
GOOGLE_API_KEY	Google Generative AI API 金鑰
CHANNEL_ACCESS_TOKEN	LINE Messaging API Channel access token
CHANNEL_SECRET	LINE Channel secret
DEFALUT_TALKING	（選用）true/false，控制是否回覆使用者（預設 true）

注意：變數名沿用現有程式中的拼字（DEFALUT_TALKING）。

本地開發（快速開始）
# 1) 安裝
pip install -r requirements.txt

# 2) 設定環境變數（舉例：Linux/macOS）
export GOOGLE_API_KEY=xxx
export CHANNEL_ACCESS_TOKEN=xxx
export CHANNEL_SECRET=xxx

# 3) 啟動
uvicorn main:app --host 0.0.0.0 --port 7860 --reload


本地測試：

# 健康檢查
curl http://localhost:7860/health
# 診斷資訊（會回傳模型與是否有 key）
curl http://localhost:7860/diag
# 可用路由
curl http://localhost:7860/routes
# 快速測 LLM
curl http://localhost:7860/test_llm


設定 LINE Webhook（開發期可用 ngrok 轉址）：

LINE Developers > Messaging API > Webhook URL 設為 https://你的公開網址/webhook

記得 啟用 Webhook、將 bot 加為好友。

部署到 Hugging Face Spaces

在 Space 的「Settings → Secrets」設定與上方相同的三個變數。

若要 GitHub Actions 自動部署，可新增 workflow（需 HF_TOKEN、HF_SPACE_ID）：

HF_SPACE_ID 例：lyh26x03/Fernlight-Gemiline

HF_TOKEN 到 HF 右上角 Tokens 產生，至少有寫入 Space 權限。

目前我採「GitHub 為主倉」→（選擇性）自動推送到新建的 HF Space。
若早期是從別人 Space fork，已將內容整理到自有倉庫，避免權限/同步混亂。

已知限制 & 後續規劃

目前為 Demo 級：無資料庫、無使用者狀態持久化。

Roadmap

心情日記（Mood Journal）：紀錄/標籤/回顧（DB + Flex Message）。

Rich Menu / Quick Replies：更友善的功能入口。

觀測：請求指標、錯誤率、簡單儀表板。

測試：單元測試（llm/handlers）、webhook 端到端測試。

降級策略：429/5xx 重試與退避、替代模型或回覆模板。

致謝 Credits

本專案靈感與早期結構來自教學範例，後續改造為自有倉庫與部署流程；若引用到他人程式片段，已在註解與文件中標註來源。



---
title: Gemiline
emoji: 🌖
colorFrom: red
colorTo: red
sdk: docker
pinned: true
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
