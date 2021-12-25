import random
import statistics

import matplotlib.pyplot as plt

plt.rcParams['font.family'] = "Meiryo"


def assets_simulation(name: str, win_rate: float, win_change_rate: float, lose_change_rate: float, price_rate: float,
                      init_assets: int,
                      cost_rate: float = 0, max_inv_count: int = 10000, min_price: int = 1000, simul_num: int = 1000,
                      stop_get_paid: bool = False):
    """
    :param name: シミュレーション名
    :param win_rate: 投資回数ごとの勝率
    :param win_change_rate: 勝った場合の増加率
    :param lose_change_rate: 負けた場合の減少率
    :param price_rate: 投資回数ごとの投資金割合
    :param init_assets: 初期資産
    （以下任意パラメータ）
    :param cost_rate: 手数料割合
    :param max_inv_count: 投資回数上限
    :param min_price: 最低購入価格
    :param simul_num: シミュレーション回数
    :param stop_get_paid: 元本回収ラインを超えた場合に投資を止めるかどうか
    """
    print(f"シミュレーション名: 【{name}】")
    print(f"初期資産: {init_assets / 10000}万円")
    print(f"投資金割合: {'{:.1%}'.format(price_rate)}")
    print(f"勝率: {'{:.5%}'.format(win_rate)}")
    print(f"勝った場合の増加率: {'{:.1%}'.format(win_change_rate)}")
    print(f"負けた場合の減少率: {'{:.1%}'.format(lose_change_rate)}")
    print(f"手数料割合: {'{:.1%}'.format(cost_rate)}")
    print(f"投資回数上限: {max_inv_count}回")
    print(f"最低購入価格: {min_price / 10000}万円")
    print(f"サンプル数: {simul_num}")
    print(f"元本回収ラインを超えた場合に投資を止めるかどうか: {stop_get_paid}")

    fig, ax = plt.subplots()

    # シミュレーション
    exit_list = []  # 退場になったシミュレーション番号のリスト
    get_paid_list = []  # 元本回収ラインを超えたシミュレーション番号のリスト
    stop_get_paid_list = []  # 元本回収ラインを超えて投資をやめたシミュレーション番号のリスト
    assets_list = []  # 投資終了時の資産リスト
    win_count = 0
    lose_count = 0

    for i in range(simul_num):

        assets_record = [init_assets / init_assets]
        assets = init_assets

        # 投資を繰り返す
        while True:
            # 購入価格計算
            price = int(assets * price_rate)
            # 最低購入価格以下なら購入できず退場
            if price < min_price:
                exit_list.append(i)
                break
            # 購入
            assets -= price

            # 勝敗に応じて資産反映
            if random.random() >= 1 - win_rate:
                change_rate = win_change_rate
                win_count += 1
            else:
                change_rate = -lose_change_rate
                lose_count += 1
            # 資産反映
            assets += int(price * (1 + change_rate - cost_rate))

            principal_ratio = assets / init_assets  # 元本割合
            assets_record.append(principal_ratio)

            # 元本回収ラインを超えた場合
            if principal_ratio >= simul_num:
                # 重複しないようにリスト追加
                if i not in get_paid_list:
                    get_paid_list.append(i)
                # 投資をやめる指定がされていた場合はリスト追加して投資終了
                if stop_get_paid:
                    stop_get_paid_list.append(i)
                    break

            # 投資回数上限を超えているなら終了
            if max_inv_count:
                if len(assets_record) > max_inv_count:
                    break

        assets_list.append(assets)

        # プロット
        x = range(len(assets_record))
        y = assets_record
        ax.plot(x, y)

    # グラフ表示
    ax.set_xlabel('投資回数')  # x軸ラベル
    ax.set_ylabel('元本割合')  # y軸ラベル
    # ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))  # y軸を百分率で表示
    title = f"【{name}】\n"
    title += f"元本割合_中央値: {'{:.1%}'.format(statistics.median(assets_list) / init_assets)}\n"
    exit_rate = (len(exit_list) - len(stop_get_paid_list)) / (i + 1)
    if exit_rate < 0:
        exit_rate = 0
    title += f"退場率: {'{:.1%}'.format(exit_rate)}\n"
    title += f"元本回収ライン達成率: {'{:.1%}'.format(len(get_paid_list) / (i + 1))}"
    ax.set_title(title)  # グラフタイトル
    fig.tight_layout()  # レイアウトの設定
    ax.grid()  # 罫線
    if get_paid_list:
        plt.axhline(y=simul_num, xmin=0.0, xmax=1.0, color="blue", linestyle=":")  # 元本回収ライン
    plt.axhline(y=init_assets / init_assets, xmin=0.0, xmax=1.0, color="black", linestyle=":")  # 初期資産ライン
    plt.axhline(y=min_price / init_assets, xmin=0.0, xmax=1.0, color="red", linestyle=":")  # 退場（最低購入価格）ライン
    fig.set_size_inches(10, 10)
    fig.savefig(f"【{name}】.png")
    # plt.show()


def best_risk():
    init_assets = 1000000
    min_price = int(init_assets / 10000)

    # 最適なリスクの取り方をシミュレーションで調べる
    # 何回かやってみて「(勝率%-50%)*2」が最適っぽいからその近辺で細かくシミュレーションさせる
    init_win_rate = 0.500000000000000
    max_win_rate = 0.60

    win_rate = init_win_rate
    while win_rate <= max_win_rate:
        best_change_rate = (win_rate - 0.500000000000000) * 2
        change_rate_list = [
            best_change_rate - 0.005,
            best_change_rate,
            best_change_rate + 0.005,
        ]
        for change_rate in change_rate_list:
            if change_rate < 0:
                continue
            assets_simulation(
                name=f"勝率{'{:.1%}'.format(win_rate)}、増減率±{'{:.1%}'.format(change_rate)}",
                price_rate=1.0,
                win_rate=win_rate,
                win_change_rate=change_rate,
                lose_change_rate=change_rate,
                init_assets=init_assets,
                min_price=min_price,
                simul_num=1000,
                max_inv_count=10000,
                # stop_get_paid=True
            )
        win_rate += 0.01


def main():
    # assets_simulation(
    #     name=f"シミュレーション",
    #     init_assets=1000000,
    #     price_rate=1.00,
    #     win_rate=0.5000000000,
    #     win_change_rate=0.05,
    #     lose_change_rate=0.05,
    #     cost_rate=0.00000,
    #     max_inv_count=1000,
    #     min_price=1000,
    #     simul_num=10000,
    #     stop_get_paid=False
    # )
    best_risk()


if __name__ == '__main__':
    main()
