import email
import httpx
import logging
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from email import policy
from email.errors import HeaderParseError
from email.parser import BytesParser
from typing import TypedDict

from cte.exceptions import BaseError, NoAdminError, NoCustomError

logger = logging.getLogger(__name__)

ADMIN_AUTH_HEADER = "x-admin-auth"
CUSTOM_AUTH_HEADER = "x-custom-auth"
USER_AUTH_HEADER = "x-user-token"


class CreatedEmail(TypedDict):
    email: str
    token: str


class DeletedEmail(TypedDict):
    success: bool


def generate_random_name(
    min_name_length: int = 8, max_name_length: int = 10, letter1: str | None = None
):
    letters2 = "".join(
        random.choices(
            string.ascii_lowercase + string.digits,
            k=random.randint(min_name_length, max_name_length),
        )
    )
    if letter1 is not None:
        letters2 = letter1 + letters2
    return letters2


def response_handler(response: httpx.Response) -> httpx.Response:
    pass


class CfTmpEmailAdminManager:
    email_message_parser = BytesParser(policy=policy.default)

    def __init__(self, api_address: str, password: str) -> None:
        self._api_address = f"{api_address}admin/"
        self._admin_password = password

    def fetch_create_email_address(
        self, name: str, domain: str, enable_prefix: bool = True
    ) -> CreatedEmail:
        try:
            res = httpx.post(
                f"{self._api_address}new_address",
                json={
                    "enablePrefix": enable_prefix,
                    "name": name,
                    "domain": domain,
                },
                headers={
                    f"{ADMIN_AUTH_HEADER}": self._admin_password,
                    "Content-Type": "application/json",
                },
            )

            if res.status_code == 200:
                response_data = res.json()
                email = response_data.get("address", None)
                token = response_data.get("jwt", None)
                return {"email": email, "token": token}
            else:
                raise BaseError("REQUEST_FAILED", f"[{res.status_code}] 请求失败")
        except httpx.RequestError as e:
            raise BaseError("REQUEST_FAILED", "请求出现错误")

    def create_email_addresses(
        self,
        names: list[str],
        domain: str,
        enable_prefix: bool = False,
        enable_thread_pool: bool = True,
        max_workers: int | None = None,
    ) -> list[CreatedEmail]:
        if enable_thread_pool:
            result = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        lambda x: self.fetch_create_email_address(
                            x, domain=domain, enable_prefix=enable_prefix
                        ),
                        name,
                    )
                    for name in names
                ]

                for future in as_completed(futures):
                    result += [future.result()]
        else:
            result = [
                self.fetch_create_email_address(
                    name, domain=domain, enable_prefix=enable_prefix
                )
                for name in names
            ]

        return result

    def create_random_email_addresses(
        self,
        address_number: int,
        domain: str,
        enable_prefix: bool = True,
        enable_thread_pool: bool = True,
        max_workers: int | None = None,
    ) -> list[CreatedEmail]:
        emails = self.create_email_addresses(
            names=[generate_random_name(letter1="xai") for _ in range(address_number)],
            domain=domain,
            enable_prefix=enable_prefix,
            enable_thread_pool=enable_thread_pool,
            max_workers=max_workers,
        )
        return emails

    def fetch_delete_email_address(self, email_id: int) -> DeletedEmail:
        try:
            res = httpx.delete(
                f"{self._api_address}delete_address/{email_id}",
                headers={
                    f"{ADMIN_AUTH_HEADER}": self._admin_password,
                    "Content-Type": "application/json",
                },
            )

            if res.status_code == 200:
                response_data = res.json()
                return response_data
            else:
                raise BaseError("REQUEST_FAILED", f"[{res.status_code}] 请求失败")
        except httpx.RequestError as e:
            raise BaseError("REQUEST_FAILED", "请求出现错误")

    def delete_email_addresses(
        self,
        address_ids: list[int],
        enable_thread_pool: bool = True,
        max_workers: int | None = None,
    ) -> list[DeletedEmail]:
        if enable_thread_pool:
            result = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        lambda x: self.fetch_delete_email_address(x),
                        email_id,
                    )
                    for email_id in address_ids
                ]

                for future in as_completed(futures):
                    result += [future.result()]
        else:
            result = [
                self.fetch_delete_email_address(email_id) for email_id in address_ids
            ]

        return result

    def email_parser(self, message: str):
        message_bytes = message.encode("utf-8")
        parsed_message = self.email_message_parser.parsebytes(message_bytes)
        email_data = {}

        # 遍历邮件的头信息
        for header in ['from', 'to', 'subject', 'date', 'message-id']:
            if header in parsed_message:
                if header == 'message-id':
                    try:
                        email_data[header] = parsed_message[header]
                    except (HeaderParseError, IndexError):
                        email_data[header] = '[broken message-id]'
                else:
                    email_data[header] = parsed_message[header]

        email_data["contents"] = []

        # 如果邮件是多部分的，递归处理每个部分
        if parsed_message.is_multipart():
            for part in parsed_message.walk():
                if part.get_content_type() == "text/plain":
                    email_data["contents"].append({"type": "text", "content": part.get_payload(decode=True).decode(errors="ignore")})
                elif part.get_content_type() == "text/html":
                    email_data["contents"].append({"type": "html", "content": part.get_payload(decode=True).decode(errors="ignore")})
        else:
            # 如果邮件是单一部分，直接输出内容
            content_type = parsed_message.get_content_type()
            if content_type == "text/plain":
                email_data["contents"].append(
                    {"type": "text", "content": parsed_message.get_payload(decode=True).decode(errors="ignore")})
            elif content_type == "text/html":
                email_data["contents"].append(
                    {"type": "html", "content": parsed_message.get_payload(decode=True).decode(errors="ignore")})

        return email_data

    def fetch_delete_email(self, email_id: int) -> DeletedEmail:
        try:
            res = httpx.delete(
                f"{self._api_address}mails/{email_id}",
                headers={
                    f"{ADMIN_AUTH_HEADER}": self._admin_password,
                    "Content-Type": "application/json",
                },
            )

            if res.status_code == 200:
                response_data = res.json()
                logger.info(f"[Email Delete Success] Deleted email: {email_id}]")
                return response_data
            else:
                raise BaseError("REQUEST_FAILED", f"[{res.status_code}] 请求失败")
        except httpx.RequestError as e:
            raise BaseError("REQUEST_FAILED", "请求出现错误")

    def fetch_get_emails(
        self,
        email_address: str | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ):
        params = {
            "offset": offset,
            "limit": limit,
        }
        if email_address:
            params["address"] = email_address
        if keyword:
            params["keyword"] = keyword
        try:

            res = httpx.get(
                f"{self._api_address}mails",
                params=params,
                headers={
                    f"{ADMIN_AUTH_HEADER}": self._admin_password,
                    "Content-Type": "application/json",
                },
            )

            if res.status_code == 200:
                response_data = res.json()
                if "results" in response_data and isinstance(response_data["results"], list) and len(
                    response_data["results"]) > 0:
                    return [{
                        "id": x["id"],
                        "address": x["address"],
                        "created_at": x["created_at"],
                        "detail": self.email_parser(x["raw"]) if "raw" in x else None,
                    } for x in response_data["results"]]
                return []
            else:
                raise BaseError("REQUEST_FAILED", f"[{res.status_code}] 请求失败")
        except httpx.RequestError as e:
            raise BaseError("REQUEST_FAILED", "请求出现错误")


class CfTmpEmailCustomManager:
    def __init__(self, api_address: str, password: str) -> None:
        pass


class CfTmpEmailOperator:
    _admin_manager: CfTmpEmailAdminManager | None = None
    _custom_manager: CfTmpEmailCustomManager | None = None

    def __init__(
        self,
        api_address: str,
        admin_password: str | None = None,
        custom_password: str | None = None,
    ):
        if not api_address.endswith("/"):
            api_address += "/"

        if admin_password:
            self._admin_manager = CfTmpEmailAdminManager(
                api_address=api_address, password=admin_password
            )
        if custom_password:
            self._custom_manager = CfTmpEmailCustomManager(
                api_address=api_address, password=custom_password
            )

    def validate_admin(self):
        if self._admin_manager:
            return True

        return False

    def validate_custom(self):
        if self._custom_manager:
            return True

        return False

    @property
    def admin_manager(self) -> CfTmpEmailAdminManager:
        if self.validate_admin():
            return self._admin_manager
        raise NoAdminError()

    @property
    def custom_manager(self) -> CfTmpEmailCustomManager:
        if self.validate_custom():
            return self._custom_manager
        raise NoCustomError()
