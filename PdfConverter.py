import subprocess

class PdfConverter:
    def __init__(self, folder):
        self.folder = folder

    def convert_pdf_to_html(self, filename):
        #(pipe_r, pipe_w) = os.pipe()
        result = subprocess.run("pdftohtml -i {path}/{name}.PDF -stdout".format(path=self.folder, name=filename),
                      shell=True, stdout=subprocess.PIPE)

        return result.stdout
