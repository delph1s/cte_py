from cte import CfTmpEmailOperator
import re


def extract_valid_address(text):
    # 修改正则表达式以完整匹配包含csrf的URL
    match = re.search(r'https://accounts\.x\.ai/verify-email\?user-id=[^&]+&csrf=[^\s]+', text)
    if match:
        verification_link = match.group(0)
        return verification_link
    return None


if __name__ == "__main__":
    cf_tmp_eo = CfTmpEmailOperator(
        "https://api.mail.com/",
        admin_password="changeme",
        custom_password="changeme",
    )
    # 搜索邮件
    email_list = cf_tmp_eo.admin_manager.fetch_get_emails(email_address="tmp_xai001@email.com",
                                                          keyword="https://accounts.x.ai/verify-email", limit=1)
    # 获取目标内容
    target_content = "".join(extract_valid_address(email_list[0]["detail"]["contents"][0]["content"]).split())
    print(target_content)
    # 删除邮件
    cf_tmp_eo.admin_manager.fetch_delete_email(email_list[0]["id"])
