from PicRequest import PicRequest

import requests
import json


class BuffGPTAgent(PicRequest):
    url = "https://buffgpt.agentsyun.com/api/agents_application/open/v1/execute/task/workflow"

    # 请求头
    headers = {
        "Content-Type": "application/json",
        "API-KEY": "ak-ef6bcd0655a748a39e3866796ef8b8be"
    }
    
    def __init__(self):
        super().__init__()


    def req_pic(self, promt_strs):
        # 请求体
        data = {
            "workflowApplicationId": "110",
            "workflowApplicationUuid": "466bf125-e18d-4a1e-b0ef-4bd5fa08f69b",
            "globalNodeInvokeDTO": {
                "name": "buffgpt",
                "age": 20
            },
            "version": 49,
            "callbackUrl": "回调地址"
        }

        # 发送POST请求
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

        # 输出响应状态码和响应体
        print("Response Status Code:", response.status_code)
        print("Response Body:", response.json())




# bga = BuffGPTAgent()
# bga.req_pic("一只母鸡")