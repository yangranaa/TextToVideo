import re

import cn2an

from ReplaceWindow import ReplaceData


def gen_txt(txt, **kwargs):
    result = txt

    for src,dst in ReplaceData.replace_dic.items():
        result = result.replace(src, dst)

    line_list = re.split('\n', result)
    line_list = [line for line in line_list if line.strip()]

    if kwargs.get("tra_num"):
        line_list = [cn2an.transform(line, 'an2cn') for line in line_list]
    if kwargs.get("remove_chapter"):
        zhangjie_pattern = r'^第.*章$'
        zhangjie_pat = re.compile(zhangjie_pattern)
        line_list = [line for line in line_list if not (zhangjie_pat.findall(line))]
    if kwargs.get("clear_mark"):
        pattern_str = r'[a-zA-Z\u4e00-\u9fff\u3400-\u4dbf\d]'
        pattern = re.compile(pattern_str)

        new_list = []
        for line in line_list:
            find_txts = pattern.findall(line)

            new_line = ' '.join(find_txts)
            new_list.append(new_line)

        line_list = new_list

    # line_list = check_line_len(line_list)

    result = '\n'.join(line_list)

    return result

def check_line_len(line_list, limit_line_len=20):
    new_list = []
    for line in line_list:
        if len(line) < limit_line_len:
            new_list.append(line)
        else:
            sp_list = line.split(' ')
            new_line = ''
            for sp_line in sp_list:
                if len(new_line) + len(sp_line) < limit_line_len:
                    new_line += sp_line
                else:
                    if len(new_line) > 0:
                        new_list.append(new_line)

                    new_line = sp_line

            if len(new_line) > 0:
                new_list.append(new_line)

    return new_list