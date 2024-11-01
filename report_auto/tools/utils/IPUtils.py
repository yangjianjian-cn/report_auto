__coding__ = "utf-8"


def get_client_ip(request):
    # 尝试从 X-Forwarded-For 头部获取客户端IP地址
    if 'X-Forwarded-For' in request.headers:
        # X-Forwarded-For 可能包含多个IP地址，它们之间用逗号分隔
        # 第一个IP地址通常是客户端的真实IP地址
        client_ip: str = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        # 如果没有 X-Forwarded-For 头部，则使用远程地址
        client_ip: str = request.remote_addr
    client_ip: str = client_ip.replace(".", "")
    return client_ip
