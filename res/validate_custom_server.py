"""在构建前校验内置服务器配置，不输出配置内容。"""

import base64
import binascii
import os
from urllib.parse import urlsplit


def validate(values):
    for name in ("RENDEZVOUS_SERVER", "RELAY_SERVER"):
        value = values.get(name, "")
        if not value and name == "RELAY_SERVER":
            continue
        if not value or value != value.strip() or any(c.isspace() for c in value):
            raise ValueError(f"{name} 必须为非空主机名或 IP，可附带端口")
        parsed = urlsplit("//" + value)
        if not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username is not None or parsed.password is not None:
            raise ValueError(f"{name} 不能包含协议、路径或认证信息")
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError(f"{name} 端口超出范围")
    try:
        key = base64.b64decode(values.get("RS_PUB_KEY", ""), validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("RS_PUB_KEY 必须是有效的 Base64 公钥") from None
    if len(key) != 32:
        raise ValueError("RS_PUB_KEY 必须解码为 32 字节的 Ed25519 公钥")
    api = values.get("API_SERVER", "")
    if api:
        parsed = urlsplit(api)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username is not None or parsed.password is not None or any(c.isspace() for c in api):
            raise ValueError("API_SERVER 必须是无认证信息的 HTTP(S) 地址")


if __name__ == "__main__":
    try:
        validate(os.environ)
    except ValueError:
        raise SystemExit("服务器配置无效，请检查 RENDEZVOUS_SERVER、RS_PUB_KEY、RELAY_SERVER 和 API_SERVER") from None
    print("服务器配置校验通过")
