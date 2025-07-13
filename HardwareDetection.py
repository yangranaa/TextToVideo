import subprocess


class HardwareDetection:

    _hardware_sup_dict = {}

    @classmethod
    def is_encoder_available(cls, encoder_name):
        try:
            # 获取所有编码器列表
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True
            )
            # 检查编码器名称是否在输出中
            return encoder_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def get_fast_encoder(cls, codec):
        result = {}
        result['b:v'] = '10M'
        result['maxrate'] = '15M'
        result['profile:v'] = 'high'
        result['c:a'] = 'flac'
        result['r'] = '30'

        if codec == "h264_nvenc":
            result['c:v'] = 'h264_nvenc'
            result['pix_fmt'] = 'yuv420p'
            result['preset'] = 'slow'
            result['rc'] = 'vbr_hq'
            result['cq'] = '20'
        elif codec == "h264_qsv":
            result['c:v'] = 'h264_qsv'
            result['usage'] = 'veryslow'  # 类似预设（可选: veryslow, slower, fast等）
            result['icq'] = '23'  # 智能恒定质量（0-51）
        elif codec == "h264_amf":
            result['c:v'] = 'h264_amf'
            result['quality'] = 'quality'  # 质量模式（speed/balanced/quality）
            result['qp_i'] = '20'  # I帧量化参数（0-51）
            result['qp_p'] = '23'  # P帧量化参数
            result['rc'] = 'VBR_QP'
        else:
            result['c:v'] = 'libx264'
            result['preset'] = 'slow'
            result['crf'] = '23'
            result['bufsize'] = '30M'

        return result