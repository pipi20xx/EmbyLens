import openai
from app.services.config_service import ConfigService
from app.utils.logger import logger

class AIService:
    _client = None
    _config_cache = {}

    @classmethod
    async def get_config(cls):
        """获取 AI 相关配置"""
        provider = await ConfigService.get("ai_provider", "openai")
        api_key = await ConfigService.get("ai_api_key", "")
        base_url = await ConfigService.get("ai_base_url", "https://api.openai.com/v1")
        model = await ConfigService.get("ai_model", "gpt-3.5-turbo")
        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }

    @classmethod
    async def _get_client(cls):
        """获取或初始化 OpenAI 客户端"""
        config = await cls.get_config()
        
        # 简单缓存检查，如果配置变更则重新创建客户端
        current_cache_key = f"{config['provider']}|{config['api_key']}|{config['base_url']}"
        if cls._client is None or cls._config_cache.get("key_hash") != current_cache_key:
            # 对于 Ollama，API Key 可以为空
            if config['provider'] == 'openai' and not config["api_key"]:
                return None
            
            # 如果是 Ollama 且没填 key，给一个占位符，因为 SDK 往往要求有值
            api_key = config["api_key"] if config["api_key"] else "ollama"
            
            cls._client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=config["base_url"]
            )
            cls._config_cache["key_hash"] = current_cache_key
            
        return cls._client

    @classmethod
    async def chat_completion(cls, messages: list):
        """发送聊天请求"""
        client = await cls._get_client()
        if not client:
            raise ValueError("AI API Key not configured")

        config = await cls.get_config()
        
        logger.info(f"🤖 [AI请求] Provider: {config['provider']}, Model: {config['model']}")
        logger.debug(f"💬 [AI内容] Messages: {messages}")
        
        try:
            response = await client.chat.completions.create(
                model=config["model"],
                messages=messages,
                stream=True  # 启用流式响应
            )
            return response
        except Exception as e:
            logger.error(f"❌ [AI错误] {str(e)}")
            raise e

    @classmethod
    async def chat_json(cls, messages: list):
        """发送聊天请求并获取完整的 JSON 响应 (内部逻辑使用)"""
        client = await cls._get_client()
        if not client:
            raise ValueError("AI API Key not configured")

        config = await cls.get_config()
        
        try:
            response = await client.chat.completions.create(
                model=config["model"],
                messages=messages,
                stream=False,
                response_format={ "type": "json_object" } if config['provider'] == 'openai' else None
            )
            content = response.choices[0].message.content
            return content
        except Exception as e:
            logger.error(f"❌ [AI JSON请求错误] {str(e)}")
            raise e
