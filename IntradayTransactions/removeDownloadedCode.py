def removeNewLine(linesFromFile):
    newLines = []
    for line in linesFromFile:
        newLines.append(line.rstrip("\n"))
    return newLines

file_succeeded = open("DownloadedCodes.txt","r")
codes_succeeded = removeNewLine(file_succeeded.readlines())
file_succeeded.close()

file_Sina = open("ACode_Sina.txt",'r')
codes_all = removeNewLine(file_Sina.readlines())
file_Sina.close()
file_Sina = open("ACode_Sina.txt",'w')
i = 0
for code in codes_all:
    try:
        codes_succeeded.index(code)
        print("remove: " + code)
    except ValueError as e:
        if not i == 0:
            file_Sina.write("\n")            
        file_Sina.write(code)
        i = i + 1
file_Sina.close()
