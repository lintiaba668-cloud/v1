"""V3.1 Lite 字段解析优化"""
import re
INVALID='\\/:*?"<>|'
PREFIX=('B113','C513','181320','5Z')

def sanitize_filename(name:str)->str:
    for c in INVALID:
        name=name.replace(c,'')
    return name.strip()

def merge_lines(lines,index):
    text=lines[index].strip()
    if index+1<len(lines) and len(text)<25:
        nxt=lines[index+1].strip()
        if not any(k in nxt for k in ['工程编号','项目编号','工程名称','项目名称']):
            text+=nxt
    return text

def find_code(lines,start):
    area=' '.join(lines[start:start+3])
    m=re.findall(r'[A-Za-z0-9-]{5,}',area)
    if not m:return ''
    code=max(m,key=len).upper().replace('O','0').replace('I','1').replace('S','5')
    if code.startswith('5513'): code='C'+code[2:]
    return code

def valid_power_code(code):
    return any(code.startswith(p) for p in PREFIX)
