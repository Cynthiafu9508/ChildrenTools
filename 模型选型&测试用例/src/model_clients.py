"""
模型客户端封装
支持多个国内大模型API调用
"""
import json
import time
import requests
from typing import Dict, Optional, Any
from datetime import datetime


class ModelClient:
    """模型客户端基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = config.get("name", "Unknown")
        self.provider = config.get("provider", "")
        self.model_id = config.get("model_id", "")
        
    def chat(self, messages: list, stream: bool = False, **kwargs) -> Dict:
        """发送聊天请求
        
        Args:
            messages: 消息列表
            stream: 是否使用流式输出
            **kwargs: 其他参数
        """
        raise NotImplementedError
    
    def chat_stream(self, messages: list, **kwargs) -> Dict:
        """流式输出聊天请求，返回首token延迟和完整响应"""
        raise NotImplementedError
        
    def check_config(self) -> bool:
        """检查配置是否完整"""
        return True


class QwenClient(ModelClient):
    """通义千问客户端"""
    
    def check_config(self) -> bool:
        api_key = self.config.get("api_key", "")
        if not api_key:
            print(f"⚠️  {self.name}: 请在config/models_config.json中填写api_key")
            print(f"   推荐位置: {self.config.get('recommended_key_location', '')}")
            return False
        return True
    
    def chat(self, messages: list, stream: bool = False, **kwargs) -> Dict:
        if not self.check_config():
            return {"error": "配置不完整"}
        
        if stream:
            return self.chat_stream(messages, **kwargs)
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "latency": latency,
                    "ttfb": latency,  # 非流式时，TTFB等于总延迟
                    "tokens": result.get("usage", {}),
                    "model": self.name
                }
            else:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": latency
                }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def chat_stream(self, messages: list, **kwargs) -> Dict:
        """流式输出，测量首token延迟（TTFB）"""
        if not self.check_config():
            return {"error": "配置不完整"}
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": time.time() - start_time
                }
            
            # 读取流式响应
            content_parts = []
            ttfb = None
            first_token_time = None
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    # 记录首token时间
                                    if first_token_time is None:
                                        first_token_time = time.time()
                                        ttfb = first_token_time - start_time
                                    
                                    content_parts.append(delta['content'])
                        except json.JSONDecodeError:
                            continue
            
            total_latency = time.time() - start_time
            content = ''.join(content_parts)
            
            return {
                "content": content,
                "latency": total_latency,
                "ttfb": ttfb if ttfb is not None else total_latency,
                "tokens": {},  # 流式输出通常不返回token统计
                "model": self.name
            }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }


class DeepSeekClient(ModelClient):
    """DeepSeek客户端（兼容OpenAI格式）"""
    
    def check_config(self) -> bool:
        api_key = self.config.get("api_key", "")
        if not api_key:
            print(f"⚠️  {self.name}: 请在config/models_config.json中填写api_key")
            print(f"   推荐位置: {self.config.get('recommended_key_location', '')}")
            return False
        return True
    
    def chat(self, messages: list, stream: bool = False, **kwargs) -> Dict:
        if not self.check_config():
            return {"error": "配置不完整"}
        
        if stream:
            return self.chat_stream(messages, **kwargs)
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "latency": latency,
                    "ttfb": latency,  # 非流式时，TTFB等于总延迟
                    "tokens": result.get("usage", {}),
                    "model": self.name
                }
            else:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": latency
                }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def chat_stream(self, messages: list, **kwargs) -> Dict:
        """流式输出，测量首token延迟（TTFB）"""
        if not self.check_config():
            return {"error": "配置不完整"}
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": time.time() - start_time
                }
            
            # 读取流式响应
            content_parts = []
            ttfb = None
            first_token_time = None
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    # 记录首token时间
                                    if first_token_time is None:
                                        first_token_time = time.time()
                                        ttfb = first_token_time - start_time
                                    
                                    content_parts.append(delta['content'])
                        except json.JSONDecodeError:
                            continue
            
            total_latency = time.time() - start_time
            content = ''.join(content_parts)
            
            return {
                "content": content,
                "latency": total_latency,
                "ttfb": ttfb if ttfb is not None else total_latency,
                "tokens": {},  # 流式输出通常不返回token统计
                "model": self.name
            }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }


class GLMClient(ModelClient):
    """智谱GLM客户端"""
    
    def check_config(self) -> bool:
        api_key = self.config.get("api_key", "")
        if not api_key:
            print(f"⚠️  {self.name}: 请在config/models_config.json中填写api_key")
            print(f"   推荐位置: {self.config.get('recommended_key_location', '')}")
            return False
        return True
    
    def chat(self, messages: list, stream: bool = False, **kwargs) -> Dict:
        if not self.check_config():
            return {"error": "配置不完整"}
        
        if stream:
            return self.chat_stream(messages, **kwargs)
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "latency": latency,
                    "ttfb": latency,
                    "tokens": result.get("usage", {}),
                    "model": self.name
                }
            else:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": latency
                }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def chat_stream(self, messages: list, **kwargs) -> Dict:
        """流式输出，复用DeepSeekClient的逻辑（OpenAI兼容格式）"""
        if not self.check_config():
            return {"error": "配置不完整"}
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": time.time() - start_time
                }
            
            # 读取流式响应
            content_parts = []
            ttfb = None
            first_token_time = None
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    if first_token_time is None:
                                        first_token_time = time.time()
                                        ttfb = first_token_time - start_time
                                    content_parts.append(delta['content'])
                        except json.JSONDecodeError:
                            continue
            
            total_latency = time.time() - start_time
            content = ''.join(content_parts)
            
            return {
                "content": content,
                "latency": total_latency,
                "ttfb": ttfb if ttfb is not None else total_latency,
                "tokens": {},
                "model": self.name
            }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }


class ErnieClient(ModelClient):
    """文心一言客户端"""
    
    def check_config(self) -> bool:
        api_key = self.config.get("api_key", "")
        secret_key = self.config.get("secret_key", "")
        if not api_key or not secret_key:
            print(f"⚠️  {self.name}: 请在config/models_config.json中填写api_key和secret_key")
            print(f"   推荐位置: {self.config.get('recommended_key_location', '')}")
            return False
        return True
    
    def _get_access_token(self) -> Optional[str]:
        """获取access_token"""
        api_key = self.config.get("api_key")
        secret_key = self.config.get("secret_key")
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key
        }
        
        try:
            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get("access_token")
        except Exception as e:
            print(f"获取access_token失败: {e}")
        return None
    
    def chat(self, messages: list, **kwargs) -> Dict:
        if not self.check_config():
            return {"error": "配置不完整"}
            
        access_token = self._get_access_token()
        if not access_token:
            return {"error": "获取access_token失败"}
        
        api_base = self.config.get("api_base")
        model_id = self.model_id
        
        url = f"{api_base}/{model_id}"
        params = {"access_token": access_token}
        
        # 转换消息格式
        data = {
            "messages": messages
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, params=params, json=data, timeout=30)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    return {
                        "content": result["result"],
                        "latency": latency,
                        "tokens": result.get("usage", {}),
                        "model": self.name
                    }
                else:
                    return {
                        "error": f"API返回异常: {result}",
                        "latency": latency
                    }
            else:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": latency
                }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }


class DoubaoClient(ModelClient):
    """豆包客户端（兼容OpenAI格式）"""
    
    def check_config(self) -> bool:
        api_key = self.config.get("api_key", "")
        if not api_key:
            print(f"⚠️  {self.name}: 请在config/models_config.json中填写api_key")
            print(f"   推荐位置: {self.config.get('recommended_key_location', '')}")
            return False
        return True
    
    def chat(self, messages: list, stream: bool = False, **kwargs) -> Dict:
        if not self.check_config():
            return {"error": "配置不完整"}
        
        if stream:
            return self.chat_stream(messages, **kwargs)
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "latency": latency,
                    "ttfb": latency,
                    "tokens": result.get("usage", {}),
                    "model": self.name
                }
            else:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": latency
                }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def chat_stream(self, messages: list, **kwargs) -> Dict:
        """流式输出，复用DeepSeekClient的逻辑（OpenAI兼容格式）"""
        if not self.check_config():
            return {"error": "配置不完整"}
            
        api_key = self.config.get("api_key")
        api_base = self.config.get("api_base")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_id,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "error": f"API错误: {response.status_code}",
                    "message": response.text,
                    "latency": time.time() - start_time
                }
            
            # 读取流式响应
            content_parts = []
            ttfb = None
            first_token_time = None
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_str = line_text[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    if first_token_time is None:
                                        first_token_time = time.time()
                                        ttfb = first_token_time - start_time
                                    content_parts.append(delta['content'])
                        except json.JSONDecodeError:
                            continue
            
            total_latency = time.time() - start_time
            content = ''.join(content_parts)
            
            return {
                "content": content,
                "latency": total_latency,
                "ttfb": ttfb if ttfb is not None else total_latency,
                "tokens": {},
                "model": self.name
            }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}",
                "latency": time.time() - start_time if 'start_time' in locals() else 0
            }


def create_model_client(model_key: str, config: Dict) -> Optional[ModelClient]:
    """根据配置创建对应的模型客户端"""
    provider = config.get("provider", "")
    
    client_map = {
        "dashscope": QwenClient,
        "openai_compatible": DeepSeekClient,  # DeepSeek和Doubao都使用这个
        "zhipu": GLMClient,
        "baidu": ErnieClient,
    }
    
    # 特殊处理：根据api_base判断是DeepSeek、Doubao还是Kimi
    if provider == "openai_compatible":
        api_base = config.get("api_base", "")
        if "deepseek" in api_base:
            return DeepSeekClient(config)
        elif "volces" in api_base or "doubao" in api_base:
            return DoubaoClient(config)
        elif "moonshot" in api_base:
            return DeepSeekClient(config)  # Kimi使用OpenAI兼容格式，复用DeepSeekClient
        else:
            return DeepSeekClient(config)  # 默认使用DeepSeek格式
    
    client_class = client_map.get(provider)
    if client_class:
        return client_class(config)
    
    print(f"⚠️  不支持的provider: {provider}")
    return None

