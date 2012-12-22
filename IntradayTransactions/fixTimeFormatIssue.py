import os
import sys

def removeNewLine(linesFromFile):
    newLines = []
    for line in linesFromFile:
        newLines.append(line.rstrip("\n"))
    return newLines

if (len(sys.argv)==3): 
    g_dir1 = os.path.abspath(sys.argv[1])
    g_dir2 = os.path.abspath(sys.argv[2])
    if not g_dir1.upper() == g_dir2.upper():
        if os.path.exists(g_dir1):
            if not os.path.exists(g_dir2):
                os.mkdir(g_dir2)
            for root, dirs, files in os.walk(g_dir1):
                for filename in files:
                    print('Fix ' + filename + ' ... ')
                    f_old = open(os.path.join(g_dir1,filename))
                    lines = f_old.readlines()
                    f_old.close()
                    f_new = open(os.path.join(g_dir2,filename),'wt')
                    for line in lines:
                        line2 = line.replace(';','')
                        line2 = line2.replace(' 12:59',' 13:00')
                        line2 = line2.replace(' 01:',' 13:')
                        line2 = line2.replace(' 02:',' 14:')
                        f_new.write(line2)
                    f_new.close()
else: 
    print 'Usage: convert <old_folder> <new_folder>' 
