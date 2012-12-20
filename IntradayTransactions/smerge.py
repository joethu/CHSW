# Simple Merge
import os
import fnmatch
import re

g_mergefile = fnmatch.translate('merge.txt')

def merge(root):
    mergefiles = []
    for root, dir, files in os.walk(root):
        for filename in files:
            if not re.match(g_mergefile, filename):
                continue
            fullname = os.path.join(root, filename)
            mergefiles.append(fullname)
    for mergefile in mergefiles:
        f = open(mergefile, 'rt')
        refs = f.readlines()
        f.close()
        if len(refs)>1:
            mergefile2 = mergefile + '.out.txt'
            f2 = open(mergefile2, 'wt')
            for ref in refs:
                ref = ref.strip('\n')
                f = open(ref, 'rt')
                f2.writelines(f.readlines())
                f.close()
            f2.close()
        print(mergefile)
#
import sys
if (len(sys.argv)==2): 
    merge(os.path.abspath(sys.argv[1]))
else: 
    print 'Usage: merge <folder>' 

#test
#os.system('convert "convert_test_sh600219_2012-12-06.xls" "convert_template_am5min.txt"') 

