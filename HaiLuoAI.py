import json

import requests

from PicRequest import PicRequest

class HaiLuoAI(PicRequest):

    url = "https://api.minimaxi.com/v1/image_generation"

    api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLmnajnhLYiLCJVc2VyTmFtZSI6IuadqOeEtiIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTM0NTQ4Mjk3NTcwMDY2NTY2IiwiUGhvbmUiOiIxMzAxNTcxMTQxNiIsIkdyb3VwSUQiOiIxOTM0NTQ4Mjk3NTYxNjc3OTU4IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMDYtMTcgMDA6NTM6NDciLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.y0P6TcUnM8WLyK0Ya9C4EugjTpt4hAzMpps1NcCsGC6reum0BBD2GnD2Y9b82MkpASumwQCTReS70yhrkDd_l4m76I47SeiywSt-GST5IWdPW-3P2lK6A_aDAG6uerhmIqrc5vPcwpQ4XisD9EObKmKj-OmFfT8pno371i9M8HhCCCmbosKvwwQkeInj3Hp5EJcqJEceFMxy_a9bP9RiEStzO65EFhM-5LgO8Rf3PA-sOYs2MR41kx6nb-fiGxfEzDi6eWs-S5VPFOnZsayuhxmeVKg00svwgodlrDmMvhllCVdI44qIzdrGlbDLWZ0epbt2h81SaszPKc9YtL663g"

    def __init__(self):
        super().__init__()

    def req_pic(self, promt_strs):
        payload = json.dumps({
            "model": "image-01",
            "prompt": promt_strs,
            "aspect_ratio": "1:1",
            "response_format": "url",
            "n": 1,
            "prompt_optimizer": True
        })
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", self.url, headers=headers, data=payload)

        print(response.json())

# hailuo = HaiLuoAI()
# hailuo.req_pic("一只猫")