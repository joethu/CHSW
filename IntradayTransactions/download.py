import urllib.request
import os
import os.path
import threading
import time
import socket

NUM_THREADS = 10
SEC_INTERVAL = 1
AVG_NUM_PER_SEC = 7.54 # used to calculated join timeout. this number differs according to NUM_THREADS
TIMEOUT_RELAX_FACTOR = 1.25
SOCKET_TIMEOUT = 1     # considering AVG_NUM_PER_SEC, 1 sec shld be large enough
TRY_TIMES_FILE = 4     # retry times per file
RETRY_TIMES_ALL =4     # recursive retry times to all failures

class DownloadThread(threading.Thread):
    def __init__(self, code, dates, index):
        threading.Thread.__init__(self)
        self.code   = code
        self.dates  = dates
        self.index = index
        self.finishedTo = -1   #To which index of dates, download is finished

    def run(self):
        for date in self.dates:
            link = "http://market.finance.sina.com.cn/downxls.php?date=" + date + "&symbol=" + self.code
            folder = "downloads/"+self.code
            if not os.path.exists(folder):
                os.mkdir(folder)
            fileName = self.code + "_" + date + ".xls"
            isDownloaded = False
            retryInterval = SEC_INTERVAL
            for i in range(TRY_TIMES_FILE):
                try:
                    urllib.request.urlretrieve(link, folder+"/"+fileName)
                    print("Saved: " + fileName)
                    self.finishedTo = self.finishedTo + 1
                    isDownloaded = True
                    break
                except Exception as e:
                    retryInterval = retryInterval*2
                    print("!!!Exception downloading "+ fileName + ": " + str(e.args) + " Retry-" + str(i) + " after " + str(retryInterval) + " sec!!!")
                    time.sleep(retryInterval)
            if isDownloaded:
                time.sleep(SEC_INTERVAL)
            else:
                print("!!Abort downloading " + self.code + "!!") # once one date fails, just exit and let calling thread record the remained dates
                break
        print("***Thread Ended: " + self.code + "-" + str(self.index) + "***")
        
def downloadCode(code, dates, join_timeout, file_succeeds):
    global gFailureDict
    
    CountFinishedThreads = 0    
    cntDates = len(dates)
    threadLoad = (int)(cntDates/NUM_THREADS)
    print("All Dates: "+str(cntDates)+" ThreadLoad: "+str(threadLoad))
    i = 0;
    l = 0;
    threads = []
    while i < NUM_THREADS:
        if i == NUM_THREADS - 1:
            r = cntDates
        else:
            r = l + threadLoad
        downloadThread = DownloadThread(code,dates[l:r],i)
        threads.append(downloadThread)
        downloadThread.start()
        l = r
        i = i + 1
    for thread in threads:
        print("--- Waiting for thread: " + str(thread.index) + " ---")
        thread.join(join_timeout)
        realLoad = len(thread.dates)
        if thread.finishedTo < realLoad-1:
            if not code in gFailureDict:
                gFailureDict[code] = []
            gFailureDict[code].extend(thread.dates[thread.finishedTo+1:realLoad])

    if code in gFailureDict:
        failures = gFailureDict[code]
        cntFailures = len(failures)
        if cntFailures > 0:
            sep = "##"
            print("--- " + str(cntFailures) + " FAILED DATES FOR " + code + ": " + sep.join(failures.__iter__()))
    else:
        print("------ FINISHED: " + code + " -------")
        file_succeeds.write(code + "\n")

def retryFailures(failuresDict, join_timeout, file_succeeds):
    newFailureDict = dict()
    cntFailures = len(failuresDict)
    if cntFailures < 1:
        return newFailureDict
    keys = list(failuresDict.keys())
    values = list(failuresDict.values())
    cntThreadSet = (int)(cntFailures/NUM_THREADS) + 1
    l = 0
    iThreadSet = 0
    while iThreadSet < cntThreadSet:
        threads = []
        r = l + NUM_THREADS
        if iThreadSet == cntThreadSet - 1:
            r = cntFailures
        for k in range(l,r):
            downloadThread = DownloadThread(keys[k],values[k],k)
            threads.append(downloadThread)
            downloadThread.start()
        for thread in threads:
            print("--- Waiting for thread: " + str(thread.index) + " ---")
            thread.join(join_timeout)
            realLoad = len(thread.dates)
            if thread.finishedTo < realLoad-1:
                if not thread.code in newFailureDict:
                    newFailureDict[thread.code] = []
                newFailureDict[thread.code].extend(thread.dates[thread.finishedTo+1:realLoad])
            else:
                file_succeeds.write(thread.code + "\n")
        iThreadSet = iThreadSet + 1
        l = r
    return newFailureDict
        

def removeNewLine(linesFromFile):
    newLines = []
    for line in linesFromFile:
        newLines.append(line.rstrip("\n"))
    return newLines

def downloadAll(file_succeeds):
    global gFailureDict
    # download
    # 1.read HS300 code, format in sz000001
    file_Sina = open("ACode_Sina.txt",'r')
    codes = removeNewLine(file_Sina.readlines())
    file_Sina.close()
    # 2.read TradeDates, format in 2007-01-04
    file_tradeDates = open("TradeDates_Downloads.txt",'r')
    dates = removeNewLine(file_tradeDates.readlines())
    file_tradeDates.close()
    # 3.start downloading

    socket.setdefaulttimeout(SOCKET_TIMEOUT)
    join_timeout = float(len(dates)) / AVG_NUM_PER_SEC * TIMEOUT_RELAX_FACTOR
    print("Join timeouts: " + str(join_timeout) + " ## Socket global timeouts: " + str(socket.getdefaulttimeout()))
    for code in codes:
        downloadCode(code,dates,join_timeout,file_succeeds)

    # retry
    maxRetryTimes = len(gFailureDict)
    if maxRetryTimes == 0:
        print("ALL DONE!")
    else:
        for i in range(maxRetryTimes):
            cntFailCode = len(gFailureDict)
            if cntFailCode == 0:
                print("ALL DONE!")
                break
            print("***** RetryAll-" + str(i) + " *****")
            print("Failure Codes Num: " + str(cntFailCode))
            print(str("###").join(gFailureDict.keys()))
            for code in gFailureDict.keys():
                print(code + ": " + str(len(gFailureDict[code])))
            gFailureDict = retryFailures(gFailureDict,join_timeout,file_succeeds)
        stillFails = gFailureDict.keys()
        if len(stillFails) > 0:
            file_fails = open("StillFailsCodes.txt",'w+')
            for sf in stillFails:
                file_fails.write(sf+"\n")
            file_fails.close()

def getDateListFromFileList(code,fileNames):
    datesList = []
    for file in fileNames: #format in sz300289_2011-12-30.xls
        (name,ext) = os.path.splitext(file) #name as sz300289_2011-12-30
        (c,s,date) = name.partition("_")
        datesList.append(date)
    return datesList
    
def downloadMissing(file_succeeds):
    #1.read TradeDates, format in 2007-01-04
    file_tradeDates = open("TradeDates_Downloads.txt",'r')
    set_allDates = set(removeNewLine(file_tradeDates.readlines()))
    length_dates = len(set_allDates)
    file_tradeDates.close()

    #2.traver downloads directories and find missing dates for each downloaded code
    rootDir = "downloads"
    missingDatesDict = dict()
    for dirPath,dirNames,fileNames in os.walk(rootDir):
        if len(dirNames) > 0: #go to the leaf directory
            continue
        code = os.path.basename(dirPath)
        print("Processing " + code)
        set_codeDates = set(getDateListFromFileList(code,fileNames))
        if not len(set_codeDates) == length_dates:
            set_missingDates = set_allDates - set_codeDates
            if len(set_missingDates) > 0:
                missingDatesDict[code] = list(set_missingDates)

    print("Totally " + str(len(missingDatesDict)) + " incomplete codes")
    for code,missingDates in missingDatesDict.items():
        print(code + " lacks: " + str("##").join(missingDates))

    socket.setdefaulttimeout(SOCKET_TIMEOUT)
    join_timeout = float(length_dates) / AVG_NUM_PER_SEC * TIMEOUT_RELAX_FACTOR
    print("Join timeouts: " + str(join_timeout) + " ## Socket global timeouts: " + str(socket.getdefaulttimeout()))

    maxRetryTimes = len(missingDatesDict)
    if maxRetryTimes == 0:
        print("No missing dates found!")
    else:
        for i in range(maxRetryTimes):
            cntFailCode = len(missingDatesDict)
            if cntFailCode == 0:
                print("ALL DONE!")
                break
            print("***** RetryAll-" + str(i) + " *****")
            print(str(cntFailCode) + " codes incompleted: " + str("###").join(missingDatesDict.keys()))
            for code in missingDatesDict.keys():
                print(code + ": " + str(len(missingDatesDict[code])))
            missingDatesDict = retryFailures(missingDatesDict,join_timeout,file_succeeds)
        stillFails = missingDatesDict.keys()
        if len(stillFails) > 0:
            file_fails = open("StillIncompleteCodes.txt",'w+')
            for sf in stillFails:
                file_fails.write(sf+"\n")
            file_fails.close()
    

# entrypoint
gFailureDict = dict()

def downloadSina(bAll):
    file_s = open("DownloadedCodes.txt",'w+')
    try:
        if bAll:
            downloadAll(file_s)
        else:
            downloadMissing(file_s)
    except Exception as e:
        print("ERROR: " + str(e.args))
    finally:
        file_s.close()

#1.firstly try downloading all
#downloadSina(True)

#2.find missing dates and re-download
downloadSina(False)
