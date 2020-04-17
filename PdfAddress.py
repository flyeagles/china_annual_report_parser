import re

import PdfConverter

class PdfAddress:

    def get_address(self, pdfconverter):
        raw_addr = self.get_address_raw(pdfconverter)
        return re.sub(r'^中国', '', string=raw_addr)

    def get_address_raw(self, pdfconverter):
        FILE = pdfconverter.get_FILE()
        address = ""
        text_list = []
        in_table = False
        for line in FILE:
            if in_table:
                text_list.append(line)
                if re.search('公司网址', line):
                    break
                if re.search('邮政编码', line):
                    break

            if re.search('办公地址', line):
                in_table = True
                shortline = re.sub('.*?办公地址', '', line)
                text_list.append(shortline)


        text = ''.join(text_list)
        text = re.sub('&#160;', ' ', string=text)
        text = re.sub('<br/>', ' ', string=text)

        match = re.search('[\w（）·]+', text)
        if match is None:
            return ""

        return re.sub('[（）·]+', '', match.group(0))


if __name__ == '__main__':

    filename = "001979_2016.PDF"
    pdfconverter = PdfConverter.PdfFileConverter('../reports/year/2016/0019', filename)

    pdfaddress = PdfAddress()
    address = pdfaddress.get_address(pdfconverter)
    print(address)

    pdfconverter.close()
