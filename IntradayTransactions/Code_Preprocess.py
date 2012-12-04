# read HS300 codes, format in e.g 000001.SZ
file = open("ACodes.txt",'r')
codes = file.readlines()
file.close()
# create a new file to save the sina format
file_sina = open("ACode_Sina.txt",'w+')
for code in codes:
    code = code.rstrip('\n')
    code_sep_ex = code.partition('.')
    code_sina = code_sep_ex[2].lower() + code_sep_ex[0]
    file_sina.write(code_sina)
    file_sina.write('\n')

file_sina.close()
