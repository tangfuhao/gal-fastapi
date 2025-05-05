import os
import json
import time
import hashlib
import base64
import requests
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from config import get_settings
import httpx
import asyncio
from utils.ali_upload import upload_from_url
import logging
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)

url_pre = "https://cn.tensorart.net"
app_id = "PUCMSW6Tt"
url_workflow = "/v1/workflows"
url_job = "/v1/jobs"
url_resource = "/v1/resource"

private_key_str = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCujbS8Sujiq7WL
klV696kIUTp/0Af9fklL473C4Hd0eKsLP76BqD8AYy2RBEL8msQT6r/ajVZG3PY4
zfdUs4sqMxuJz8BcsSpDY81j0cZxHS067o3ZmqHdS7TwZuARQ3yx1lkWLk74ju3p
LddCLzXb+akZx8ZJN8KcwSJlmC3ST2Vd0zwrt8lwtdeYB7Su5QIyHsAWsv9ZjE+2
FeYva9yYHhMwLzIp4CUt7yKtaou+VIhRs8DzvmQ+tb4sg6jpTPDN9PZcYfHVgv1M
kf7DxZctDI1kfBsT6idmBKf6NUorbI3iqaJ6BuU6XX0pU0rvo9PB2G7DTbObJLtB
CJomWjPnAgMBAAECggEAL6rhBV6LlIMBs9jFYSxKy8uq5wZ/eBlJmODbjGFSHctq
IktJEg1JDykGY4i/Zk45Z5r+w4c/XWCwGLkeZtIVGfQU/CBwzp9PBFI335+EypUG
KgbFU/xnYZBwHApr/Crq3YHEmEsTI8ucasYq95b+5VCbfj/RBWOl0LrpUscpFDpI
zxq0A5Oxv0Bc/C8dePajv65CKk6Bgmi47zGfhG/oU87fpiRFLPglhOMhNZbBlyQy
SSU/UXccGYx2Tqo8iyxzaB9Y7uDsRAArdlWTi2hE8z4XlDeKBSF2s/jFZBVw4JXy
Bm6LYGv7LRo8rPsU6n5nugok1R31QCGBOBp8Uk0LMQKBgQDb/77bOZDEIkv7Txph
aXEgLAyFcuYWzacWI6PaEscEXiCRzBQF74MsqGYjHrIJ8gWiN65C4LxVhUAEECc6
am4MNVpnM6WuO6G3ZcKc8kfyFIliDh6kVDhCcl8pc6aqX2N7cTilGRcU+T63L6aO
zx3Ue5QOcclFSPK/Tsw5eHQLzwKBgQDLHiW6U/tufCReL8dwTrSvObHLD1uCIWme
VMXNQklCT0Ht+Rk5DiiyXBKaIZ/CJ1BSuM2oNC/3K6fSaV3NRL0vK1pN9Tp+1dnJ
EA/+zkZpaW4PHGroA1/2hnTplFHuvaXoT+7eS+BFTaxbtQwaAsCGukoOic6MpPn2
42DN1jPkaQKBgAydd6Y+gMyeYtkASjT3xOLhY75rPkJkfIZKeOTSWtMnSprRpvxI
Ja9z4Jd29SKY3DXXF4kCNgp5X5hcDMPOwoy0qoBsd72r8bQAg85YHkQFZXNX9+3Y
XnmA8XABD7eJTL0RWvwsmiQ7vprmgpiBy+YZR/4kDDSK4FCUBiXtgEoFAoGBAKD/
nXIK3XIe7ojFoHURvcBin93Pp34HU/uPQFZJY14vCphBaU/DPFjcCFaprkMr/EwF
deYMr7Rgox5yLErnYHmCCItghORCR+VKWRNkl4U4b2eE4+xRuH/k5ci7qxHsuxPg
P/tt8y+buLHcWOJJKifgg5DwhIsQvZ2Hb5TYY7t5AoGAPl783kwRSuMs785OuDSI
ckV+9WmCJMFDV0M05hOINV9tB7/R7/ZofQ8gq6AYr5Itnd9T9cHPPtvU9A8yDXgX
wpfRVrix0lZw2S717FtRBUFluAm72hKazrhFWl4/XQ/gH0BJ9rn+Da2k00+noe99
I3mJQzPjdIUInPw+Fk7QLUY=
-----END PRIVATE KEY-----"""


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    max_requests: int = 5  # 每个时间窗口内的最大请求数
    time_window: int = 10  # 时间窗口（秒）

class ImageText2ImageTool:
    """
    文生图工具类，基于 TensorArt/TAMS API。
    配置项通过 config.get_settings() 获取。
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        """初始化文生图工具"""
        self._client = httpx.AsyncClient(timeout=60.0)
        self.rate_limit = RateLimitConfig()
        self._request_times = deque(maxlen=self.rate_limit.max_requests)
    
    @classmethod
    async def get_instance(cls) -> "ImageText2ImageTool":
        """获取 ImageText2ImageTool 的单例实例"""
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance
    
    async def _check_rate_limit(self) -> None:
        """检查并等待速率限制"""
        now = datetime.now()
        
        # 清理过期的请求记录
        while self._request_times and \
              (now - self._request_times[0]) > timedelta(seconds=self.rate_limit.time_window):
            self._request_times.popleft()
        
        # 如果请求数达到限制，等待到最早的请求过期
        if len(self._request_times) >= self.rate_limit.max_requests:
            wait_time = (self._request_times[0] + 
                        timedelta(seconds=self.rate_limit.time_window) - now).total_seconds()
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting for {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # 记录新的请求时间
        self._request_times.append(now)
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self._client.aclose()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    def generate_signature(self, method, url, body, app_id, private_key_str):
        method_str = method.upper()
        url_str = url
        timestamp = str(int(time.time()))
        nonce_str = hashlib.md5(timestamp.encode()).hexdigest()
        body_str = body
        to_sign = f"{method_str}\n{url_str}\n{timestamp}\n{nonce_str}\n{body_str}"
        private_key = serialization.load_pem_private_key(
            private_key_str.encode(), password=None, backend=default_backend()
        )
        signature = private_key.sign(to_sign.encode(), padding.PKCS1v15(), hashes.SHA256())
        signature_base64 = base64.b64encode(signature).decode()
        auth_header = f"TAMS-SHA256-RSA app_id={app_id},nonce_str={nonce_str},timestamp={timestamp},signature={signature_base64}"
        return auth_header

    async def async_get_job_result(
        self, job_id: str, poll_interval: float = 1.0, timeout: float = 120.0,
        max_retries: int = 3, retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        异步轮询获取任务结果，直到成功或失败或超时。
        
        Args:
            job_id: 任务ID
            poll_interval: 轮询间隔（秒）
            timeout: 超时时间（秒）
            max_retries: 单次请求的最大重试次数
            retry_delay: 重试间隔（秒）
            
        Returns:
            Dict[str, Any]: 任务结果
            
        Raises:
            TimeoutError: 整体超时
            Exception: 其他不可恢复的错误
        """
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                await asyncio.sleep(poll_interval)
                
                # 带重试的请求逻辑
                for retry in range(max_retries):
                    try:
                        headers = {
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                            "Authorization": self.generate_signature(
                                "GET", f"{url_job}/{job_id}", "", app_id, private_key_str
                            ),
                        }
                        response = await client.get(
                            f"{url_pre}{url_job}/{job_id}",
                            headers=headers,
                            timeout=10.0  # 设置单次请求超时
                        )
                        response.raise_for_status()
                        data = response.json()
                        
                        if "job" in data:
                            job = data["job"]
                            status = job.get("status")
                            if status == "SUCCESS" or status == "FAILED":
                                return job
                            # 如果状态是进行中，跳出重试循环，继续下一次轮询
                            break
                            
                    except (httpx.ConnectTimeout, httpx.ReadTimeout,
                            httpx.ConnectError, httpx.NetworkError) as e:
                        # 网络相关错误，可以重试
                        if retry < max_retries - 1:
                            logger.warning(f"Request failed (attempt {retry + 1}/{max_retries}): {str(e)}")
                            await asyncio.sleep(retry_delay)
                            continue
                        # 如果是最后一次重试，记录错误但不抛出异常
                        logger.error(f"All retries failed for request: {str(e)}")
                        
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code in {502, 503, 504}:  # 服务器临时错误
                            if retry < max_retries - 1:
                                logger.warning(f"Server error (attempt {retry + 1}/{max_retries}): {str(e)}")
                                await asyncio.sleep(retry_delay)
                                continue
                        # 其他 HTTP 错误或最后一次重试失败，记录错误但继续轮询
                        logger.error(f"HTTP error: {str(e)}")
                        
                    except Exception as e:
                        # 其他意外错误，记录但继续轮询
                        logger.error(f"Unexpected error while polling: {str(e)}")
                        
            # 只有整体超时才抛出异常
            raise TimeoutError(f"Job {job_id} did not finish in {timeout} seconds.")

    async def async_text2img(
        self,
        prompt: str,
        width: int = 768,
        height: int = 1280,
        steps: int = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        异步调用文生图接口，直接返回生成结果。

        Args:
            prompt (str): 提示词
            width (int): 图像宽度
            height (int): 图像高度
            steps (int): 生成步数
            **kwargs: 其他参数，包括：
                - negativePrompts: 负面提示词列表
                - sdModel: 模型ID
                - sdVae: VAE模型
                - sampler: 采样器
                - cfgScale: CFG比例
                - poll_interval: 轮询间隔（秒）
                - timeout: 超时时间（秒）
                - upload_to_oss: 是否上传到OSS（默认False）
                - oss_type: OSS存储类型（如"character", "background"等）

        Returns:
            Dict[str, Any]: 生成结果，包含图像URL等信息。如果上传到OSS，还会包含OSS URL。

        Raises:
            httpx.HTTPError: HTTP请求错误
            TimeoutError: 任务超时
            Exception: 其他错误
        """
        settings = get_settings()

        # 检查速率限制
        await self._check_rate_limit()

        # 创建异步HTTP客户端
        async with httpx.AsyncClient() as client:
            # 准备请求数据
            request_id = hashlib.md5(f"{int(time.time())}_{prompt}".encode()).hexdigest()
            print(f"Request ID: {request_id}")
            txt2img_data = {
                "request_id": request_id,
                "stages": [
                    {
                        "type": "INPUT_INITIALIZE",
                        "inputInitialize": {"seed": -1, "count": 1},
                    },
                    {
                        "type": "DIFFUSION",
                        "diffusion": {
                            "width": width,
                            "height": height,
                            "prompts": [{"text": f"'{prompt}'"}],
                            "negativePrompts": [{}],
                            "sdModel": "757279507095956705",
                            "sdVae": "ae.sft",
                            "sampler": "euler",
                            "steps": 25,
                            "cfgScale": 7,
                            "clipSkip": 2,
                            "embedding": {},
                            "scheduleName": "beta",
                            "guidance": 3.5,
                        },
                    },
                ],
            }
            body = json.dumps(txt2img_data)
            auth_header = self.generate_signature("POST", url_job, body, app_id, private_key_str)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": auth_header,
            }

            # 发起任务创建请求
            response = await client.post(
                f"{url_pre}{url_job}", 
                content=body,
                headers=headers
            )
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            response.raise_for_status()
            result = response.json()

            # 检查任务是否创建成功
            if "job" not in result or "id" not in result["job"]:
                raise Exception(f"Failed to create image generation job: {result}")

            # 获取任务结果
            job_id = result["job"]["id"]
            get_job_result = await self.async_get_job_result(
                job_id,
                poll_interval=kwargs.get(
                    "poll_interval", settings.IMAGE_DEFAULT_POLL_INTERVAL
                ),
                timeout=kwargs.get("timeout", settings.IMAGE_DEFAULT_TIMEOUT),
            )

            # 如果需要上传到OSS
            if (
                kwargs.get("upload_to_oss")
                and get_job_result["status"] == "SUCCESS"
            ):
                image_url = get_job_result["successInfo"]["images"][0]["url"]
                oss_type = kwargs.get("oss_type", "image")
                success = await upload_from_url(image_url, oss_type)
                if success:
                    # 构建OSS URL
                    filename = image_url.split("/")[-1].split("?")[0]
                    oss_path = f"gal-test/{oss_type}/{filename}"
                    oss_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '')}/{oss_path}"
                    # 添加OSS URL到结果中
                    result["oss_url"] = oss_url

            return result


# 用法示例（建议放到 test 或 main 里）
# from utils.image_tool import ImageText2ImageTool
# tool = ImageText2ImageTool()
# resp = tool.text2img(prompt="1girl, amber eyes")
# job_id = resp.get("job", {}).get("id")
# if job_id:
#     import asyncio
#     result = asyncio.run(tool.async_get_job_result(job_id))
#     print(result)
