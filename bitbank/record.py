import csv
import os
from copy import copy
from enum import Enum

from bitbank import config
from bitbank.const import RATE
from cmn.log import get_logger

logger = get_logger(modname=__name__, is_debug=config.IS_DEBUG)


class Record:

    def __init__(self, file_name: str = 'record.csv'):
        self.csv = CSV(file_name=file_name)

    def buy(self, volume: float, price: str, try_num: int, executed_at: int, change_rate: float, assets: str):
        cols = {
            CSV.COlUMN.VOLUME: volume,
            CSV.COlUMN.BUY_PRICE: price,
            CSV.COlUMN.BUY_AT: executed_at,
            CSV.COlUMN.BUY_TRY_NUM: try_num,
            CSV.COlUMN.BEST_CHANGE_RATE: change_rate,
            CSV.COlUMN.ASSETS: assets,
            CSV.COlUMN.STATUS: CSV.STATUS.MONITORING.value,
        }
        self.csv.monitoring_line = CSV.generate_line(cols=cols)

    def sell(self, price: str, executed_at: int, try_num: int, assets: str):
        if not self.csv.monitoring_line:
            logger.error('「monitoring_line」が設定されていません。')

        buy_price = CSV.get_column_value(line=self.csv.monitoring_line, col=CSV.COlUMN.BUY_PRICE)
        volume = CSV.get_column_value(line=self.csv.monitoring_line, col=CSV.COlUMN.VOLUME)
        price_diff = int(price) - int(buy_price)
        pl = int(price_diff * volume)
        change_rate = round((int(price) / int(buy_price) - 1), RATE.ROUND_DIGITS.value)
        logger.info(f'損益: {pl}  増減率: {change_rate}')
        cols = {
            CSV.COlUMN.SELL_PRICE: price,
            CSV.COlUMN.SELL_AT: executed_at,
            CSV.COlUMN.SELL_TRY_NUM: try_num,
            CSV.COlUMN.RESULT_CHANGE_RATE: change_rate,
            CSV.COlUMN.PL: pl,
            CSV.COlUMN.ASSETS: assets,
            CSV.COlUMN.STATUS: CSV.STATUS.CLOSED.value,
        }
        self.csv.lines.append(CSV.generate_line(cols=cols, src_line=self.csv.monitoring_line))
        self.csv.monitoring_line = None

    def get_sell_info(self, line=None):
        if not line:
            line = self.csv.monitoring_line
        buy_price = CSV.get_column_value(line=line, col=CSV.COlUMN.BUY_PRICE)
        volume = CSV.get_column_value(line=line, col=CSV.COlUMN.VOLUME)
        change_rate = CSV.get_column_value(line=line, col=CSV.COlUMN.BEST_CHANGE_RATE)
        profit_price = str(int(int(buy_price) * (1 + change_rate)))
        stop_loss_price = str(int(int(buy_price) * (1 - change_rate)))
        return volume, profit_price, stop_loss_price

    def get_win_rate(self, size: int = None, min_win_rate: float = 0):
        win_rate = 0
        use_min_win_rate = False

        trade_count = 0
        win_count = 0
        lose_count = 0
        zero_count = 0

        if size:
            # 指定されたサイズより履歴がある場合は指定されたサイズ分の最新履歴を対象とする
            if len(self.csv.lines) - 1 >= size:
                lines = self.csv.lines[-size:]
            # 指定されたサイズより履歴がない場合は最低勝率を採用（存在する全履歴の勝率は算出できるようにする）
            else:
                lines = self.csv.lines[1:]
                logger.warning(f'勝率計算サンプル数不足: {len(lines)} / {size}')
                use_min_win_rate = True
        else:
            lines = self.csv.lines[1:]

        # 取引回数、勝敗をカウント
        for line in lines:
            trade_count += 1
            result_change_rate = CSV.get_column_value(line=line, col=CSV.COlUMN.RESULT_CHANGE_RATE)
            if float(result_change_rate) == 0:
                zero_count += 1
            elif float(result_change_rate) > 0:
                win_count += 1
            elif float(result_change_rate) < 0:
                lose_count += 1

        # 取引がない場合は最低勝率を採用
        if trade_count == 0:
            logger.debug(f'取引履歴なし')
            use_min_win_rate = True
        else:
            # 勝ちがない場合
            if win_count == 0:
                win_rate = 0
            else:
                # 勝率計算
                win_rate = round(win_count / (trade_count - zero_count), RATE.ROUND_DIGITS.value)
            # 勝率が最低勝率より低い場合は最低勝率を採用
            if win_rate < min_win_rate:
                logger.warning(f'最低勝率以下: {win_rate} < {min_win_rate}')
                use_min_win_rate = True

        # 最低勝率の採用処理
        if use_min_win_rate:
            logger.debug(f'最低勝率を採用: {min_win_rate}')
            win_rate = min_win_rate

        logger.debug(f'増減率合計: {self.get_change_rate_sum(size=size)}')

        return win_rate

    def get_change_rate_sum(self, size: int):
        if len(self.csv.lines) - 1 < 1:
            logger.debug(f'取引履歴なし')
            return 0
        result_change_rate_list = []
        if size:
            # 指定されたサイズより履歴がある場合は指定されたサイズ分の最新履歴を対象とする
            if len(self.csv.lines) - 1 >= size:
                lines = self.csv.lines[-size:]
            # 指定されたサイズより履歴がない場合は存在する全履歴を対象
            else:
                lines = self.csv.lines[1:]
                logger.warning(f'増減率合計サンプル数不足: {len(lines)} / {size}')
        else:
            lines = self.csv.lines[1:]
        for line in lines:
            result_change_rate = CSV.get_column_value(line=line, col=CSV.COlUMN.RESULT_CHANGE_RATE)
            result_change_rate_list.append(float(result_change_rate))

        return round(sum(result_change_rate_list), RATE.ROUND_DIGITS.value)


class CSV:
    class COlUMN(Enum):
        VOLUME = ['VOLUME', float]
        BUY_PRICE = ['BUY_PRICE', str]
        BUY_AT = ['BUY_AT', int]
        BUY_TRY_NUM = ['BUY_TRY_NUM', int]
        SELL_PRICE = ['SELL_PRICE', str]
        SELL_AT = ['SELL_AT', int]
        SELL_TRY_NUM = ['SELL_TRY_NUM', int]
        BEST_CHANGE_RATE = ['BEST_CHANGE_RATE', float]
        RESULT_CHANGE_RATE = ['RESULT_CHANGE_RATE', float]
        PL = ['PL', str]
        ASSETS = ['ASSETS', str]
        STATUS = ['STATUS', str]

    class STATUS(Enum):
        MONITORING = 'MONITORING'
        CLOSED = 'CLOSED'

    COLUMNS = []
    for column in COlUMN:
        COLUMNS.append(column)
    del column

    def __init__(self, file_name: str = 'record.csv'):
        self.file_name = file_name
        self.lines = self.read_lines()
        self.monitoring_line = ''

        # 前回処理途中だった場合の考慮
        last_line = copy(self.lines[-1])
        if last_line and CSV.get_column_value(line=last_line, col=CSV.COlUMN.STATUS) == CSV.STATUS.MONITORING.value:
            self.monitoring_line = last_line
            del self.lines[-1]
            logger.warning("前回売却できずに終了しています。")

        self.f = open(file=self.file_name, newline='', mode='w')
        self.writer = csv.writer(self.f)

    def __del__(self):
        self.writer.writerows(self.lines)
        if self.monitoring_line:
            self.writer.writerow(self.monitoring_line)
        self.f.close()

    def read_lines(self):
        if not os.path.exists(self.file_name):
            self.create()

        with open(file=self.file_name, mode='r') as f:
            reader = csv.reader(f)
            lines = []
            for i, line in enumerate(reader):
                if line:
                    lines.append(line)
        return lines

    def create(self):
        with open(file=self.file_name, mode='w') as f:
            writer = csv.writer(f)
            line = self.generate_new_line()
            for column in self.COLUMNS:
                col_name, _ = column.value
                line[self.COLUMNS.index(column)] = col_name
            writer.writerow(line)

    @classmethod
    def generate_new_line(cls):
        line = [''] * len(cls.COlUMN)
        return line

    @classmethod
    def get_column_value(cls, line: list, col: COlUMN):
        value = line[cls.COLUMNS.index(col)]
        _, col_type = col.value
        return col_type(value)

    @classmethod
    def generate_line(cls, cols: dict, src_line: list = None):
        if src_line:
            line = copy(src_line)
        else:
            line = cls.generate_new_line()
        for col, value in cols.items():
            line[cls.COLUMNS.index(col)] = value
        return line
