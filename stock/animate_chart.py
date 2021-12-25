'''
This file contains a simple animation demo using mplfinance "external axes mode".
Note that presently mplfinance does not support "blitting" (blitting makes animation
more efficient).  Nonetheless, the animation is efficient enough to update at least
once per second, and typically more frequently depending on the size of the plot.
'''
import os

import pandas as pd
import mplfinance as mpf
import matplotlib.animation as animation

stock_code = "1407"
mplf_csv = os.path.join('mplf_csv', stock_code + '.csv' + '.mplf')
df = pd.read_csv(mplf_csv, index_col=0, parse_dates=[0], encoding="SHIFT-JIS")
df = df.sort_index(ascending=True)
df.shape
df.head(3)
df.tail(3)

fig = mpf.figure(style='charles', figsize=(8, 7))
ax1 = fig.add_subplot(2, 1, 1)
ax2 = fig.add_subplot(3, 1, 3)


def animate(ival):
    if (20 + ival) > len(df):
        print('no more data to plot')
        ani.event_source.interval *= 3
        if ani.event_source.interval > 12000:
            exit()
        return
    data = df.iloc[0:(20 + ival)]
    ax1.clear()
    ax2.clear()
    mpf.plot(data, ax=ax1, volume=ax2, type='candle')


ani = animation.FuncAnimation(fig, animate, interval=1000)

mpf.show()
