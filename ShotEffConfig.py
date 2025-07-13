import random

shot_enter_eff_config = [("滑入","huaru",0.67), ("斜线","xiexian", 0.67), ("漩涡","xuanwo", 0.5), ("扫描","saomiao", 0.5), ("无","")]

shot_eff_config = [("缓慢移动","yidong"), ("警告","jinggao"), ("抖动","doudong"), ("无效果","tupian")]

shot_after_eff_config = [("金粉", "jinfen"), ("萤火虫", "yinghuochong"), ("光束", "guangshu"), ("动感推镜","donggantuijing"), ("丁达尔", "dingdaer"), ("无", "")]

def find_eff_index(eff):
    for idx, eff_config in enumerate(shot_eff_config):
        if eff_config[1] == eff:
            return idx

def find_enter_eff_index(eff):
    for idx, eff_config in enumerate(shot_enter_eff_config):
        if eff_config[1] == eff:
            return idx

def get_enter_eff_config(eff):
    for idx, eff_config in enumerate(shot_enter_eff_config):
        if eff_config[1] == eff:
            return eff_config

def find_after_eff_idx(eff):
    for idx, eff_config in enumerate(shot_after_eff_config):
        if eff_config[1] == eff:
            return idx