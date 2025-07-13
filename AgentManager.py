import ast
import http.client
import json
import threading
import time

from AgentSetingView import AIKeyData
from FileTool import calculate_string_hash
from PicRequest import PicRequest
from TengXunAgent import TengXunAgent
from WenXinAgent import WenXinAgent
from XunFeiAgent import XunFeiAgent
from ZhiPuAI import ZhiPuAI

# class PromtRequest:
#     req_id = 0
#
#     headers = {
#         "Content-Type": "application/json",
#         "Accept": "text/event-stream",
#         "Authorization": "Bearer 1446d3e95446065ce677c021024ecf25:ZGRlY2U3MzczNjg1ODBmYTE5N2M0Zjgw"
#     }
#
#     base_data = {
#         "flow_id": "7329098317796519936",
#         "uid": "19954564624",
#         "stream": False
#     }
#
#     def __init__(self):
#         self.conn = http.client.HTTPSConnection(host, timeout=120)
#
#     def req_promt(self, text):
#         data = self.base_data.copy()
#         user_input = {"AGENT_USER_INPUT": text}
#         self.req_id += 1
#
#         data['parameters'] = user_input
#         data['uid'] = str(self.req_id)
#
#         payload = json.dumps(data)
#
#         self.conn.request(
#             "POST", "/workflow/v1/chat/completions", payload, self.headers, encode_chunked=True
#         )
#
#         res = self.conn.getresponse()
#
#         promt_list = None
#
#         while chunk := res.readline():
#             result = json.loads(chunk.decode("utf-8"))
#
#             print(result)
#
#             # if result['code'] == 0:
#             #     url_list = result['choices'][0]['delta']['content']
#             #     return url_list
#
#         return promt_list

# 可灵 可套用明星脸，低随机，多脸混淆
# 文心质量不行画画2D漫画
# 腾讯慢 2d漫画光影好看 两人以上不会画漫画 3d不认脸
# 智普 只能画3D 不认脸
# ||海螺 即梦要钱


class AgentManager:

    agent_idx = 0

    @classmethod
    def req_gen_pic(cls, promt_strs):

        ai_data = AIKeyData.ai_list[cls.agent_idx]
        keys = ai_data['keys']

        pic_req = None

        if ai_data['type'] == "讯飞":
            pic_req = XunFeiAgent(keys['API Secret'], keys['API Key'], keys['API Flowid'])
        elif ai_data['type'] == "文心":
            pic_req = WenXinAgent(keys['ID'], keys['密钥'])
        elif ai_data['type'] == "腾讯":
            pic_req = TengXunAgent(keys['app_key'])
        elif ai_data['type'] == "智谱":
            pic_req = ZhiPuAI(keys['api_key'])


        if pic_req:
            url_list = pic_req.req_pic(promt_strs)

            return url_list

    # @classmethod
    # def req_promt(cls, text):
    #     promt_req = PromtRequest()
    #     promt_list = promt_req.req_promt(text)
    #
    #     return promt_list
