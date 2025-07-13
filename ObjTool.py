# 打印对象的所有属性和方法
import json
import traceback


def print_dir(obj):
    for attr_name in dir(obj):
        print(attr_name)

# 打印对象的属性
def print_attr(obj):
    for attr_name in dir(obj):
        if not callable(getattr(obj, attr_name)) and not attr_name.startswith('__'):
            print(f"{attr_name}: {getattr(obj, attr_name)}")

# 打印对象的方法
def print_fun(obj):
    for attr_name in dir(obj):
        if callable(getattr(obj, attr_name)) and not attr_name.startswith('__'):
            print(f"{attr_name}")

def print_trace_back():
    stack = traceback.extract_stack()  # 获取当前堆栈
    print("当前调用堆栈：")
    for line in traceback.format_list(stack):
        print(line.strip())

def print_dict(my_dict):
    print(json.dumps(my_dict, indent=4))