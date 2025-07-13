import ast
import http.client
import json
import uuid
from http.client import responses

import requests
from PicRequest import PicRequest
from SSEClient import SSEClient


class TengXunAgent(PicRequest):
    req_id = 0

    url = 'https://wss.lke.cloud.tencent.com/v1/qbot/chat/sse'

    headers = {
        "Content-Type": "application/json",
    }

    base_data = {
        "incremental": True,
        "streaming_throttle": 10,
        "visitor_labels": [],
        "custom_variables": {},
        "search_network": "disable",
        "stream": "disable",
        "workflow_status": "enable"
    }

    def __init__(self, app_key):
        super().__init__()

        self.base_data['bot_app_key'] = app_key

    def req_pic(self, promt_strs):

        data = self.base_data.copy()
        prom_list = []
        prom_list.append(promt_strs)

        prompt_list = json.dumps(prom_list, ensure_ascii=False)
        TengXunAgent.req_id = uuid.uuid4()

        data['request_id'] = str(TengXunAgent.req_id)
        data['session_id'] = str(TengXunAgent.req_id)
        data['visitor_biz_id'] = str(TengXunAgent.req_id)
        data['content'] = prompt_list

        payload = json.dumps(data)

        sse_client = SSEClient(self.url, payload, self.headers)
        event_list = sse_client.process_sse_stream()

        url_list = []

        for event in event_list:
            if event['type'] == 'reply':
                # 17 工作流结束
                if event['payload']['reply_method'] == 17:

                    url_content = json.loads(event['payload']['content'])

                    for content in url_content:
                        url_list.append(content['ouput'])

        return url_list
