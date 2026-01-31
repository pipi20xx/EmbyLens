from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from app.services.ai_service import AIService
from app.services.config_service import ConfigService
from app.utils.auth import get_current_user
from app.utils.logger import logger

router = APIRouter()

class AIChatRequest(BaseModel):
    messages: List[dict]

class AIConfig(BaseModel):
    provider: str
    api_key: str
    base_url: str
    model: str

@router.get("/config")
async def get_ai_config(current_user = Depends(get_current_user)):
    """获取当前 AI 配置"""
    return await AIService.get_config()

@router.post("/config")
async def save_ai_config(config: AIConfig, current_user = Depends(get_current_user)):
    """保存 AI 配置"""
    await ConfigService.set("ai_provider", config.provider, "AI Service Provider")
    await ConfigService.set("ai_api_key", config.api_key, "AI Service API Key")
    await ConfigService.set("ai_base_url", config.base_url, "AI Service Base URL")
    await ConfigService.set("ai_model", config.model, "AI Service Model Name")
    return {"status": "success"}

@router.post("/chat")
async def chat(request: AIChatRequest, current_user = Depends(get_current_user)):
    """与 AI 对话 (流式)"""
    try:
        # 简单的生成器，用于流式传输
        async def generate():
            full_content = ""
            try:
                stream = await AIService.chat_completion(request.messages)
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_content += content
                        yield content
                logger.info(f"✅ [AI响应] 完成。长度: {len(full_content)}")
            except Exception as e:
                # 已经由 AIService 记录了 error，这里直接向上抛出
                yield f"\n[服务错误: {str(e)}]"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
