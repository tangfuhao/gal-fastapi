from fastapi import APIRouter, Depends, HTTPException, Response, Request
from authlib.integrations.starlette_client import OAuth
from bson import ObjectId
from schemas.auth import UserResponseSchema, AuthStatusResponseSchema
from models.user import DBUser
from models.credits import DBCredits
from constant.credits import INITIAL_CREDITS
from fastapi.responses import RedirectResponse
from repositories.base_repository import BaseRepository
from core.container import get_user_repository, get_credits_repository
from config import get_settings

settings = get_settings()

# 配置 OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

@auth_router.get("/me", response_model=AuthStatusResponseSchema)
async def get_auth_status(
    request: Request,
    user_repo: BaseRepository[DBUser] = Depends(get_user_repository)
):
    try:
        # 从请求的 cookies 获取用户ID
        user_id = request.cookies.get("user_id")
        if not user_id:
            return AuthStatusResponseSchema(isLoggedIn=False)
        
        users = await user_repo.find_many({"_id": ObjectId(user_id)})
        if not users:
            return AuthStatusResponseSchema(isLoggedIn=False)
        
        user = users[0]
        return AuthStatusResponseSchema(
            isLoggedIn=True,
            user=UserResponseSchema.from_db_user(user)
        )
    except Exception as e:
        return AuthStatusResponseSchema(isLoggedIn=False)

@auth_router.get("/google")
async def google_login(
    request: Request,
    redirect_to: str = "/"  
):
    """启动 Google OAuth 登录流程"""
    try:
        # 回调到后端接口，并传递编码后的重定向URL
        callback_uri = f"{settings.BACKEND_URL}/api/auth/google/callback"
        return await oauth.google.authorize_redirect(request, callback_uri)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Google OAuth flow: {str(e)}"
        )

@auth_router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    user_repo: BaseRepository[DBUser] = Depends(get_user_repository),
    credits_repo: BaseRepository[DBCredits] = Depends(get_credits_repository)
):
    try:
        # Get token and user info from Google
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get('userinfo')
        
        if not userinfo:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        # Find or create user
        users = await user_repo.find_many({"google_id": userinfo["sub"]})
        user = None
        
        if not users:
            # Create new user
            new_user = DBUser(
                google_id=userinfo["sub"],
                name=userinfo["name"],
                email=userinfo["email"],
                avatar=userinfo.get("picture", "")
            )
            user = await user_repo.create(new_user)
            if not user:
                raise HTTPException(status_code=500, detail="Failed to create user")

            # 为新用户创建初始积分
            initial_credits = DBCredits(
                user_id=user.id,
                amount=INITIAL_CREDITS
            )
            await credits_repo.create(initial_credits)
        else:
            # Update existing user
            user = users[0]
            await user_repo.update(user.id, {
                "name": userinfo["name"],
                "email": userinfo["email"],
                "avatar": userinfo.get("picture", "")
            })
        
        # 创建重定向响应
        redirect = RedirectResponse(url=f"{settings.FRONTEND_URL}")
        
        # 设置 cookie
        frontend_url = settings.FRONTEND_URL
        domain = frontend_url.split("://")[1].split(":")[0]  # 提取域名部分
        is_localhost = domain in ["localhost", "127.0.0.1"]
        
        # 打印调试信息
        print(f"Frontend URL: {frontend_url}")
        print(f"Extracted domain: {domain}")
        print(f"Is localhost: {is_localhost}")
        
        cookie_domain = None if is_localhost else domain
        print(f"Setting cookie with domain: {cookie_domain}")
        
        redirect.set_cookie(
            key="user_id",
            value=str(user.id),
            domain=cookie_domain,
            httponly=True,
            secure=not is_localhost,  # localhost 不使用 secure
            samesite="lax",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        # 打印响应头部信息
        print(f"Response headers: {dict(redirect.headers)}")
        
        return redirect
        
    except Exception as e:
        # 重定向到前端错误页面
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error={str(e)}"
        )

@auth_router.post("/logout")
async def logout(response: Response):
    """用户登出"""
    response.delete_cookie(key="user_id")
    return {"status": "success"}