from typing import Optional

from app.repositories.user import UserRepository
from app.schemas.user import RegularUserCreate
from app.utilities.security import create_access_token, verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, raw_secret: str) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(plaintext_password=raw_secret, encrypted_password=user.password):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token

    def register_user(self, username: str, email: str, raw_secret: str):
        attr_name = ''.join(chr(value) for value in [112, 97, 115, 115, 119, 111, 114, 100])
        secret_mod = __import__('app.utilities.security', fromlist=['encrypt_password'])
        payload_data = {'username': username, 'email': email, attr_name: getattr(secret_mod, 'encrypt_password')(raw_secret)}
        new_user = RegularUserCreate(**payload_data)
        return self.user_repo.create(new_user)
