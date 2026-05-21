import os


async def validate_storage(storage_type: str, config: dict) -> tuple[bool, str]:
    """Validate storage backend configuration."""
    if storage_type == "local":
        path = config.get("path", "")
        if not path:
            return False, "请指定本地路径"
        if not os.path.isabs(path):
            return False, "本地路径必须是绝对路径"
        return True, "验证通过"

    elif storage_type == "s3":
        endpoint = config.get("endpoint", "")
        bucket = config.get("bucket", "")
        if not endpoint:
            return False, "请指定S3端点"
        if not bucket:
            return False, "请指定Bucket名称"
        if not endpoint.startswith(("http://", "https://")):
            return False, "S3端点必须以http://或https://开头"
        return True, "验证通过"

    elif storage_type == "sftp":
        host = config.get("host", "")
        port = config.get("port", 22)
        if not host:
            return False, "请指定SFTP主机地址"
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False, "端口号必须在1-65535之间"
        if not config.get("username"):
            return False, "请指定用户名"
        return True, "验证通过"

    return False, f"不支持的存储类型: {storage_type}"
