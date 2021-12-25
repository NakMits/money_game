import time

import python_bitbankcc

from bitbank import config
from bitbank.const import DIRECTION, INTERVAL, PAIR, ORDER
from bitbank.trade import Trade
from cmn.log import get_logger

logger = get_logger(modname=__name__, is_debug=config.IS_DEBUG)
pub = python_bitbankcc.public()


class Watch:

    @staticmethod
    def reach(pair: PAIR, price: str, time_from: int, direction: DIRECTION, interval: int = 5):
        while True:
            transactions = pub.get_transactions(pair.value)['transactions']
            for transaction in transactions:
                if not transaction['executed_at'] > time_from:
                    continue
                if (direction == DIRECTION.UP and transaction['price'] >= price) or (
                        direction == DIRECTION.DOWN and transaction['price'] <= price):
                    logger.debug(transaction)
                    return True
            time.sleep(interval)

    @staticmethod
    def price_diff(pair: PAIR, size: int = 1, interval: int = INTERVAL.MIN, except_diff_1: bool = True):
        while True:
            depth = pub.get_depth(pair.value)
            ask_price = Trade.get_mean_by_limit_orders(depth['asks'], size=size)
            bid_price = Trade.get_mean_by_limit_orders(depth['bids'], size=size)
            diff = ask_price - bid_price
            diff_rate = '{:.4%}'.format(diff / ask_price)
            if not except_diff_1 or (except_diff_1 and diff > 1):
                logger.info(f'{diff_rate}: {diff}')
            time.sleep(interval)

