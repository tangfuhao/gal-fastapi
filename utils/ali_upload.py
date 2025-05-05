import oss2
import os
import httpx
from urllib.parse import unquote
import asyncio
from typing import Optional
from config import get_settings

settings = get_settings()
 
# 初始化OSS Bucket
auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)


async def upload_from_url(url: str, type: str, oss_object_path: Optional[str] = None, chunk_size: int = 1024*1024) -> bool:
    """
    通过URL异步上传文件到OSS（支持大文件流式传输）
    :param url: 源文件URL地址
    :param type: 文件类型（用于确定OSS中的存储路径）
    :param oss_object_path: OSS存储路径（可选，默认使用URL文件名）
    :param chunk_size: 分块大小（字节）
    :return: 上传结果
    """
    try:
        # 自动获取文件名（如果未指定OSS路径）
        if not oss_object_path:
            filename = unquote(url.split('/')[-1].split('?')[0])
            oss_object_path = f"gal-test/{type}/{filename}"

        # 异步发起流式请求
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url, timeout=300.0) as response:
                response.raise_for_status()
                
                # 获取文件总大小（可能不存在）
                total_size = int(response.headers.get('content-length', 0))

                # 初始化分片上传（适合大文件）
                upload_id = bucket.init_multipart_upload(oss_object_path).upload_id
                parts = []

                try:
                    # 分块上传
                    part_number = 1
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        # 使用 run_in_executor 在线程池中执行同步的 OSS 上传
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None,
                            bucket.upload_part,
                            oss_object_path,
                            upload_id,
                            part_number,
                            chunk
                        )
                        parts.append(oss2.models.PartInfo(part_number, result.etag))
                        part_number += 1

                        # 显示进度（如果已知文件大小）
                        if total_size > 0:
                            uploaded = min(part_number * chunk_size, total_size)
                            print(f"\r进度: {uploaded/total_size:.1%}", end='')

                    # 完成分片上传
                    await loop.run_in_executor(
                        None,
                        bucket.complete_multipart_upload,
                        oss_object_path,
                        upload_id,
                        parts
                    )
                    print(f"\nURL上传完成：{url} -> {oss_object_path}")
                    return True

                except Exception as inner_e:
                    print(f"\n分片上传失败: {str(inner_e)}")
                    # 中断上传
                    await loop.run_in_executor(
                        None,
                        bucket.abort_multipart_upload,
                        oss_object_path,
                        upload_id
                    )
                    return False

    except Exception as e:
        print(f"\nURL上传失败: {str(e)}")
        return False


if __name__ == '__main__':
    # 示例用法：
    async def main():
        # 大文件分片上传（自动模式）
        await upload_from_url(
            url='https://static001.geekbang.org/resource/image/b9/66/b90f536e47b2949b3831e8486acf3766.png',
            type='image',
        )

    asyncio.run(main())