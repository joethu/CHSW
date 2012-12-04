import os

def genSinaLink(date,code):
    return "http://market.finance.sina.com.cn/downxls.php?date=" + date + "&symbol=" + code

# read HS300 code, format in sz000001
file_HS300Sina = open("HS300_Sina.txt",'r')
codes = file_HS300Sina.readlines()
file_HS300Sina.close()
# read TradeDates, format in 2007-01-04
file_tradeDates = open("TradeDates.txt",'r')
dates = file_tradeDates.readlines()
file_tradeDates.close()

dirName='links'
if not os.path.exists(dirName):
    os.mkdir('links')
for code in codes:
    code = code.rstrip('\n')
    # create a new file to save the sina links
    fileName = "links\\links_" + code + '.txt'
    file_linkcode = open(fileName,'w+')
    lenDates = len(dates)
    i = 0
    for date in dates:
        date = date.rstrip('\n')
        link = genSinaLink(date,code)
        file_linkcode.write(link)
        i = i + 1
        if i == lenDates:
            break
        file_linkcode.write('\n')
    file_linkcode.close()
