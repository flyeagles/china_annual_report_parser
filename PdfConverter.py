import subprocess
import io
import logging
import tempfile
import os

import sys
sys.path.append('/home/yluo/stocks/common')
import auxi

class PdfFileConverter:

    def __init__(self, folder, filename):
        self.folder = folder
        self.filename = filename
        self.html_bytes = self._convert_pdf_to_html(filename)
        self.FILE = None

    def _convert_pdf_to_html(self, filename):
        #(pipe_r, pipe_w) = os.pipe()
        fullfilename = '{path}/{name}'.format(path=self.folder, name=filename)
        cmd = "pdftohtml -i {fullname} -stdout -l 100".format(fullname=fullfilename)
        logging.info(cmd)
        auxi.printt(cmd)
        if os.stat(fullfilename).st_size > 7000000: # 7 MB
            (tfileid, tfilename) = tempfile.mkstemp()
            subprocess.run(cmd, shell=True, stdout=tfileid, stderr=None)
            os.close(tfileid)

            TFILE = open(tfilename, mode='rb')

            bytes_list = []
            bytes = TFILE.read(10240)
            while bytes is not None and len(bytes)>0:
                bytes_list.append(bytes)
                bytes = TFILE.read(10240)

            TFILE.close()
            os.unlink(tfilename)
            return b''.join(bytes_list)
        else:
            res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=None)
            # Pipe will block when file size > 8 MB.
            return res.stdout

    def get_FILE(self):
        if self.FILE:
            self.FILE.seek(0, io.SEEK_SET)
            return self.FILE

        for encoding in ["utf-8", "gbk", "gb2312", "hz"]: #, "gb18030", "iso2022_jp_2"]:
            linecnt = 0
            try:
                FILE = io.StringIO(self.html_bytes.decode(encoding=encoding, errors='ignore'))
                for line in FILE:
                    linecnt += 1
                    pass

                self.FILE = FILE
                self.FILE.seek(0, io.SEEK_SET)
                if linecnt > 1000:
                    break
                else:
                    print("Not encoded with " + encoding)

            except UnicodeDecodeError as e:
                print(e)


        return self.FILE




    def close(self):
        self.FILE.close()
