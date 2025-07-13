import ast
import http.client
import json
from urllib.parse import urlencode

from ObjTool import print_dict
from PicRequest import PicRequest


class WenXinAgent(PicRequest):

    assist_url = 'agentapi.baidu.com'

    headers = {
        "Content-Type": "application/json",
    }

    req_id = 0

    def __init__(self, app_id, key):
        super().__init__()

        self.query_params = {
            "appId": app_id,
            'secretKey': key
        }


    def req_pic(self, promt_strs):
        self.conn = http.client.HTTPSConnection(self.assist_url, timeout=120)

        query_string = urlencode(self.query_params)

        WenXinAgent.req_id += 1

        payload = {
           'from':'openapi',
           'openId':str(self.req_id),
           'message':{
               'content':{
                   'type':'text',
                   'value':{
                       "showText": promt_strs
                   }
               }
           }
        }

        payload = json.dumps(payload)

        self.conn.request(
            "POST", f"/assistant/getAnswer?{query_string}", payload, self.headers, encode_chunked=True
        )

        res = self.conn.getresponse()

        while chunk := res.readline():
            if chunk == b'client closed':
                return []

            result = json.loads(chunk.decode("utf-8"))

            if result['status'] == 0 and result.get('data'):
                url_data = result['data']['content'][0]['data']

                if url_data == '':
                    return []

                if url_data[0] == '[':
                    return ast.literal_eval(url_data)
                else:
                    return [url_data]
            else:
                return []

        return []