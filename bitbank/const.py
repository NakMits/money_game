from enum import Enum


class PAIR(Enum):
    BTC_JPY = 'btc_jpy'


class INTERVAL(Enum):
    MIN = 3
    SHORT = 5
    LONG = 10


class DIRECTION(Enum):
    UP = 'UP'
    DOWN = 'DOWN'


class ORDER(Enum):
    BUY = 'BUY'
    SELL = 'SELL'


class WINRATE(Enum):
    MIN = 0.5001


class RATE(Enum):
    ROUND_DIGITS = 6


class CHANGERATE(Enum):
    MIN = 0.0002


class TRADERULE(Enum):
    WITHIN_DIFFRATE = 'within_diffrate'
    WITHOUT_DIFFRATE = 'without_diffrate'


class TRYNUM(Enum):
    BUY = 100
    SELL = 100
