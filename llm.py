import os
import google.generativeai as genai
from google.api_core.exceptions import (
    NotFound, PermissionDenied, InvalidArgument, ResourceExhausted, GoogleAPICallError
)
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

API_KEY = os.environ["GOOGLE_API_KEY"]
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # 可用 Secrets 覆蓋

genai.configure(api_key=API_KEY)

_generation_config = genai.types.GenerationConfig(
    max_output_tokens=2048, temperature=0.2, top_p=0.5, top_k=16
)
_model = genai.GenerativeModel(
    MODEL_ID,
    system_instruction="你是一個小天使。先用一小句夢幻的場景開場，再用清楚、親切的人話回答。"
)

_EXECUTOR = ThreadPoolExecutor(max_workers=4)

def _invoke(prompt: str) -> str:
    res = _model.generate_content(prompt, generation_config=_generation_config)
    txt = (getattr(res, "text", None) or "").strip()
    if not txt and getattr(res, "candidates", None):
        parts = res.candidates[0].content.parts or []
        txt = "".join(getattr(p, "text", "") for p in parts).strip()
    if not txt:
        raise RuntimeError("EMPTY_RESPONSE")
    return txt

def call_llm(prompt: str, timeout_s: float = 8.0) -> str:
    """主要出入口：加上逾時、把常見錯誤轉成可讀標籤。"""
    try:
        return _EXECUTOR.submit(_invoke, prompt).result(timeout=timeout_s)

    except FuturesTimeout as e:
        raise RuntimeError("TIMEOUT") from e
    except NotFound as e:
        raise RuntimeError(f"MODEL_NOT_FOUND:{MODEL_ID}") from e
    except PermissionDenied as e:
        raise RuntimeError("PERMISSION_DENIED_API_OR_KEY") from e
    except ResourceExhausted as e:
        raise RuntimeError("QUOTA_EXCEEDED") from e
    except InvalidArgument as e:
        raise RuntimeError("BAD_REQUEST_PAYLOAD") from e
    except GoogleAPICallError as e:
        raise RuntimeError(f"GOOGLE_API_ERROR:{str(e)}") from e

def list_model_ids():
    return [m.name.split("/")[-1] for m in genai.list_models()]
