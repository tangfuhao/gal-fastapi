import requests
import json
import hashlib
import time

import base64
import hashlib
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding

url_pre = "https://cn.tensorart.net"
app_id = "PUCMSW6Tt"

# u can put ur private key under the root directory
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


url_workflow = "/v1/workflows"
url_job = "/v1/jobs"
url_resource = "/v1/resource"


def generate_signature(method, url, body, app_id, private_key_str):
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


txt2img_data = {
    "request_id": hashlib.md5(str(int(time.time())).encode()).hexdigest(),
    "stages": [
        {"type": "INPUT_INITIALIZE", "inputInitialize": {"seed": -1, "count": 1}},
        {
            "type": "DIFFUSION",
            "diffusion": {
                "width": 768,
                "height": 1280,
                "prompts": [
                    {
                        "text": """'Dominic Russo full-body portrait, #000000 hair, #2B3A55 eyes, tailored black suit with blood-red tie, piercing gaze with half-smile, chiaroscuro lighting, anime style, clean lines, --no background --v 5.2'"""
                    }
                ],
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


def get_job_credits():
    body = json.dumps(txt2img_data)
    response = requests.post(
        f"{url_pre}{url_job}/credits",
        json=txt2img_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": generate_signature(
                "POST", f"{url_job}/credits", body, app_id, private_key_str
            ),
        },
    )
    print(response.text)


# 文生图
def text2img():
    response_data = create_job(txt2img_data)
    if "job" in response_data:
        job_dict = response_data["job"]
        job_id = job_dict.get("id")
        job_status = job_dict.get("status")
        print(job_id, job_status)
        get_job_result(job_id)


# 图生图
# def img2img(img_path):
#     resource_id = upload_img(img_path)
#     data = {
#         "request_id": hashlib.md5(str(int(time.time())).encode()).hexdigest(),
#         "stages": [
#             {
#                 "type": "INPUT_INITIALIZE",
#                 "inputInitialize": {"image_resource_id": f"{resource_id}", "count": 1},
#             },
#             {
#                 "type": "DIFFUSION",
#                 "diffusion": {
#                     "width": 512,
#                     "height": 512,
#                     "prompts": [{"text": "1girl"}],
#                     "sampler": "DPM++ 2M Karras",
#                     "sdVae": "Automatic",
#                     "steps": 15,
#                     "sd_model": "600423083519508503",
#                     "clip_skip": 2,
#                     "cfg_scale": 7,
#                 },
#             },
#         ],
#     }
#     response_data = create_job(data)
#     if "job" in response_data:
#         job_dict = response_data["job"]
#         job_id = job_dict.get("id")
#         job_status = job_dict.get("status")
#         print(job_id, job_status)
#         get_job_result(job_id)


def get_job_result(job_id, max_retries=3, retry_delay=2):
    retries = 0
    while True:
        try:
            time.sleep(1)
            response = requests.get(
                f"{url_pre}{url_job}/{job_id}",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": generate_signature(
                        "GET", f"{url_job}/{job_id}", "", app_id, private_key_str
                    ),
                },
                timeout=10  # 添加超时设置
            )
            response.raise_for_status()  # 检查HTTP错误
            get_job_response_data = json.loads(response.text)
            
            if "job" in get_job_response_data:
                job_dict = get_job_response_data["job"]
                job_status = job_dict.get("status")
                if job_status == "SUCCESS":
                    print(job_dict)
                    return job_dict
                elif job_status == "FAILED":
                    print(job_dict)
                    return job_dict
                else:
                    print(job_dict)
                    retries = 0  # 重置重试次数，因为成功获取到了响应
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            retries += 1
            if retries >= max_retries:
                print(f"Error after {max_retries} retries: {str(e)}")
                return None
            print(f"Retry {retries}/{max_retries} after error: {str(e)}")
            time.sleep(retry_delay * retries)  # 指数退避重试


def create_job(data):
    body = json.dumps(data)
    auth_header = generate_signature("POST", url_job, body, app_id, private_key_str)
    response = requests.post(
        f"{url_pre}{url_job}",
        json=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": auth_header,
        },
    )
    print(response.text)
    return json.loads(response.text)


def upload_img(img_path):
    print(img_path)
    data = {
        "expireSec": 3600,
    }
    body = json.dumps(data)
    response = requests.post(
        f"{url_pre}{url_resource}/image",
        json=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": generate_signature(
                "POST", f"{url_resource}/image", body, app_id, private_key_str
            ),
        },
    )
    print(response.text)
    response_data = json.loads(response.text)
    resource_id = response_data["resourceId"]
    put_url = response_data["putUrl"]
    headers = response_data["headers"]
    with open(img_path, "rb") as f:
        res = f.read()
        response = requests.put(put_url, data=res, headers=headers)
        print(response.text)
    return resource_id


def get_workflow_template(template_id):
    response = requests.get(
        f"{url_pre}{url_workflow}/{template_id}",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": generate_signature(
                "GET", f"{url_workflow}/{template_id}", "", app_id, private_key_str
            ),
        },
    )
    print(response.text)


def workflow_template_check():
    data = {
        "templateId": "676018193025756628",
        "fields": {
            "fieldAttrs": [
                {"nodeId": "25", "fieldName": "image", "fieldValue": None},
                {"nodeId": "27", "fieldName": "text", "fieldValue": "1 girl"},
            ]
        },
    }
    body = json.dumps(data)
    response = requests.post(
        f"{url_pre}{url_workflow}/template/check",
        json=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": generate_signature(
                "POST", f"{url_workflow}/template/check", body, app_id, private_key_str
            ),
        },
    )
    print(response.text)


def workflow_template_job():
    data = {
        "request_id": "9f2bf085998e76acd5c8bc306a4f034f",
        "templateId": "676018193025756628",
        "fields": {
            "fieldAttrs": [
                {
                    "nodeId": "25",
                    "fieldName": "image",
                    "fieldValue": "f29036b4-ff7b-4394-8c26-aabc1bdae008",
                },
                {
                    "nodeId": "27",
                    "fieldName": "text",
                    "fieldValue": "1 girl, amber_eyes",
                },
            ]
        },
    }

    body = json.dumps(data)
    response = requests.post(
        f"{url_pre}{url_job}/workflow/template",
        json=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": generate_signature(
                "POST", f"{url_job}/workflow/template", body, app_id, private_key_str
            ),
        },
    )
    print(response.text)
    response_data = json.loads(response.text)
    if "job" in response_data:
        job_dict = response_data["job"]
        job_id = job_dict.get("id")
        job_status = job_dict.get("status")
        print(job_id, job_status)
        get_job_result(job_id)


def get_model(id):
    response = requests.get(
        f"{url_pre}/v1/models/{id}",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": generate_signature(
                "GET", f"/v1/models/{id}", "", app_id, private_key_str
            ),
        },
    )
    print(response.text)


if __name__ == "__main__":
    get_model(757279507095956705)
    # 算力预估
    get_job_credits()

    # 文生图
    text2img()
    # 图生图
    # img2img("../test.webp")

    # 模版相关
    # get_workflow_template(676018193025756628)
    # workflow_template_check()
    # workflow_template_job()
