import unittest
import os
import sys

sys.path.append('..')
import PdfPayTable


class TestPdfPayTable(unittest.TestCase):

    def setUp(self):
        self.root = os.getcwd()

    def tearDown(self):
        os.chdir(self.root)

    def test_world(self):
        hello = 'hello'
        self.assertEqual(hello, 'hello')

    def test_init_close(self):
        pdfpaytable = PdfPayTable.PdfPayTable('/home/yluo')
        tempfolder = pdfpaytable.get_temp_folder()
        pdfpaytable.close()
        self.assertFalse(os.path.exists(tempfolder))

    def test_convert_pdf_to_html(self):
        pdfpaytable = PdfPayTable.PdfPayTable('input')
        tempfolder = pdfpaytable.get_temp_folder()
        filename = "normal_pay_table"

        newfilename = pdfpaytable.convert_pdf_to_html(filename)

        self.assertTrue(os.path.exists(newfilename))

        #print(tempfolder)
        pdfpaytable.close()

    def test_read_file(self):
        pdfpaytable = PdfPayTable.PdfPayTable('input')
        filename = "normal_pay_tables.html"
        (text_list, use_share_table) = pdfpaytable.read_file(filename)
        print(text_list)
        print(use_share_table)

        pdfpaytable.close()


if __name__ == '__main__':
    unittest.main()