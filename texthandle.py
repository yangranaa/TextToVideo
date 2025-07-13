
import re

# with open('C:\\Users\\Administrator\\Desktop/ceshi.txt', 'r+', encoding='utf-8') as file:
#     content = file.read()
#     content = content.replace('。', "。\n")
#     file.seek(0)
#     print(content)
#     file.write(content)

class texthandle:

    def gen_txt_to_list(self, txt_path):
        def read_file(path):
            with open(path, 'r', encoding = 'utf-8') as file:
                for line in file:
                    yield line.strip()

        pattern_str = r'[\u4e00-\u9fff\u3400-\u4dbf0-9a-zA-Z\+\-\*\/\%]+'
        pattern = re.compile(pattern_str)

        zhangjie_pattern = r'第*章'
        zhangjie_pat = re.compile(zhangjie_pattern)

        str_count = 0
        con_str = ''
        for line in read_file(txt_path):
            if zhangjie_pat.findall(line):
                continue
            sub_list = pattern.findall(line)
            self.line_list += sub_list

            if len(sub_list) > 0:
                con_str = ''
                for str in sub_list:
                    con_str += str
                self.gen_line_list.append(con_str)

            # for sub in sub_list:
            #     sub_len = len(sub)
            #     if str_count > 10 and sub_len > 15:
            #         self.gen_line_list.append(con_str)
            #         str_count = 0
            #         con_str = ''
            #
            #     str_count += sub_len
            #     con_str += sub
            #     if str_count > 15:
            #         self.gen_line_list.append(con_str)
            #         str_count = 0
            #         con_str = ''

        re.purge()

    def __init__(self, txt_path):
        self.gen_line_list = []
        self.line_list = []

        self.gen_txt_to_list(txt_path)