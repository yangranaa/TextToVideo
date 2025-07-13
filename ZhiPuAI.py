from zhipuai import ZhipuAI

from PicRequest import PicRequest

class ZhiPuAI(PicRequest):

    def __init__(self, api_key):
        super().__init__()

        self.client = ZhipuAI(api_key=api_key)  # 请填写您自己的APIKey

    def req_pic(self, promt_strs):

        response = self.client.images.generations(
            model="CogView-3-Flash",  # 填写需要调用的模型编码
            prompt=promt_strs,
        )

        return [response.data[0].url]


    def req_video(self, prompt_str):
        image_url = r"C:\Users\Administrator\Desktop\12.jpg"  # 替换为您的图片URL地址

        # 调用视频生成接口
        response = self.client.videos.generations(
            model="CogVideoX-Flash",  # 使用的视频生成模型
            image_url=image_url,  # 提供的图片URL地址或者 Base64 编码
            prompt=prompt_str,
            quality="speed",  # 输出模式，"quality"为质量优先，"speed"为速度优先
            with_audio=True,
            size="1920x1080",  # 视频分辨率，支持最高4K（如: "3840x2160"）
            fps=30,  # 帧率，可选为30或60
        )

        print(response, response.id)

    def down_load_video(self):
        video_result = self.client.videos.retrieve_videos_result(
            id='6311750075524917'
        )

        print(video_result)


# zpa = ZhiPuAI()
# zpa.req_video("让画面动起来")
# zpa.down_load_video()