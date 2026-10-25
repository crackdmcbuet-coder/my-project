from pypdf import PdfWriter, PdfReader
import sys
w = PdfWriter()
w.append(PdfReader("cover.pdf"), import_outline=False)
w.append(PdfReader("body.pdf"))
w.add_metadata({"/Title": "সকাল-সন্ধ্যা ও রাতের মাসনূন আমল", "/Author": "Raqi Faisal Ahmed Sabit — Al Quranic Ruqyah Healing", "/Subject": "কুরআন ও হাদীসের আলোকে যিকির, দুআ ও সূরা"})
w.write(sys.argv[1])
