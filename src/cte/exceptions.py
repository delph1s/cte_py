class BaseError(Exception):
    def __init__(self, error_type: str, detail: str):
        self.error_type = error_type
        self.detail = detail

    def __str__(self):
        return f"[{self.error_type}] {self.detail}"

    def __repr__(self):
        return f"[{self.error_type}] {self.detail}"


class NoAdminError(BaseError):
    def __init__(self):
        super().__init__("NO_ADMIN", "No admin authorization.")


class NoCustomError(BaseError):
    def __init__(self):
        super().__init__("NO_CUSTOM", "No custom authorization.")
