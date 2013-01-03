import ConfigParser
import MySQLdb
from datetime import datetime,timedelta

CONFIG_FILE = 'Strategy.ini'
DB_SERVER = 'chsw1982.oicp.net'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWD = 'root'
DB_MAX_ROWS = 100000
def stripNewLine(linesFromFile):
    newLines = []
    for line in linesFromFile:
        newLines.append(line.rstrip("\n"))
    return newLines

#search the first element which is larger than or equal to _valToFind
#assumming _sortedList is in ascending order
def biSearch_firstLargerOrEqual(_sortedList,_valToFind,low=0,high=-1):
    res = -1
    if high == -1:
        high = len(_sortedList) - 1
    while low <= high:
        mid = (low + high) / 2
        val = _sortedList[mid]
        if val < _valToFind:
            low = mid + 1
        else:
            res = mid
            high = mid - 1
    return res

def readStrategySettings(strategy,paramList):
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(open(CONFIG_FILE))
    params = dict()
    if config.has_section(strategy):
        for param in paramList:
            params[param] = config.get(strategy,param)
    return params

class TradeMeta:
    POS_LONG = 'L'
    POS_SHORT = 'S'
    POS_CLOSE = 'C'
    RESTORE_RIGHTS_FORWARD = 'FORWARD'
    RESTORE_RIGHTS_BACKWARD = 'BACKWARD'

class TimePriceInfo:
    def __init__(self,_timeStamp,_price):
        self.timeStamp = _timeStamp
        self.price = _price

    @staticmethod
    def printTimePriceSequence(_timePriceList,_fileName):
        file = open(_fileName,'wb')
        for item in _timePriceList:
            file.write(str(item.timeStamp) + '\t' + str(item.price) + '\n')
        file.close()

class Evaluation:
    def __init__(self,_symbol,_ulPxChange,_yieldRate):
        self.symbol = _symbol
        self.ulPxChange = _ulPxChange
        self.yieldRate = _yieldRate

class PositionInfo:
    def __init__(self,_timeStamp,_capital,_posType):
        self.timeStamp = _timeStamp
        self.capital = _capital
        self.posType = _posType

    @staticmethod
    def printPositionSequence(_positionList,_fileName):
        file = open(_fileName,'wb')
        for item in _positionList:
            file.write(str(item.timeStamp) + '\t' + str(item.capital) + '\t' + item.posType + '\n')
        file.close()

class TradeSignal:
    def __init__(self,_timeStamp,_type,_intensity):
        self.timeStamp = _timeStamp
        self.type = _type           # TradeMeta.POS_*
        self.intensity = _intensity # (0,1], indicate the confidence, to be used later

    @staticmethod
    def printTradeSignalSequence(_tradeSignals,_fileName):
        file = open(_fileName,'wb')
        for item in _tradeSignals:
            file.write(str(item.timeStamp) + '\t' + item.type + '\t' + str(item.intensity) + '\n')
        file.close()

    @staticmethod
    def computePositionsWithSignalsHelper(_timePriceList,_signal,_indexOfSignal,_lastIndexOfSignal,_lastPos,_lastCapital,_lastPrice,_positionList):
        #update positions till this signal
        capital = _lastCapital
        price = _lastPrice
        for index in range(_lastIndexOfSignal+1,_indexOfSignal+1):
            timePriceItem = _timePriceList[index]
            price = timePriceItem.price
            if _lastPos==TradeMeta.POS_LONG:
                capital = _lastCapital * (_signal.intensity * price / _lastPrice + (1 - _signal.intensity))
            elif _lastPos==TradeMeta.POS_SHORT:
                capital = _lastCapital * (_signal.intensity * _lastPrice / price + (1 - _signal.intensity))
            _positionList.append(PositionInfo(timePriceItem.timeStamp,capital,_lastPos))
        #trade on this signal
        return (_indexOfSignal,_signal.type,capital,price)
        
        
        
    @staticmethod
    def computePositionsWithSignals(_timePriceList,_tradeSignals):
        #simply assume timestamps in _tradeSignals is within those in _timePriceList
        timeStamps = []
        for item in _timePriceList:
            timeStamps.append(item.timeStamp)
        positionList = []
        length = len(timeStamps)
        if length > 0:
            lastCapital = 1
            lastPos = TradeMeta.POS_CLOSE
            lastIndexOfSignal = 0
            lastPrice = _timePriceList[0].price
            positionList.append(PositionInfo(timeStamps[0],lastCapital,lastPos))
            for sig in _tradeSignals:
                try:
                    indexOfSignal = timeStamps.index(sig.timeStamp,lastIndexOfSignal)
                except:
                    print ("Error - signal timestamp out of range: " + sig.timeStamp)
                    indexOfSignal = length - 1
                    break
                (lastIndexOfSignal,lastPos,lastCapital,lastPrice) = TradeSignal.computePositionsWithSignalsHelper(_timePriceList,sig,indexOfSignal,lastIndexOfSignal,lastPos,lastCapital,lastPrice,positionList)
            if lastIndexOfSignal < length - 1:
                #fake a last signal
                indexOfSignal = length - 1
                fakeSignal = TradeSignal(timeStamps[indexOfSignal],TradeMeta.POS_CLOSE,1)
                TradeSignal.computePositionsWithSignalsHelper(_timePriceList,fakeSignal,indexOfSignal,lastIndexOfSignal,lastPos,lastCapital,lastPrice,positionList)
        return positionList
        

class PriceProcess:
    @staticmethod
    def calcMovingAvg(_timePriceList,avgRange=5):
        res = []
        if avgRange < 1:
            avgRange = 5
        elif avgRange == 1:
            res = _timePriceList
        else:
            length = len(_timePriceList)
            sum = 0;
            indexFirstAvg = avgRange - 1
            # set as -1 when list is shorter than the avgRange
            for i in range(min(indexFirstAvg,length)):
                res.append(TimePriceInfo(_timePriceList[i].timeStamp,-1.0))
                sum = sum + _timePriceList[i].price
            # calculate the 1st avg
            if indexFirstAvg < length:
                sum = sum + _timePriceList[indexFirstAvg].price
                avg = sum / avgRange
                res.append(TimePriceInfo(_timePriceList[indexFirstAvg].timeStamp,avg))
                left = 0
                # calculate all avg following (left,right]
                for right in range(indexFirstAvg+1,length):
                    avg = avg + (_timePriceList[right].price - _timePriceList[left].price) / avgRange
                    left = left + 1
                    res.append(TimePriceInfo(_timePriceList[right].timeStamp,avg))
        return res
  
def queryPriceFromDB(database,table,symbol,priceType,start,end):
    try:
        conn = MySQLdb.connect(host=DB_SERVER,user=DB_USER,passwd=DB_PASSWD,port=DB_PORT)
        conn.select_db(database)
        sql = 'select EndTime, ' + priceType + ' from ' + table + ' where symbol = \'' + symbol + '\' and StartTime > \'' + start + '\' and StartTime < \'' + end + '\' limit ' + str(DB_MAX_ROWS)
#        print(sql + ' ...')
        conn.query(sql)
        res = conn.store_result()
        records = res.fetch_row(maxrows=0)
        conn.close()
        timePriceList = []
        for rec in records:
            timePriceList.append(TimePriceInfo(str(rec[0]),rec[1]))
        return timePriceList
    except MySQLdb.Error,e:
        print ("MySQL Error %d: %s" % (e.args[0], e.args[1]))
    return []

class ExRightsData:
    s_allExRights = dict() # symobl -> (date -> ExRightsData instance)
    def __init__(self,_divStock,_divCash,_allotShr,_allotPx):
        self.divStock = _divStock
        self.divCash = _divCash
        self.allotShr = _allotShr
        self.allotPx = _allotPx

    def restoreRatio(self,_closePx):
        ratio = 1.0
        if _closePx > 0:
            exRightsPx = (_closePx - self.divCash/10.0 + self.allotPx*self.allotShr/10.0) / (1 + self.divStock/10.0 + self.allotShr/10.0)
            if exRightsPx > 0:
                ratio = _closePx / exRightsPx
        return ratio

    @staticmethod
    def getExRightsDataInSpan(_symbol,_start,_end):
        if len(ExRightsData.s_allExRights) == 0:
            #read ExRightsData from file
            file = open('ExRightsData.txt')
            exRightsItems = stripNewLine(file.readlines())
            for item in exRightsItems:
                (sym,date,divStock,allotShr,allotPx,divCash) = item.split('\t')
                #convert date format from 'yyyymmdd' to 'yyyy-mm-dd'
                date = datetime.strptime(date,'%Y%m%d').strftime('%Y-%m-%d')
                exRightsObj = ExRightsData(float(divStock),float(divCash),float(allotShr),float(allotPx))
                if sym in ExRightsData.s_allExRights:
                    ExRightsData.s_allExRights[sym][date] = exRightsObj
                else:
                    exRightsSym = dict()
                    exRightsSym[date] = exRightsObj
                    ExRightsData.s_allExRights[sym] = exRightsSym
        # return the ExRights dictionary for this symbol in the span
        exRigtsDict = dict()
        checkStart = len(_start)>0
        checkEnd = len(_end)>0
        if _symbol in ExRightsData.s_allExRights:
            for (date,exRights) in ExRightsData.s_allExRights[_symbol].items():
                if (checkStart and date < _start) or (checkEnd and date >=_end):
                    continue
                exRigtsDict[date] = exRights
        return exRigtsDict

    @staticmethod
    def printExRights(_exRightsDict):
        print("Date\t\tDivStock\tDivCash\tallotShares\tallotPx")
        datesExRights = list(_exRightsDict.keys())
        datesExRights.sort()
        for date in datesExRights:
            exRights = _exRightsDict[date]
            print (date + '\t' + str(exRights.divStock) + '\t' + str(exRights.divCash) + '\t' + str(exRights.allotShr) + '\t' + str(exRights.allotPx))

    @staticmethod
    def restoreRights(_symbol,_timePriceList,_orientation=TradeMeta.RESTORE_RIGHTS_FORWARD):
        #suppose timestamps in the input list in sorted ascendingly
        length = len(_timePriceList)
        if length > 1:
            dateList = []
            for item in _timePriceList:
                dateList.append(datetime.strptime(item.timeStamp,'%Y-%m-%d %H:%M:%S').date().isoformat())
            startDate = dateList[0]
            endDate = (datetime.strptime(dateList[length - 1],'%Y-%m-%d') + timedelta(days=1)).date().isoformat()
            exRightsDict = ExRightsData.getExRightsDataInSpan(_symbol,startDate,endDate)
            datesExRights = list(exRightsDict.keys())
            datesExRights.sort()
            #restore rights one by one in the normal time sequence
            startIndex = 0
            for exDate in datesExRights:
                #calculate restoreRatio:
                indexOfExDate = biSearch_firstLargerOrEqual(dateList,exDate,startIndex)
                if indexOfExDate < 0:
                    print('ERROR: EXRight date not in range: ' + exDate)
                    return
                startIndex = indexOfExDate + 1
                exRights = exRightsDict[exDate]
                if indexOfExDate > 0:
                    ratio = exRights.restoreRatio(_timePriceList[indexOfExDate-1].price)
                    #restore rights before this exRightsDate
                    if _orientation==TradeMeta.RESTORE_RIGHTS_FORWARD:
                        for i in range(0,indexOfExDate):
                            _timePriceList[i].price = _timePriceList[i].price / ratio
                    elif _orientation==TradeMeta.RESTORE_RIGHTS_BACKWARD:
                        for i in range(indexOfExDate,length):
                            _timePriceList[i].price = _timePriceList[i].price * ratio