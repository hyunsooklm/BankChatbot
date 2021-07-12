import time
import requests
import json
from bs4 import BeautifulSoup as bs
from collections import defaultdict



#TODO 저축기간에 따라(6,12,24,36), 적립 방식에 따라(정액적립,자유적립), 시중은행, 저축은행, 모두냐에 따라
# 분리해서 searching할 수 있는 자료구조 생각

def from_user():
    money = ""
    while True:
        rsrv_type = input('정액 적립식:S 자유 적립식:F 입력하세요:')
        rsrv_type = rsrv_type.upper()
        if rsrv_type == 'S' or rsrv_type == 'F':
            break
        print('적금 방식 재선택 요망')
    if rsrv_type == 'S':
        while True:
            try:
                money,term = map(int,input("월 저축금액, 기간: ").split())
                if money < 0 or term<0:
                    print("돈 기간 정확히 입력")
                else:
                    break
            except ValueError:
                print("돈을 적으라고")
    return rsrv_type, money,term
def interest_cal(money, save_trm, intr_rate, rsrv_type, Tax_type='normal'):
    interest = -1
    rsrv_type=rsrv_type.upper().strip()
    if rsrv_type == 'S':
        # 이자(단리): 월납입금 * n(n+1)/2 * r/12
        origin_interest = money * save_trm * (save_trm + 1) / 2 * (intr_rate / 12)
    elif rsrv_type == 'F':
        # 이자(복리): (월납입금 * (1 + r / 12) * ((1 + r / 12) ** n - 1) / (r / 12)) - (월납입금 * n)
        origin_interest = (money * (1 + intr_rate / 12) * ((1 + intr_rate / 12) ** save_trm - 1) / (intr_rate / 12)) - (money * save_trm)
    if Tax_type == 'normal':
        interest = origin_interest * 0.846
    if Tax_type == 'non_Tax':
        interest = origin_interest
    if Tax_type == 'tax preferential':
        interest = origin_interest * 0.905
    return int(interest)
#사용법: intr=interest_cal(100000,24,0.02,' s ')
if __name__ == "__main__":
    bankset=set()
    intr = interest_cal(100000, 24, 0.02, 'S')
    print('안녕하세요. 적금서비스입니다.')
    rsrv_type,money,term=from_user()
    print(rsrv_type,money)
    auth_key='b555824094d0be01126bc05694f89259'
    bank_code='020000'
    savebank_code='030300'
    loan='030200'
    insurance='050000'
    banking=[bank_code,savebank_code,loan,insurance]
    Total_bank_info=defaultdict(dict)
    num=1
    api_start=time.time()
    for bankkind in banking:    #권역별로 itemlist 따오기
        current_pageNo=1
        while True:
            URL=f'http://finlife.fss.or.kr/finlifeapi/savingProductsSearch.xml?auth={auth_key}&topFinGrpNo={bankkind}&pageNo={current_pageNo}'
            response=requests.get(URL)
            if response.status_code==200:
                soup=bs(response.content,'lxml')
                products=soup.find_all('product')
                max_pageNo=int(soup.find('max_page_no').text)     #max_pageNo
                for p in products:
                    info=p.find('baseinfo')
                    ops=p.find_all('option')         #해당 금융상품에서 option tag로 달린것들
                    for base in info.children:       #baseinfo태그값들
                        if base.name==None:
                            continue
                        Total_bank_info[num][base.name.replace("\n","")]=base.text #base.name은 태그명, base.text는 태그 안 str
                    Total_bank_info[num]['option']=[]
                    for option in ops:
                        sub_opt=dict()
                        for child in option.children:
                            if child.name==None:
                                continue
                            sub_opt[child.name.replace("\n","")]=child.text
                        Total_bank_info[num]['option'].append(sub_opt)
                    num+=1
                if current_pageNo<max_pageNo:     #해당 권역코드의 금융상품 MAX Page에 맞춰 모두 가져오기.
                    current_pageNo+=1
                else:
                    break
            else:
                print('Http error occur!\n')
                break
    api_end=time.time()
    print(f'api따오는데 걸리는 시간:{api_end-api_start} 초')
    i=1
    cal_start=time.time()
    max_intr=-1
    max_item=""
    for n,item in Total_bank_info.items():
        bankset.add(item['kor_co_nm'])
        if item['max_limit'] and int(item['max_limit'])<money:
            continue
        for opt in item['option']:
            if opt['rsrv_type']!=rsrv_type or int(opt['save_trm'])!=term: #적립유형/기간/
                # print(opt['rsrv_type'],rsrv_type,opt['save_trm'],term)
                continue
            print(opt['rsrv_type'],rsrv_type,opt['save_trm'],term)
            intr_rate_type=opt['intr_rate_type']
            save_trm=int(opt['save_trm'])
            intr_rate=float(opt['intr_rate'])/100
            interest=interest_cal(money,save_trm, intr_rate, opt['rsrv_type'])
            if interest>max_intr:
                max_intr=interest
                max_item=(item,opt)
                print(item['fin_prdt_nm'], opt['save_trm'])
            # print(opt)
    cal_end = time.time()
    item=max_item[0]
    opt=max_item[1]
    print(f'쓰는데 {cal_end-cal_start}초 걸립니다. ' )
    print(f'''최적의 아이템은 {item["kor_co_nm"]}의 {item["fin_prdt_nm"]} 금리는 {opt["intr_rate_type"]} {opt["intr_rate"]} 이자는 {max_intr}, 기간:{opt["save_trm"]} '
          월 최대한도:{item["max_limit"]}''')
    print(len(bankset))
    print(bankset)
    # print(interest_cal(money,12, 0.02200000000002, 's'))
    # money, save_trm, intr_rate, rsrv_type, Tax_type='normal'):