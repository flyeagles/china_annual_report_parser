import re
import os
import io

def read_file(filename, encode="utf-8"):
    FILE = open("{name}s.html".format(name=filename), mode="r", encoding=encode)
    in_table = False
    use_share_table = False
    text_list = []
    for line in FILE:

        #print(line)

        if re.search('高级管理人员报酬情况', line):
            in_table = True

        if in_table:
            text_list.append(line)
            if re.search('公司员工情况', line):
                break
            elif re.search('高级管理人员变动情况', line):
                use_share_table = True
                break
                # need refetch the table

    if use_share_table:
        text_list = []
        in_table = False
        FILE.seek(0, io.SEEK_SET)
        for line in FILE:

            if re.search('高级管理人员持股变动及报酬情况', line):
                in_table = True

            if in_table:
                text_list.append(line)
                if re.search('合计', line):
                    break

    FILE.close()
    return (text_list, use_share_table)


def extract_share_pay_table(table_text, pay_list):
    '''
    1.姓名
    2.职务(注)
    3.性别
    4.年龄
    5.任期起始日期
    6.任期终止日期
    7.年初持股数  # could be empty
    8.年末持股数  # could be empty
    9.年度内股份增减变动量  # could be empty
    10.增减变动原因  # might be empty
    11.报告期内从公司获得的税前报酬总额（万元）
    12.是否在公司关联方获取报酬  # could be empty
    '''
    col_adjust = 0
    last_col_null = False
    res = re.findall(
        "([\w\u3001]+)\s+([\w\u3001]+)\s+(\w+)\s+(\d+)\s+([\d\-]+)\s+([\d\-]+)\s+([\d,]+)\s+([\d,]+)\s+(\d+)\s+(\w+)\s+([\d\.]+)\s+(\w+)",
        table_text)
    if res is None:
        col_adjust = 1  # has no column 10
        res = re.findall(
            "([\w\u3001]+)\s+([\w\u3001]+)\s+(\w+)\s+(\d+)\s+([\d\-]+)\s+([\d\-]+)\s+([\d,]+)\s+([\d,]+)\s+(\d+)\s+([\d\.]+)\s+(\w+)",
            table_text)
        if res is None:
            col_adjust = 0
            last_col_null = True
            res = re.findall(
                "([\w\u3001]+)\s+([\w\u3001]+)\s+(\w+)\s+(\d+)\s+([\d\-]+)\s+([\d\-]+)\s+([\d,]+)\s+([\d,]+)\s+(\d+)\s+(\w+)\s+([\d\.]+)",
                table_text)

    if res:
        for item in res:
            pay = []
            for i in range(0, 4):
                pay.append(item[i])
            pay.append(item[5])  # end of tenure

            pay.append(item[10 - col_adjust])  # pay
            if last_col_null:
                pay.append(None)
            else:
                pay.append(item[11 - col_adjust])  # income from related party
            if '\u3001' in pay[0]:
                temp = pay[0]
                pay[0] = pay[1]
                pay[1] = temp

            pay_list.append(pay)


def read_table():
    os.chdir("/home/yluo/download")
    print(os.getcwd())

    filename = "dygk16" #"zqgf"
    if not os.path.exists("{name}s.html".format(name=filename)):
        os.system("pdftohtml -i {name}.PDF {name}".format(name=filename))

    text_list = []
    use_share_table = False
    for encoding in ["utf-8"]: #, "gbk", "gb2312", "hz", "gb18030", "iso2022_jp_2"]:
        try:
            (text_list, use_share_table) = read_file(filename, encoding)
            break
        except UnicodeDecodeError as e:
            print(e)

    table_text = "".join(text_list)
    table_text = re.sub('&#160;', ' ', string=table_text)
    table_text = re.sub('<br/>', ' ', string=table_text)

    pay_list = []
    if use_share_table:
        extract_share_pay_table(table_text, pay_list)
    else:
        '''
        姓名 | 职务 | 性别 | 年龄 | 任职状态 | 从公司获得的税前报酬总额 | 是否在公司关联方获取报酬
        '''
        res = re.findall("([\w\u3001]+)\s+([\w\u3001]+)\s+(\w+)\s+(\d+)\s+(\w+)\s+([\d\.]+)\s+(\w+)", table_text)
        if res:
            for item in res:
                pay = []
                for i in range(0,7):
                    pay.append(item[i])
                if '\u3001' in pay[0]:
                    temp = pay[0]
                    pay[0] = pay[1]
                    pay[1] = temp
                pay_list.append(pay)

    print(pay_list)

read_table()