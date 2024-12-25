import html
import re
import time

from cte import CfTmpEmailOperator


def extract_valid_address(text, pattern):
    text = html.unescape(text)
    # 修改正则表达式以完整匹配包含csrf的URL
    match = re.search(
        pattern, text
    )
    if match:
        verification_link = match.group(0)
        return verification_link
    return None


def get_xai_valid_address(cte_op: CfTmpEmailOperator, email_address: str):
    email_list = []
    while len(email_list) < 1:
        email_list = cte_op.admin_manager.fetch_get_emails(
            email_address=email_address,
            keyword="https://accounts.x.ai/verify-email",
            limit=1,
        )
        time.sleep(1)
    target_content = "".join(
        extract_valid_address(
            email_list[0]["detail"]["contents"][0]["content"],
            r"https://accounts\.x\.ai/verify-email\?user-id=[\w-]+&csrf=[\w]+",
        ).split()
    )
    print(f"[Verify Address] {target_content}")
    cte_op.admin_manager.fetch_delete_email(email_list[0]["id"])

    return target_content


def get_genspark_valid_address(cte_op: CfTmpEmailOperator, email_address: str):
    email_list = []
    while len(email_list) < 1:
        email_list = cte_op.admin_manager.fetch_get_emails(
            email_address=email_address,
            keyword="Genspark",
            limit=1,
        )
        time.sleep(1)
    target_content = "".join(
        extract_valid_address(
            email_list[0]["detail"]["contents"][0]["content"],
            r"Your code is: \s*(\d+)\s*",
        ).split()
    )
    print(f"[Verify Code] {target_content}")
    cte_op.admin_manager.fetch_delete_email(email_list[0]["id"])

    return target_content


if __name__ == "__main__":
    cf_tmp_eo = CfTmpEmailOperator(
        "https://api.mail.com/",
        admin_password="changeme",
        custom_password="changeme",
    )
    # 获取验证链接
    verify_xai_email_address = get_xai_valid_address(cf_tmp_eo, "tmp_xai001@email.com")
    verify_genspark_email_code = get_genspark_valid_address(cf_tmp_eo, "tmp_genspark001@email.com")
