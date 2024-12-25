# Cloudflare Temp Email Python Tool

## 1. Overview

A python tool for [cloudflare temp email](https://github.com/dreamhunter2333/cloudflare_temp_email)

## 2. Document

### Install

Dev:

```bash
poetry add -e /path/to/cte_py
```

Prod:

```bash
poetry add /path/to/cte_py
```

### How to use

按名称批量创建邮箱

```python
from cte import CfTmpEmailOperator

cf_tmp_eo = CfTmpEmailOperator(
    "https://api.mail.com/",
    admin_password="changeme",
    custom_password="changeme",
)
created_email_addresses = cf_tmp_eo.admin_manager.create_email_addresses(
    [f"xai{i:0>3}" for i in range(41, 51)], "email.com", enable_prefix=True
)
print(created_email_addresses)
```

随机创建一定数量的邮箱

```python
created_emails = cf_tmp_eo.admin_manager.create_random_email_addresses(10, "email.com")
```

按 id 批量删除邮箱

```python
cf_tmp_eo.admin_manager.delete_email_addresses([i for i in range(1, 11)])
```

根据搜索条件获取邮件

```python
email_list = cf_tmp_eo.admin_manager.fetch_get_emails(email_address="tmp_xai001@email.com",
                                                      keyword="https://accounts.x.ai/verify-email", limit=1)
```

根据 id 删除邮件

```python
cf_tmp_eo.fetch_delete_email(email_list[0]["id"])
```
