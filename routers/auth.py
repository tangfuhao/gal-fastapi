from fastapi import APIRouter, Depends, HTTPException, Response, Request, Header
from authlib.integrations.starlette_client import OAuth
from schemas.auth import UserResponseSchema, AuthStatusResponseSchema
from models.user import DBUser
from models.credits import DBCredits
from constant.credits import INITIAL_CREDITS
from fastapi.responses import RedirectResponse, JSONResponse
from repositories.base_repository import BaseRepository
from core.container import get_user_repository, get_credits_repository
from config import get_settings
from utils.jwt import create_access_token
from typing import Optional
from core.auth import get_current_user  

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

@auth_router.get("/google")
async def google_login(request: Request):
    """启动 Google OAuth 登录流程"""
    try:
        # 回调到后端接口
        callback_uri = f"{settings.BACKEND_URL}/api/auth/google/callback"
        return await oauth.google.authorize_redirect(request, callback_uri)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Google OAuth flow: {str(e)}"
        )

@auth_router.get("/me", response_model=AuthStatusResponseSchema)
async def get_auth_status(
    current_user: Optional[DBUser] = Depends(get_current_user)
):
    if not current_user:
        return AuthStatusResponseSchema(isLoggedIn=False)
    
    return AuthStatusResponseSchema(
        isLoggedIn=True,
        user=UserResponseSchema.from_db_user(current_user)
    )

@auth_router.get("/google/callback")
async def google_callback(
    request: Request,
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
        
        # 创建 JWT token
        access_token = create_access_token({"sub": str(user.id)})
        
        # 创建重定向响应到 Next.js 的回调页面
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        # 重定向到前端错误页面
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error={str(e)}"
        )

@auth_router.post("/logout")
async def logout():
    # JWT 不需要服务端登出
    return JSONResponse({"message": "Logged out successfully"})