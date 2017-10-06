import re
import os
import io
import tempfile
import subprocess

class PdfPayTable:
    def __init__(self, folder):
        self.folder = folder


    def read_file(self, full_html_bytes, encode="utf-8"):
        #FILE = open(filename, mode="r", encoding=encode)
        FILE = io.StringIO(full_html_bytes.decode(encoding=encode))
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


    def extract_share_pay_table(self, table_text, pay_list):
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


    def convert_pdf_to_html(self, filename):
        #(pipe_r, pipe_w) = os.pipe()
        result = subprocess.run("pdftohtml -i {path}/{name}.PDF -stdout".format(path=self.folder, name=filename),
                      shell=True, stdout=subprocess.PIPE)

        return result.stdout

        '''
        byte_strs = []
        file_binary = os.read(pipe_r, 1024)
        while file_binary is not None:
            byte_strs.append(file_binary)
            file_binary = os.read(pipe_r, 1024)
        return bytes.join(byte_strs)
        '''


    def read_table(self, filename):
        full_html_bytes = self.convert_pdf_to_html(filename)

        text_list = []
        use_share_table = False
        for encoding in ["utf-8", "gbk", "gb2312", "hz"]: #, "gb18030", "iso2022_jp_2"]:
            try:
                (text_list, use_share_table) = self.read_file(full_html_bytes, encoding)
                break
            except UnicodeDecodeError as e:
                print(e)

        table_text = "".join(text_list)
        table_text = re.sub('&#160;', ' ', string=table_text)
        table_text = re.sub('<br/>', ' ', string=table_text)

        pay_list = []
        if use_share_table:
            self.extract_share_pay_table(table_text, pay_list)
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


if __name__ == '__main__':
    filename = "zjj" #"zqgf"
    pdfpaytable = PdfPayTable('/home/yluo/download')
    pdfpaytable.read_table(filename)
