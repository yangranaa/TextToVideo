import ast
import http.client
import json

from PicRequest import PicRequest

host = "xingchen-api.xf-yun.com"

class XunFeiAgent(PicRequest):
    req_id = 0

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    base_data = {
        "uid": "19954564624",
        "stream": False
    }

    def __init__(self, api_secret, api_key, flow_id):
        super().__init__()

        self.conn = http.client.HTTPSConnection(host, timeout=120)

        self.headers['Authorization'] = f'Bearer {api_secret}:{api_key}'
        self.base_data['flow_id'] = flow_id


    def req_pic(self, promt_strs):
        data = self.base_data.copy()

        prompt_list = f'["{promt_strs}"]'

        user_input = {"AGENT_USER_INPUT": prompt_list}
        XunFeiAgent.req_id += 1

        data['parameters'] = user_input
        data['uid'] = str(XunFeiAgent.req_id)

        payload = json.dumps(data)

        self.conn.request(
            "POST", "/workflow/v1/chat/completions", payload, self.headers, encode_chunked=True
        )

        res = self.conn.getresponse()


        while chunk := res.readline():
            result = json.loads(chunk.decode("utf-8"))

            if result.get('code') == 0:
                content = result['choices'][0]['delta']['content']

                if content[0] == '[':
                    img_list = ast.literal_eval(content)
                else:
                    img_list = [content]

                return img_list

        return []