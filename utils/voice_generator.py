import requests
import os
from typing import Optional, Dict, Any
from urllib.parse import urljoin

class VoiceGenerator:
    def __init__(
        self,
        access_token: str,
        model_name: str = "鸣潮",
        speaker_name: str = "折枝",
        base_url: str = "https://gsv.ai-lab.top"
    ):
        """
        初始化语音生成器
        :param access_token: API访问令牌
        :param model_name: 模型名称，默认为"鸣潮"
        :param speaker_name: 说话人名称，默认为"折枝"
        :param base_url: API基础URL
        """
        self.access_token = access_token
        self.model_name = model_name
        self.speaker_name = speaker_name
        self.base_url = base_url
        self.api_endpoint = urljoin(base_url, "/infer_single")
        self.headers = {
            "authority": "gsv.ai-lab.top",
            "priority": "u=1, i",
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "content-type": "application/json"
        }

    def generate_voice(
        self,
        text: str,
        emotion: str = "难过_sad",
        prompt_text_lang: str = "中文",
        text_lang: str = "中文",
        media_type: str = "aac",
        speed_factor: float = 1.0,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        生成语音
        :param text: 要转换的文本内容
        :param emotion: 情感参数，默认为"难过_sad"
        :param prompt_text_lang: 提示文本语言，默认为"中文"
        :param text_lang: 文本语言，默认为"中文"
        :param media_type: 媒体类型，默认为aac
        :param speed_factor: 语速因子，默认为1.0
        :param kwargs: 其他可选参数
        :return: 包含音频URL的字典（失败返回None）
        """
        payload = {
            "access_token": self.access_token,
            "model_name": self.model_name,
            "speaker_name": self.speaker_name,
            "prompt_text_lang": prompt_text_lang,
            "emotion": emotion,
            "text": text,
            "text_lang": text_lang,
            "media_type": media_type,
            "speed_facter": speed_factor,
            **kwargs
        }

        try:
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if result.get("msg") != "推理成功!" or not result.get("audio_url"):
                print(f"API Error: {result.get('msg', 'Unknown error')}")
                return None

            return result

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return None
        except json.JSONDecodeError:
            print("Failed to parse JSON response")
            return None

    def download_audio(
        self,
        audio_url: str,
        save_path: str = "output.aac",
        overwrite: bool = False
    ) -> bool:
        """
        下载音频文件
        :param audio_url: 音频文件URL
        :param save_path: 保存路径
        :param overwrite: 是否覆盖已存在文件
        :return: 是否下载成功
        """
        if os.path.exists(save_path) and not overwrite:
            print(f"File already exists: {save_path}")
            return False

        try:
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True

        except requests.exceptions.RequestException as e:
            print(f"Download failed: {str(e)}")
            return False
        except IOError as e:
            print(f"File save failed: {str(e)}")
            return False

# 使用示例
if __name__ == "__main__":
    # 初始化生成器
    generator = VoiceGenerator(
        access_token="17cfd2378d92f78cd377557205d11262",
        model_name="鸣潮",
        speaker_name="折枝"
    )

    # 生成语音并获取URL
    result = generator.generate_voice(
        text="你昨晚去哪里了",
        emotion="难过_sad",
        text_lang="中文"
    )

    if result:
        print(f"Generation successful! Audio URL: {result['audio_url']}")
        
        # 下载音频文件
        download_success = generator.download_audio(
            audio_url=result["audio_url"],
            save_path="output.aac"
        )
        
        if download_success:
            print("Audio downloaded successfully")
        else:
            print("Failed to download audio")
    else:
        print("Failed to generate voice")