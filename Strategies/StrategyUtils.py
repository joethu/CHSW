import ConfigParser
import MySQLdb

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
        print(sql + ' ...')
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

