from app.repositories.user import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo