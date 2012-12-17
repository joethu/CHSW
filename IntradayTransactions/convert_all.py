# 
import os
import sys
import fnmatch
import re

# find xls data
source = os.getcwd()
if (len(sys.argv)==2):
    source = sys.argv[1]

xlsfile = fnmatch.translate('*.xls')
for filename in os.listdir(source):
    if re.match(xlsfile, filename):
        filename = os.path.join(source, filename)
        filename2 = filename + '.sql.txt'
        print filename
        run1 = 'convert "%s" "convert_template_am5min.txt" >> "%s"' % (filename, filename2)
        os.system(run1)
        run2 = 'convert "%s" "convert_template_pm5min.txt" >> "%s"' % (filename, filename2)
        os.system(run2)
