import json

import requests


def parse_sse_line(line):
    """解析 SSE 事件行"""
    result = {'type': '', 'data': ''}

    # 注释行 (以冒号开头)
    if line.startswith(':'):
        result['type'] = 'comment'
        result['data'] = line[1:].strip()
        return result

    # 数据行
    if ':' in line:
        field, value = line.split(':', 1)
        value = value.strip()
    else:
        field, value = line, ''

    # 处理不同字段类型
    if field == 'event':
        result['type'] = 'event'
        result['event'] = value  # 事件类型
    elif field == 'data':
        result['type'] = 'event'
        result['data'] = value
    elif field == 'id':
        result['id'] = value
    elif field == 'retry':
        try:
            result['retry'] = int(value)
        except:
            pass

    return result

class SSEClient:

    def __init__(self, url, data, head):
        self.url = url
        self.data = data
        self.head = head


    def process_sse_stream(self):
        """处理 SSE 流事件"""

        event_data = []
        try:
            # 使用流模式请求
            with requests.post(self.url, data=self.data, headers=self.head, stream=True) as response:
                response.raise_for_status()  # 检查 HTTP 错误

                # 按行迭代流内容
                for line in response.iter_lines():
                    if line:  # 过滤空行
                        decoded_line = line.decode('utf-8')
                        event = parse_sse_line(decoded_line)

                        if event['type'] == 'event' and event['data']:
                            obj = json.loads(event['data'])
                            event_data.append(obj)

                        elif event['type'] == 'comment':
                            print(f"注释: {event['data']}")

        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")

        return event_data