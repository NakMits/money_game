import time

import numpy as np
import python_bitbankcc

from bitbank import config
from bitbank.const import PAIR, ORDER, RATE, INTERVAL, CHANGERATE, TRADERULE, TRYNUM
from bitbank.record import Record, CSV
from cmn.log import get_logger

logger = get_logger(modname=__name__, is_debug=config.IS_DEBUG)
pub = python_bitbankcc.public()


class Trade:

    def __init__(self, pair: PAIR, rule: TRADERULE, is_rial: bool = False):
        self.pair = pair
        self.rule = rule
        self.is_rial = is_rial

        if is_rial:
            file_name = f'【{rule.value}】{self.pair.value}.csv'
        else:
            file_name = f'【{rule.value}】{self.pair.value}（simul）.csv'

        self.record = Record(file_name=file_name)

        # TODO: 現在の資産取得
        if self.is_rial:
            pass
        else:
            # 売却中で前回終了していた場合
            if self.record.csv.monitoring_line:
                assets = CSV.get_column_value(line=self.record.csv.monitoring_line, col=CSV.COlUMN.ASSETS)
            # 初回実行の場合
            elif len(self.record.csv.lines) == 1:
                assets = config.SIMUL_INIT_ASSETS
            # 売却済みで前回終了していた場合
            else:
                assets = CSV.get_column_value(line=self.record.csv.lines[-1], col=CSV.COlUMN.ASSETS)
        self.assets = assets

    def trade(self):
        # TODO: 未約定の注文取消し
        if self.is_rial:
            pass
        logger.info("【自動売買開始】")
        if self.record.csv.monitoring_line:
            logger.info("前回売却できていない建玉を売却します。")
            volume, profit_price, stop_loss_price = self.record.get_sell_info()
            self.sell(volume=volume, profit_price=profit_price, stop_loss_price=stop_loss_price)
        while True:
            logger.info(f'資産: {self.assets}  勝率: {self.record.get_win_rate()}')
            self.buy()
            volume, profit_price, stop_loss_price = self.record.get_sell_info()
            logger.debug(
                f'利確ライン: {profit_price}  損切ライン： {stop_loss_price}  価格差： {int(profit_price) - int(stop_loss_price)}')
            self.sell(volume=volume, profit_price=profit_price, stop_loss_price=stop_loss_price)

    def judge_should_buy(self, rule: TRADERULE):
        should_buy = False
        buy_info = None

        if rule == TRADERULE.WITHIN_DIFFRATE:
            depth = pub.get_depth(self.pair.value)
            if self.within_diff_rate(depth):
                change_rate = CHANGERATE.MIN.value
                price = str(int(depth['bids'][0][0]) + 1)
                volume = self.generate_volume(price=price)
                buy_info = [price, volume, change_rate]
                should_buy = True

        elif rule == TRADERULE.WITHOUT_DIFFRATE:
            depth = pub.get_depth(self.pair.value)
            if self.without_diff_rate(depth):
                change_rate = CHANGERATE.MIN.value
                price = str(int(depth['bids'][0][0]) + 1)
                volume = self.generate_volume(price=price)
                buy_info = [price, volume, change_rate]
                should_buy = True

        return should_buy, buy_info

    def buy(self, interval: int = INTERVAL.MIN.value):
        try_count = 0
        while True:
            if try_count > TRYNUM.BUY.value:
                logger.error(f'購入挑戦回数超過: {try_count} > {TRYNUM.BUY.value}')
                # raise Exception
            logger.debug("購入条件監視中・・・")

            # 購入条件に一致した場合
            should_buy, buy_info = self.judge_should_buy(rule=self.rule)
            if should_buy:
                logger.debug("購入条件一致！")
                price, volume, change_rate = buy_info
                # 購入
                executed_at = self.limit_order(order=ORDER.BUY, price=price, volume=volume)
                try_count += 1
                # 成功した場合
                if executed_at:
                    self.assets = str(int(self.assets) - round(int(price) * volume))
                    self.record.buy(price=price,
                                    volume=volume,
                                    executed_at=executed_at,
                                    try_num=try_count,
                                    change_rate=change_rate,
                                    assets=self.assets)
                    logger.debug(f'購入挑戦回数: {try_count}')
                    return
            time.sleep(interval)

    def sell(self, volume: float, profit_price: str, stop_loss_price: str,
             interval: int = INTERVAL.MIN.value):
        try_count = 0
        while True:
            if try_count > TRYNUM.SELL.value:
                logger.error(f'売却挑戦回数超過: {try_count} > {TRYNUM.BUY.value}')
                # raise Exception
            logger.debug("売却条件監視中・・・")
            need_order = False
            price = None

            depth = pub.get_depth(self.pair.value)
            ask_price = self.get_mean_by_limit_orders(depth['asks'], size=3)
            bid_price = self.get_mean_by_limit_orders(depth['bids'], size=3)
            # 利確ラインを超えていたら
            if ask_price > int(profit_price):
                logger.debug("利確ライン到達！")
                price = str(int(depth['asks'][0][0]) - 1)
                need_order = True
            # 損切りラインを割ったら
            elif bid_price < int(stop_loss_price):
                logger.debug("損切ライン到達！")
                price = str(int(depth['bids'][0][0]) + 1)
                need_order = True
            # 注文
            if need_order:
                # 売却
                executed_at = self.limit_order(order=ORDER.SELL, price=price, volume=volume)
                try_count += 1
                # 成功した場合
                if executed_at:
                    # 売却後の資産取得
                    # TODO: APIで資産取得
                    if self.is_rial:
                        pass
                    else:
                        self.assets = str(int(self.assets) + round(int(price) * volume))
                    self.record.sell(price=price, executed_at=executed_at, try_num=try_count, assets=self.assets)
                    logger.debug(f'売却挑戦回数: {try_count}')
                    return
            time.sleep(interval)

    def limit_order(self, order: ORDER, price: str, volume: float, wait: int = INTERVAL.LONG.value * 3):
        # 注文
        # TODO: APIで指値注文
        if self.is_rial:
            pass
        logger.debug("指値注文！")
        time_from = round(time.time() * 1000)
        time.sleep(wait)
        # 売買成立
        if self.is_order_completed(price=price, volume=volume, order=order, time_from=time_from):
            logger.debug("成立！")
            executed_at = round(time.time() * 1000)
            return executed_at
        # 売買不成立
        else:
            logger.debug("不成立！")
            # 注文取消し
            # TODO: APIで注文取消
            if self.is_rial:
                pass
            logger.debug("注文取消！")
            executed_at = None
            return executed_at

    def is_order_completed(self, price: str, volume: float, order: ORDER, time_from: int = None):
        # return True
        is_completed = False
        completed_volume = 0
        if time_from is None:
            time_from = round(time.time() * 1000)
        # TODO: APIで売買成立を確認
        if self.is_rial:
            pass
        else:
            transactions = pub.get_transactions(pair=self.pair.value)['transactions']
            for transaction in transactions:
                if transaction['executed_at'] <= time_from:
                    continue
                if (order == ORDER.SELL and int(transaction['price']) >= int(price)) or (
                        order == ORDER.BUY and int(transaction['price']) <= int(price)):
                    completed_volume += float(transaction['amount'])
            if completed_volume >= volume:
                is_completed = True
            else:
                is_completed = False
        return is_completed

    def generate_volume(self, price: str, assets_rate: float = 1.0):
        return round(round(int(assets_rate * int(self.assets)) / int(price), RATE.ROUND_DIGITS.value + 1),
                     RATE.ROUND_DIGITS.value)

    @staticmethod
    def within_diff_rate(depth, limit: float = 0.0005, size: int = 3):
        ask_price = Trade.get_mean_by_limit_orders(depth['asks'], size=size)
        bid_price = Trade.get_mean_by_limit_orders(depth['bids'], size=size)
        diff = ask_price - bid_price
        diff_rate = diff / ask_price
        if diff_rate <= limit:
            return True
        else:
            return False

    @staticmethod
    def without_diff_rate(depth, limit: float = 0.0005, size: int = 3):
        ask_price = Trade.get_mean_by_limit_orders(depth['asks'], size=size)
        bid_price = Trade.get_mean_by_limit_orders(depth['bids'], size=size)
        diff = ask_price - bid_price
        diff_rate = diff / ask_price
        if diff_rate >= limit:
            return True
        else:
            return False

    @staticmethod
    def generate_best_change_rate(win_rate: float):
        best_change_rate = round((win_rate - 0.5) * 2, RATE.ROUND_DIGITS.value)
        return best_change_rate

    @staticmethod
    def get_mean_by_limit_orders(limit_orders, size: int = 3):
        # 価格と量をそれぞれ抽出してリスト化
        price_list = []
        volume_list = []
        for order in limit_orders[0:size]:
            price_list.append(int(order[0]))
            volume_list.append(float(order[1]))
        # 量を比率に変換したリストを作成
        weight_list = []
        for volume in volume_list:
            weight_list.append(volume / sum(volume_list))
        # 加重平均を計算して返却
        return round(np.average(a=price_list, weights=weight_list))


def main():
    trade = Trade(pair=PAIR.BTC_JPY, rule=TRADERULE.WITHOUT_DIFFRATE, is_rial=False)
    trade.trade()


if __name__ == '__main__':
    main()
