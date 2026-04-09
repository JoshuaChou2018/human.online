"""
密码处理工具
"""
from passlib.context import CryptContext

# 使用 bcrypt 进行密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # bcrypt 限制密码长度为 72 字节
        password_bytes = plain_password.encode('utf-8')[:72]
        return pwd_context.verify(password_bytes, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # bcrypt 限制密码长度为 72 字节
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)
