import os

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import LoginFailed


class SimpleAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        admin_user = os.getenv("ADMIN_USER", "admin")
        admin_pass = os.getenv("ADMIN_PASS", "changeme")
        if username == admin_user and password == admin_pass:
            request.session.update({"username": username})
            return response
        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request: Request) -> bool:
        return bool(request.session.get("username"))

    def get_admin_config(self, request: Request) -> AdminConfig:
        return AdminConfig(app_title="James Brannon CMS")

    def get_admin_user(self, request: Request) -> AdminUser:
        return AdminUser(username=request.session.get("username", ""))

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
