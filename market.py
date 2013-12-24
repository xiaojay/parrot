#coding=utf-8
from utils import trunc
import jsonrpclib

RIPPLED_SERVER = 'http://s1.ripple.com:51234'
ISSUER_RIPPLECN = 'rnuF96W4SZoCJmbHYBFoJZpR8eCaxNvekK'

class Market(object):
    def __init__(self, issuer=ISSUER_RIPPLECN, rippled=RIPPLED_SERVER):
        self.issuer = issuer
        self.server = jsonrpclib.Server(RIPPLED_SERVER)
    
    def add_private_info(self, address, secret=''):
        self.address = address
        self.secret = secret
    
    def get_balance(self):
        params = {'account':self.address}
        xrp_balance = self.server.account_info(params)['account_data']['Balance']
        xrp_balance = trunc(float(xrp_balance)/1000000)
        r = self.server.account_lines(params)
        for line in r['lines']:
            if line['account'] == self.issuer:
                cny_balance = line['balance']
                cny_balance = trunc(float(cny_balance))
        return {'xrp':xrp_balance, 'cny':cny_balance}
    
    def buy(self, price, amount):
        value = str(trunc(price*amount,2) + 0.01)
        gets = {'currency': 'CNY','issuer': self.issuer, 'value': value}
        params = {'secret':self.secret, 
                  'tx_json': {'TransactionType':'OfferCreate', 'Account':self.address,'TakerGets':gets, "TakerPays": str(amount*1000000)}}
        return self.server.submit(params)
    
    def sell(self, price, amount):
        value = str(trunc(price*amount,2) - 0.01)
        pays = {'currency': 'CNY','issuer': self.issuer, 'value': value}
        params = {'secret':self.secret, 
                  'tx_json': {'TransactionType':'OfferCreate', 'Account':self.address,'TakerGets':str(amount*1000000), "TakerPays":pays}}
        return self.server.submit(params)

    def get_depth(self):
        ask_params = {'taker_pays':{'currency':'CNY', 'issuer':self.issuer}, 'taker_gets':{'currency':'XRP'}}
        asks = self.server.book_offers(ask_params)
        bid_params =  {'taker_pays':{'currency':'XRP'}, 'taker_gets':{'currency':'CNY', 'issuer':self.issuer}}
        bids = self.server.book_offers(bid_params)
        return self.format_depth(bids, asks)
    
    def sort_and_format(self, l, reverse=False):
        l.sort(key=lambda x: float(x[0]), reverse=reverse)
        r = []
        for i in l:
            r.append({'price': float(i[0]), 'amount': float(i[1])})
        return r
 
    def format_depth(self, biddepth, askdepth):
        bids = []
        for bid in biddepth['offers']:
            takerpays = bid['TakerPays']
            takergets = bid['TakerGets']['value']
            if 'taker_pays_funded' in bid:
                takerpays = bid['taker_pays_funded']
            if 'taker_gets_funded' in bid:
                takergets = bid['taker_gets_funded']['value']
            takerpays = float(takerpays)/1000000
            takergets = float(takergets)
            rate = trunc(takergets/takerpays)
            bids.append([rate, trunc(takerpays)])
        bids = self.sort_and_format(bids, True)
        
        asks = []
        for ask in askdepth['offers']:
            takerpays = ask['TakerPays']['value']
            takergets = ask['TakerGets']
            if 'taker_pays_funded' in ask:
                takerpays = ask['taker_pays_funded']['value']
            if 'taker_gets_funded' in ask:
                takergets = ask['taker_gets_funded']
            takerpays = float(takerpays)
            takergets = float(takergets)/1000000
            rate = trunc(takerpays / takergets)
            asks.append([rate, trunc(takergets)])
        asks = self.sort_and_format(asks, False)
        return {'asks': asks, 'bids': bids}

if __name__ == '__main__':
    depth = Market().get_depth()
    print u'买单'
    for b in depth['bids'][:10]:
        print b['price'], b['amount']
    print u'卖单'
    for a in depth['asks'][:10]:
        print a['price'], a['amount']
