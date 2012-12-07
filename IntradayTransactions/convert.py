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
    mean = sum(data) / len(data) 
    ax = 0.0 
    for value in data: 
        ax += (value - mean)**2 
    variance = ax/(len(data)-1) 
    return (mean, variance) 
 
def merge(raw_filename, merge_filename): 
    rdata = load_raw_data(raw_filename) 
    mdata = load_merge_data(merge_filename) 
    ax = [] 
    for mrange in map(lambda x:(x,x+1), range(0,len(mdata)-1)): 
        t1 = mdata[mrange[0]][1] 
        t2 = mdata[mrange[1]][1] 
        subdata = filter(lambda t:t1<t[0]<=t2, rdata) 
        # Start merge 
        # subdata: [(time, price, volumn, amount, mode),...] 
        slen = len(subdata) 
        if (0<slen): 
            v_price_open = subdata[0][1] 
            v_price_close = subdata[slen-1][1] 
        price_data = map(lambda t:t[1], subdata) 
        v_price_min = min(price_data) 
        v_price_max = max(price_data) 
        (v_price_mean, v_price_var) = stats(price_data) 
        v_volumn_sum = sum2(subdata,2) 
        v_amount_sum = sum2(subdata,3) 
        ax.append((mdata[mrange[0]][0], 
                   mdata[mrange[1]][0], 
                   v_price_open, 
                   v_price_close, 
                   v_price_min, 
                   v_price_max, 
                   v_price_mean, 
                   v_price_var, 
                   v_volumn_sum, 
                   v_amount_sum)) 
    return ax 
 
# 
import os 
import sys 
if (len(sys.argv)==3): 
    result = merge(sys.argv[1], sys.argv[2]) 
    #FORMAT OUTPUT 
    for i in result: 
        print '[%s-%s] (%.2f,%.2f,%.2f,%.2f,%.2f,%g,%d,%d)'%i 
elif (len(sys.argv)==2 and sys.argv[1]=='test'): 
    os.system('convert "convert_test_sh600219_2012-12-06.xls" "convert_template_am5min.txt"') 
else: 
    print 'Usage: convert <raw_data_filename> <time_template>' 
 
 