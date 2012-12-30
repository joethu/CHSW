import StrategyUtils
import os

g_FSMAConfigFastMA = 'fast_ma'
g_FSMAConfigSlowMA = 'slow_ma'
g_FSMAConfigCSMD = 'check_slowma_direction'
g_database = 'chswdata'
g_table = 'ohlcquotation'
g_debug_folder = 'debug'

DEBUG = True
ALLOW_SHORT = False

def FSMA_Init():
    paramList = [g_FSMAConfigFastMA,g_FSMAConfigSlowMA,g_FSMAConfigCSMD]
    return StrategyUtils.readStrategySettings('FSMA',paramList)

def FSMA_CalcDirection(lastPx,currPx,lastDirection):
    diff = currPx - lastPx
    dir = lastDirection
    if diff > 0:
        dir = 1
    elif diff < 0:
        dir = -1
    return dir

def FSMA(data_in, params):
    # calculate moving averages
    slow_ma = int(params[g_FSMAConfigSlowMA])
    fast_ma = int(params[g_FSMAConfigFastMA])
    check_direction = bool(int(params[g_FSMAConfigCSMD]))
    if slow_ma <= fast_ma:
        print ('ERROR Setting: Slow avg range must be larger than Fast!')
        return []
    timePriceList = data_in['data']
    symbol = data_in['symbol']
    print("Running FastSlowMovingAverageLineStrategy on symbol " + symbol)

    slow_ma_list = StrategyUtils.PriceProcess.calcMovingAvg(timePriceList,slow_ma)
    fast_ma_list = StrategyUtils.PriceProcess.calcMovingAvg(timePriceList,fast_ma)
    if DEBUG:
        StrategyUtils.TimePriceInfo.printTimePriceSequence(timePriceList,os.path.join(g_debug_folder,symbol + '.orig.txt'))
        StrategyUtils.TimePriceInfo.printTimePriceSequence(slow_ma_list,os.path.join(g_debug_folder,symbol + '.avg' + str(slow_ma) + '.txt'))
        StrategyUtils.TimePriceInfo.printTimePriceSequence(fast_ma_list,os.path.join(g_debug_folder,symbol + '.avg' + str(fast_ma) + '.txt'))

    tradeSignals = []
    position = StrategyUtils.TradeMeta.POS_CLOSE
    intensity = 1
    lastDiff = 0 #slow - fast
    lastSlow = lastFast = -1 #calc moving direction
    dirSlow = dirFast = 0    #moving direction: +1, 0, -1
    
    for i in range(len(timePriceList)):
        slow_avg = slow_ma_list[i].price
        fast_avg = fast_ma_list[i].price
        if slow_avg > 0 and fast_avg > 0:
            currDiff = fast_avg - slow_avg
            if lastSlow > 0: # ignore the first avg pair
                # update moving direction
                dirSlow = FSMA_CalcDirection(lastSlow,slow_avg,dirSlow)
                dirFast = FSMA_CalcDirection(lastFast,fast_avg,dirFast)
                addSignal = False
                if currDiff > 0:
                    if lastDiff < 0 and (not position == StrategyUtils.TradeMeta.POS_LONG):
                        addSignal = True
                        if not check_direction:
                            if position == StrategyUtils.TradeMeta.POS_SHORT:
                                position = StrategyUtils.TradeMeta.POS_CLOSE
                            elif position == StrategyUtils.TradeMeta.POS_CLOSE:
                                position = StrategyUtils.TradeMeta.POS_LONG
                            else:
                                addSignal = False
                        else:
                            if dirSlow > 0:
                                position = StrategyUtils.TradeMeta.POS_LONG
                            elif position == StrategyUtils.TradeMeta.POS_SHORT:
                                position = StrategyUtils.TradeMeta.POS_CLOSE
                            else:
                                addSignal = False
                    lastDiff = currDiff
                elif currDiff < 0:
                    if lastDiff > 0 and (not position==StrategyUtils.TradeMeta.POS_SHORT):
                        addSignal = True
                        if not check_direction:
                            if position == StrategyUtils.TradeMeta.POS_LONG:
                                position = StrategyUtils.TradeMeta.POS_CLOSE
                            elif position == StrategyUtils.TradeMeta.POS_CLOSE and ALLOW_SHORT:
                                position = StrategyUtils.TradeMeta.POS_SHORT
                            else:
                                addSignal = False
                        else:
                            if dirSlow < 0:
                                if ALLOW_SHORT:
                                    position = StrategyUtils.TradeMeta.POS_SHORT
                                elif position == StrategyUtils.TradeMeta.POS_LONG:
                                    position = StrategyUtils.TradeMeta.POS_CLOSE
                                else:
                                    addSignal = False
                            elif position == StrategyUtils.TradeMeta.POS_LONG:
                                position = StrategyUtils.TradeMeta.POS_CLOSE
                            else:
                                addSignal = False
                    lastDiff = currDiff
                # don't update lastDiff if currDiff = 0
                if addSignal:
                    tradeSignals.append(StrategyUtils.TradeSignal(timePriceList[i].timeStamp,position,intensity))

            lastSlow = slow_avg
            lastFast = fast_avg
    return tradeSignals

def FSMA_symbol(symbol,pxType,start,end,params):
    # fetch data from db
    timePriceList = StrategyUtils.queryPriceFromDB(g_database,g_table,symbol,pxType,start,end)
    print (str(len(timePriceList)) + ' rows retrieved.')
    # go
    data_in_dict = dict()
    data_in_dict['symbol'] = symbol
    data_in_dict['pxType'] = pxType
    data_in_dict['data'] = timePriceList
    data_in_dict['start'] = start
    data_in_dict['end'] = end
    tradeSignals = FSMA(data_in_dict,params)
    if DEBUG:
        StrategyUtils.TradeSignal.printTradeSignalSequence(tradeSignals,os.path.join(g_debug_folder,symbol + '.signal.txt'))
    #evaluate
    positionLists = StrategyUtils.TradeSignal.computePositionsWithSignals(timePriceList,tradeSignals)
    if DEBUG:
        StrategyUtils.PositionInfo.printPositionSequence(positionLists,os.path.join(g_debug_folder,symbol + '.position.txt'))
    return (timePriceList,positionLists)

# read strategy config
#strategy_params = FSMA_Init()
#FSMA_symbol('sz000001','ClosePx','2011-01-01','2012-01-01',strategy_params)

def FSMA_symbols(symbols,pxType,start,end,params):
    evaluations = []
    for sym in symbols:
        (timePriceList,positionLists) = FSMA_symbol(sym,pxType,start,end,params)
        ulPxChange = 0
        yieldRate = 0
        length = len(timePriceList)
        if timePriceList[0].price > 0:
            ulPxChange = timePriceList[length-1].price / timePriceList[0].price - 1
        if positionLists[0].capital > 0:
            yieldRate = positionLists[length-1].capital / positionLists[0].capital - 1
        evaluations.append(StrategyUtils.Evaluation(sym,ulPxChange,yieldRate))
    return evaluations

def FSMA_HS300():
    strategy_params = FSMA_Init()
    file = open('HS300_Sina.txt')
    syms = StrategyUtils.stripNewLine(file.readlines())
    file.close()
    evaluations = FSMA_symbols(syms,'ClosePx','2011-01-01','2012-01-01',strategy_params)
    file = open('HS300_FSMA.txt','wb')
    file.write('Symbol\tUlPxChange\tYieldRate')
    for eval in evaluations:
        file.write('\n' + eval.symbol + '\t' + str(eval.ulPxChange) + '\t' + str(eval.yieldRate))
    file.close()

FSMA_HS300()