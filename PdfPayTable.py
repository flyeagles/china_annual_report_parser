import re
import io
import logging

import PdfConverter

logging.basicConfig(format='%(asctime)s]%(message)s', filename="PdfPayTable.log", level=logging.INFO)


def swap_list_item(list, pos1, pos2):
    temp = list[pos1]
    list[pos1] = list[pos2]
    list[pos2] = temp


def shift_list_item(list, pos1, pos2):
    temp = list[pos1]
    list[pos1:pos1 + 1] = []
    list.insert(pos2, temp)


class PayTableExtracter:
    def __init__(self):
        self.text_list = None

    def get_pay_table(self):
        return None

    def convert_to_space(self, text_list):
        table_text = "".join(text_list)
        table_text = re.sub('&#160;', ' ', string=table_text)
        table_text = re.sub('<br/>', ' ', string=table_text)
        table_text = re.sub('\s+', ' ', string=table_text)
        return table_text



class PayTableExtractorNormal(PayTableExtracter):
    def __init__(self, text_list, symbol):
        super(PayTableExtractorNormal, self).__init__()
        self.text_list = text_list
        self.symbol = symbol
        self.type = "normal"

        self.pat_name = '([\w\u3001]{2,12}|\w\s\w)'
        self.pat_role = '([\w\u3001/]+)'
        self.pat_sex = '(\w+)'
        self.pat_age = '(\d+)'
        self.pat_status = '(\w+)'
        self.pat_salary = '([\d\.]+)'
        self.pat_note = '\w+'

    def get_pattern(self, pat_id):
        '''
        姓名 | 职务 | 性别 | 年龄 | 任职状态 | 从公司获得的税前报酬总额 | 是否在公司关联方获取报酬
        '''
        pat_list = [self.pat_name, self.pat_role, self.pat_sex, self.pat_age,
            self.pat_status, self.pat_salary, self.pat_note]
        if pat_id == 2:
            '''
            姓名 | 职务 | 任职状态|性别 | 年龄 |  从公司获得的税前报酬总额 | 是否在公司关联方获取报酬
            '''
            pat_list = [self.pat_name, self.pat_role, self.pat_status, self.pat_sex, self.pat_age,
                         self.pat_salary, self.pat_note]

        return '\s+'.join(pat_list)


    def get_pay_table(self):
        table_text = self.convert_to_space(self.text_list)
        pay_list = []
        for pat_id in [1, 2]:
            res = re.findall(self.get_pattern(pat_id), table_text)
            if res and len(res) > 0:
                for item in res:
                    pay = []
                    for i in range(0, 6):
                        pay.append(item[i])

                    if '\u3001' in pay[0] or len(pay[0]) > 4:
                        swap_list_item(pay, 0, 1)

                    if pat_id == 2:
                        shift_list_item(pay,2, 4 )

                    if re.search('\d', pay[0]+pay[1]):
                        continue   # for case like ['2011', '董事、监事的津贴经公司于', '年', '7', '月', '14']

                    pay[0] = re.sub('\s', '', pay[0])

                    pay_list.append(pay)
                break

        logging.info("[{sym}][{type}][pattern:{pat}][{rows}]".format(sym=self.symbol,type=self.type, pat=pat_id, rows=len(pay_list)))

        return pay_list


class PayTableExtractorShare(PayTableExtracter):
    def __init__(self, text_list, report_date, symbol):
        super(PayTableExtractorShare, self).__init__()
        self.text_list = text_list
        self.report_date = report_date
        self.symbol = symbol
        self.type = "share"

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

                if '\u3001' in pay[0] or len(pay[0]) > 4:
                    swap_list_item(pay, 0, 1)

                if re.search('\d', pay[0]+pay[1]):
                    continue   # for case like ['2011', '董事、监事的津贴经公司于', '年', '7', '月', '14']

                pay[0] = re.sub('\s', '', pay[0])

                pay_list.append(pay)

        logging.info("[{sym}][{type}][{rows}]".format(sym=self.symbol,type=self.type, rows=len(pay_list)))
        return pay_list


    def get_pay_table(self):
        table_text = self.convert_to_space(self.text_list)
        return self.extract_share_pay_table(table_text)

class PdfPayTable:
    def __init__(self):
        pass

    def read_file(self, filename, FILE, report_date='2016-12-31'):
        in_table = False
        use_share_table = False
        text_list = []
        for line in FILE:
            #print(line)
            if re.search('高级管理人员报酬情况', line):
                in_table = True

            if in_table:
                text_list.append(line)
                if re.search('员工情况', line):
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

        if use_share_table:
            return PayTableExtractorShare(text_list, report_date, filename)
        else:
            return PayTableExtractorNormal(text_list, filename)


    def read_table(self, filename, pdfconverter, report_date):

        use_share_table = False
        payextracter = None
        for encoding in ["utf-8", "gbk", "gb2312", "hz"]: #, "gb18030", "iso2022_jp_2"]:
            try:
                FILE = pdfconverter.get_FILE(encoding)
                payextracter = self.read_file(filename, FILE, report_date)
                break
            except UnicodeDecodeError as e:
                print(e)

        return payextracter.get_pay_table()


if __name__ == '__main__':
    filename = "000100_2016.PDF"
    pdfconverter = PdfConverter.PdfFileConverter('../reports/year/2016/0001', filename)

    pdfpaytable = PdfPayTable()
    pay_list = pdfpaytable.read_table(filename, pdfconverter, '2016-12-31')
    print(pay_list)

    pdfconverter.close()