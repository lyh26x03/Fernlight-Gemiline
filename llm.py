# llm.py  — 單一路徑，用 google-generativeai SDK
import os
import google.generativeai as genai
from google.api_core.exceptions import (
    NotFound, PermissionDenied, InvalidArgument, ResourceExhausted, GoogleAPICallError
)

API_KEY = os.environ["GOOGLE_API_KEY"]               # HF Settings/Secrets 裡
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # 可用 Secrets 覆蓋
# Else  #gemini-2.0-flash-lite  #高流量和穩定

genai.configure(api_key=API_KEY)

_generation_config = genai.types.GenerationConfig(
    max_output_tokens=2048, temperature=0.2, top_p=0.5, top_k=16
)

_model = genai.GenerativeModel(
    MODEL_ID,
    system_instruction="你是一個小天使，請使用夢幻的場景描述做開頭，然後回答問題。"
)

def call_llm(prompt: str) -> str:
    """
    只走 SDK：減少錯點（endpoint/payload），錯誤統一由這裡拋出去。
    """
    try:
        res = _model.generate_content(prompt, generation_config=_generation_config)
        txt = (getattr(res, "text", None) or "").strip()
        if not txt and getattr(res, "candidates", None):
            parts = res.candidates[0].content.parts or []
            txt = "".join(getattr(p, "text", "") for p in parts).strip()
        if not txt:
            raise RuntimeError("EMPTY_RESPONSE")
        return txt

    # —— 常見幾類錯誤，拋出「可讀標籤」讓 main 記錄到 Logs ——
    except NotFound as e:
        # 模型 ID 不存在、或這把 key 看不到該型號
        raise RuntimeError(f"MODEL_NOT_FOUND:{MODEL_ID}") from e
    except PermissionDenied as e:
        # API 未啟用、Key 無權限、Key 限制不吻合
        raise RuntimeError("PERMISSION_DENIED_API_OR_KEY") from e
    except ResourceExhausted as e:
        # 配額/速率滿了
        raise RuntimeError("QUOTA_EXCEEDED") from e
    except InvalidArgument as e:
        # 請求內容不合法（payload 形狀、參數錯）
        raise RuntimeError("BAD_REQUEST_PAYLOAD") from e
    except GoogleAPICallError as e:
        raise RuntimeError(f"GOOGLE_API_ERROR:{str(e)}") from e

def list_model_ids():
    """
    回傳這把 key 真的「看得到」的 model ids，方便 /list_models 對齊。
    """
    return [m.name.split("/")[-1] for m in genai.list_models()]
