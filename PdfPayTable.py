import re
import os
import io
import tempfile
import subprocess


class PayTableExtracter:
    def __init__(self):
        self.text_list = None

    def get_pay_table(self):
        return None

    def convert_to_space(self, text_list):
        table_text = "".join(text_list)
        table_text = re.sub('&#160;', ' ', string=table_text)
        table_text = re.sub('<br/>', ' ', string=table_text)
        return table_text



class PayTableExtractorNormal(PayTableExtracter):
    def __init__(self, text_list):
        super(PayTableExtractorNormal, self).__init__()
        self.text_list = text_list


    def get_pay_table(self):
        table_text = self.convert_to_space(self.text_list)

        '''
        姓名 | 职务 | 性别 | 年龄 | 任职状态 | 从公司获得的税前报酬总额 | 是否在公司关联方获取报酬
        '''
        pay_list = []
        res = re.findall("([\w\u3001]+)\s+([\w\u3001]+)\s+(\w+)\s+(\d+)\s+(\w+)\s+([\d\.]+)\s+\w+", table_text)
        if res:
            for item in res:
                pay = []
                for i in range(0, 6):
                    pay.append(item[i])
                if '\u3001' in pay[0]:
                    temp = pay[0]
                    pay[0] = pay[1]
                    pay[1] = temp
                pay_list.append(pay)

        return pay_list


class PayTableExtractorShare(PayTableExtracter):
    def __init__(self, text_list, report_date):
        super(PayTableExtractorShare, self).__init__()
        self.text_list = text_list
        self.report_date = report_date

        self.pat_name = '([\w\u3001]+)'
        self.pat_role = '([\w\u3001]+)'
        self.pat_sex = '(\w+)'
        self.pat_age = '(\d+)'
        self.pat_start_date = '[\d\-]+'
        self.pat_end_date = '([\d\-]+)'
        self.pat_start_shares = '([\d\,]+)'
        self.pat_end_shares = '([\d\,]+)'
        self.pat_change_shares = '[\d\,\-]+'
        self.pat_note = '[\w]+'
        self.pat_salary = '([\d\.]+)'
        self.pat_related_pay = '\w+'
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


    def get_full_row_pattern(self):
        full_pat_list = [self.pat_name, self.pat_role, self.pat_sex, self.pat_age,
            self.pat_start_date, self.pat_end_date, self.pat_start_shares,
            self.pat_end_shares, self.pat_change_shares, self.pat_note,
            self.pat_salary, self.pat_related_pay]

        return '\s+'.join(full_pat_list)

    def get_partial_row_pattern_minus_10(self):
        full_pat_list = [self.pat_name, self.pat_role, self.pat_sex, self.pat_age,
            self.pat_start_date, self.pat_end_date, self.pat_start_shares,
            self.pat_end_shares, self.pat_change_shares,
            self.pat_salary, self.pat_related_pay]

        return '\s+'.join(full_pat_list)

    def get_partial_row_pattern_minus_12(self):
        full_pat_list = [self.pat_name, self.pat_role, self.pat_sex, self.pat_age,
            self.pat_start_date, self.pat_end_date, self.pat_start_shares,
            self.pat_end_shares, self.pat_change_shares, self.pat_note,
            self.pat_salary]

        return '\s+'.join(full_pat_list)


    def extract_share_pay_table(self, table_text):
        pay_list = []
        col_adjust = 0
        last_col_null = False
        res = re.findall(self.get_full_row_pattern(), table_text)
        if res is None or len(res) == 0:
            col_adjust = 0  # has no column 10
            res = re.findall(self.get_partial_row_pattern_minus_10(), table_text)
            if res is None or len(res) == 0:
                col_adjust = 0
                res = re.findall(self.get_partial_row_pattern_minus_12(), table_text)

        if res:
            for item in res:
                pay = []
                for i in range(0, 4):
                    pay.append(item[i])

                #pay.append(item[4])

                if item[4] < self.report_date:
                    pay.append('离任')  # end of tenure
                else:
                    pay.append('现任')


                pay.append(item[7 - col_adjust])  # pay

                if '\u3001' in pay[0]:
                    temp = pay[0]
                    pay[0] = pay[1]
                    pay[1] = temp

                pay_list.append(pay)

        return pay_list


    def get_pay_table(self):
        table_text = self.convert_to_space(self.text_list)
        return self.extract_share_pay_table(table_text)





class PdfPayTable:
    def __init__(self, folder):
        self.folder = folder


    def read_file(self, full_html_bytes, report_date='2016-12-31', encode="utf-8"):
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

        if use_share_table:
            return PayTableExtractorShare(text_list, report_date)
        else:
            return PayTableExtractorNormal(text_list)



    def convert_pdf_to_html(self, filename):
        #(pipe_r, pipe_w) = os.pipe()
        result = subprocess.run("pdftohtml -i {path}/{name}.PDF -stdout".format(path=self.folder, name=filename),
                      shell=True, stdout=subprocess.PIPE)

        return result.stdout



    def read_table(self, filename, report_date):
        full_html_bytes = self.convert_pdf_to_html(filename)

        use_share_table = False
        payextracter = None
        for encoding in ["utf-8", "gbk", "gb2312", "hz"]: #, "gb18030", "iso2022_jp_2"]:
            try:
                payextracter = self.read_file(full_html_bytes, report_date, encoding)
                break
            except UnicodeDecodeError as e:
                print(e)

        return payextracter.get_pay_table()


if __name__ == '__main__':
    filename = "jwdz" #"zqgf"
    pdfpaytable = PdfPayTable('/home/yluo/download')
    pay_list = pdfpaytable.read_table(filename, '2016-12-31')
    print(pay_list)
