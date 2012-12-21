import os
import sys

def removeNewLine(linesFromFile):
    newLines = []
    for line in linesFromFile:
        newLines.append(line.rstrip("\n"))
    return newLines

if (len(sys.argv)==4): 
    file_symbolsToLoad = open(os.path.abspath(sys.argv[1]))
    dir_data = os.path.abspath(sys.argv[2])
    if file_symbolsToLoad and os.path.exists(dir_data):
        mergedSQLFileName = os.path.abspath(sys.argv[3])
        file_meregedSQL = open(mergedSQLFileName,'wt')
        symbols = removeNewLine(file_symbolsToLoad.readlines())
        file_symbolsToLoad.close()
        for symbol in symbols:
            dataFileAbsPath = os.path.join(dir_data,symbol+'.sql')
            if os.path.exists(dataFileAbsPath):
                dataFileAbsPath = dataFileAbsPath.replace('\\','\\\\')
                print(dataFileAbsPath)
                file_meregedSQL.write('load data local infile \'' + dataFileAbsPath + '\' into table ohlcquotation columns terminated by \',\' LINES terminated by \';\';\n')
        file_meregedSQL.close()
else: 
    print 'Usage: loadSymbols <symbolsToLoad_File> <Data Sql_Dir> <OutputSQL_File>' 