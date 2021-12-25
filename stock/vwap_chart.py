import os
import re

import pandas as pd
import mplfinance as mpf

from cmn.log import get_logger

logger = get_logger(modname=__name__, is_debug=True)


def plot(stock_code: str):

    # SBI証券から取得した時系列csv
    sbi_timechart_csv = os.path.join('sbi_timechart_csv', stock_code + '.csv')
    # 過去に出力したcsv（調整済み）
    mplf_csv = os.path.join('mplf_csv', stock_code + '.csv' + '.mplf')

    # 過去に調整済みのcsvがあればそこから読み込み
    if os.path.isfile(mplf_csv):
        df = pd.read_csv(mplf_csv, index_col=0, parse_dates=[0], encoding="SHIFT-JIS")
        df = df.sort_index(ascending=True)
    # なければ元ファイルを読み込んで調整
    elif os.path.isfile(sbi_timechart_csv):
        df = pd.read_csv(sbi_timechart_csv, index_col=0, encoding="SHIFT-JIS", usecols=[0, 1, 2, 3, 4, 8, 9])
        df = df.sort_index(ascending=True)
        # mplf用の必須column調整
        df["Date"] = pd.to_datetime(df.index.values, format='%Y%m%d')
        df = df.set_index("Date")
        df = df.rename(columns={'始値': 'Open', '高値': 'High', '安値': 'Low', '終値': 'Close', '出来高': 'Volume'})
        # 独自の値を計算して列追加
        tradingprice_list = []
        vwap_5_list = []
        vwap_25_list = []
        vwap_75_list = []
        for i, (vwap, volume) in enumerate(zip(df['VWAP'], df['Volume'])):
            tradingprice_list.append(vwap * volume)
            vwap_5 = sum(tradingprice_list[max(i - 4, 0):i + 1]) / sum(df['Volume'][max(i - 4, 0):i + 1])
            vwap_25 = sum(tradingprice_list[max(i - 24, 0):i + 1]) / sum(df['Volume'][max(i - 24, 0):i + 1])
            vwap_75 = sum(tradingprice_list[max(i - 74, 0):i + 1]) / sum(df['Volume'][max(i - 74, 0):i + 1])
            if i + 1 < 5:
                vwap_5_list.append(None)
                vwap_25_list.append(None)
                vwap_75_list.append(None)
            elif i + 1 < 25:
                vwap_5_list.append(vwap_5)
                vwap_25_list.append(None)
                vwap_75_list.append(None)
            elif i + 1 < 75:
                vwap_5_list.append(vwap_5)
                vwap_25_list.append(vwap_25)
                vwap_75_list.append(None)
            elif i + 1 >= 75:
                vwap_5_list.append(vwap_5)
                vwap_25_list.append(vwap_25)
                vwap_75_list.append(vwap_75)
        df['TradingPrice'] = tradingprice_list
        df['VWAP_5'] = vwap_5_list
        df['VWAP_25'] = vwap_25_list
        df['VWAP_75'] = vwap_75_list
        df.to_csv(mplf_csv)
    # ファイルが存在しない場合
    else:
        logger.error(f"元にするファイルが見つかりません：{sbi_timechart_csv}")
        return

    logger.info(df.head())

    addplot = mpf.make_addplot(data=df[['VWAP_25', 'VWAP_75']])
    mpf.plot(
        data=df,
        type='candle',
        mav=(25, 75),
        addplot=addplot,
        volume=True,
        title=sbi_timechart_csv,
        style='nightclouds',
        savefig=os.path.join('plot', f'{stock_code}_vwap.png')
    )
    mpf.plot(
        data=df,
        type='candle',
        mav=(5, 25, 75),
        # addplot=addplot,
        volume=True,
        title=sbi_timechart_csv,
        style='nightclouds',
        savefig=os.path.join('plot', f'{stock_code}_mav.png')
    )


def main():
    stock_code_list = []
    for file_name in os.listdir('sbi_timechart_csv'):
        match = re.search(r'(\d\d\d\d),*\.csv', file_name)
        if match:
            stock_code_list.append(match.group(1))

    for stock_code in stock_code_list:
        plot(stock_code)


if __name__ == '__main__':
    main()
