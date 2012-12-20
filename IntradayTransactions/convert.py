import os
import fnmatch
import re

g_xlsfile = fnmatch.translate('*.xls')
g_dir1=''
g_dir2=''
g_lines = 0 # count how many lines written for a symbol

def load_merge_data(filename): 
    f = open(filename, 'rt') 
    lns = f.readlines() 
    f.close() 
    ax = [] 
    for ln in lns: 
        ax.append(ln.split()) 
    return sorted(ax, key=lambda t:t[1]) 
 
def load_raw_data(filename): 
    f = open(filename, 'rt') 
    lns = f.readlines() 
    f.close();
    if len(lns)<5 :
        return False
    ax = [] 
    for ln in lns[1:]: 
        (t,p,d,v,a,m)=ln.decode('gbk').split('\t') 
        if m.startswith(u'买') : m=1 
        elif m.startswith(u'卖') : m=-1 
        elif m.startswith(u'中') : m=0 
        ax.append((t.encode(), float(p), int(v), int(a), m)) 
    return sorted(ax, key=lambda t:t[0]) 
 
def sum2(data, col): 
    sum = 0.0 
    for value in data: 
        sum += value[col] 
    return sum 
 
def stats(data): 
    if (len(data)==1):
        return (data[0],0)
    mean = sum(data) / len(data) 
    ax = 0.0 
    for value in data: 
        ax += (value - mean)**2 
    variance = ax/(len(data)-1) 
    return (mean, variance) 
 
def merge(raw_filename, merge_filename): 
    rdata = load_raw_data(raw_filename)
    if not rdata:
        return False
    mdata = load_merge_data(merge_filename) 
    ax = []
    v_price_close = -1
    for mrange in map(lambda x:(x,x+1), range(0,len(mdata)-1)): 
        t1 = mdata[mrange[0]][1] 
        t2 = mdata[mrange[1]][1]
        subdata = filter(lambda t:t1<t[0]<=t2, rdata) 
        # Start merge 
        # subdata: [(time, price, volume, amount, mode),...] 
        slen = len(subdata) 
        if (0<slen): 
            v_price_open = subdata[0][1] 
            v_price_close = subdata[slen-1][1]
            price_data = map(lambda t:t[1], subdata) 
            v_price_min = min(price_data) 
            v_price_max = max(price_data) 
            (v_price_mean, v_price_var) = stats(price_data) 
            v_volume_sum = sum2(subdata,2) 
            v_amount_sum = sum2(subdata,3) 
        elif v_price_close < 0:
            # no close price got yet, jump to next period
            continue
        else:
            # just keep the last close as the open and close of this period
            v_price_open = v_price_close
            v_price_min = v_price_max = v_price_mean = v_price_close
            v_price_var = 0.0
            v_volume_sum = 0
            v_amount_sum = 0

        ax.append((mdata[mrange[0]][0], 
                   mdata[mrange[1]][0], 
                   v_price_open, 
                   v_price_close, 
                   v_price_min, 
                   v_price_max, 
                   v_price_mean, 
                   v_price_var, 
                   v_volume_sum, 
                   v_amount_sum)) 
            
    return ax 
 
# 
def handle_file(xlsname, outFile):
    global g_lines
    (a, b) = os.path.split(xlsname)
    b = b.split('.')[0]
    (sym, d)=b.split('_')
    result_am = merge(xlsname, "convert_template_am5min.txt")
    if not result_am:
        return False
    result_pm = merge(xlsname, "convert_template_pm5min.txt")
    if not result_pm:
        return False
    for i in result_am:
        #   (sz300001,2001-01-05 09:30:00,2001-01-05 09:40:00,30.0,30.0,30.0,30.0,30.0,30.0,1000,10000;)
        t1 = '%s %s' % (d, i[0])
        t2 = '%s %s' % (d, i[1])
        if g_lines > 0:
            outFile.write('\n')
        msg = "%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%g,%d,%d;" % \
                                                      (sym,   t1,  t2,   i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9])
        outFile.write(msg)
        g_lines = g_lines + 1   
    for i in result_pm:
        # INSERT INTO ohlcquotation VALUES
        #   ('sz300001','2001-01-05 09:30:00','2001-01-05 09:40:00', 30.0, 30.0, 30.0, 30.0, 30.0, 30.0, 1000, 10000 )
        t1 = '%s %s' % (d, i[0])
        t2 = '%s %s' % (d, i[1])
        if g_lines > 0:
            outFile.write('\n')
        msg = "%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%g,%d,%d;" % \
                                                      (sym,   t1,  t2,   i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9])
        outFile.write(msg)
        g_lines = g_lines + 1
    return True
    
def handle_symbols_folder(start_root):
    global g_lines
    fullroot = os.path.abspath(start_root)
    for root, dirs, files in os.walk(start_root):
        #check if we are in a symbol folder
        if len(files) > 0 and len(dirs) == 0:
            (symPath, symbol) = os.path.split(root)
            symFileAbsPath = os.path.join(g_dir2,symbol+'.sql')
            (symFileDir, symFileName) = os.path.split(symFileAbsPath)
            if not os.path.exists(symFileDir):
               os.makedirs(symFileDir)            
            f = open(symFileAbsPath, 'wt')
            g_lines = 0
            for filename in files:
                if re.match(g_xlsfile, filename):
                    #print os.path.join(root, filename)
                    fullname = os.path.join(root, filename)
                    if not handle_file(fullname,f):
                        print '[F]' + fullname
                    else:
                        print '[T]' + fullname
            f.close()
            # post process
            if g_lines == 0:
                #rename file
                os.rename(symFileAbsPath,os.path.join(symFileDir,symFileName+'ERROR'))
#
import sys
if (len(sys.argv)==3): 
    #result = merge(sys.argv[1], sys.argv[2]) 
    #FORMAT OUTPUT 
    #for i in result: 
    #    print '[%s-%s] (%.2f,%.2f,%.2f,%.2f,%.2f,%g,%d,%d)'%i
    g_dir1 = os.path.abspath(sys.argv[1])
    g_dir2 = os.path.abspath(sys.argv[2])
    if os.path.exists(g_dir1):
        handle_symbols_folder(sys.argv[1])
    g_dir1 = ''
    g_dir2 = ''
elif (len(sys.argv)==2):
    handle_symbols_folder(sys.argv[1],'.')
else: 
    print 'Usage: convert <raw_data_filename> <time_template>' 

#test
#os.system('convert "convert_test_sh600219_2012-12-06.xls" "convert_template_am5min.txt"') 

