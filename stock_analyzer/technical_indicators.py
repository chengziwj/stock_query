"""技术指标计算模块 - 完整版"""

from typing import Dict, Tuple

import numpy as np
import pandas as pd


# ============ 基础指标 ============

def calculate_ma(df: pd.DataFrame, periods: Tuple[int, ...] = (5, 10, 20, 60)) -> Dict[str, pd.Series]:
    """
    计算简单移动平均线

    Args:
        df: 包含 'close' 列的DataFrame
        periods: 周期列表，默认 (5, 10, 20, 60)

    Returns:
        字典，键为 'MA{period}'，值为移动平均线Series
    """
    result = {}
    for period in periods:
        result[f'MA{period}'] = df['close'].rolling(window=period).mean()
    return result


def calculate_ema(df: pd.DataFrame, periods: Tuple[int, ...] = (12, 26)) -> Dict[str, pd.Series]:
    """
    计算指数移动平均线

    Args:
        df: 包含 'close' 列的DataFrame
        periods: 周期列表

    Returns:
        字典，键为 'EMA{period}'
    """
    result = {}
    for period in periods:
        result[f'EMA{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    return result


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算相对强弱指数 (RSI)

    RSI = 100 - 100 / (1 + RS)
    RS = 平均涨幅 / 平均跌幅
    """
    close = df['close']
    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, pd.Series]:
    """
    计算MACD指标

    DIF = EMA(12) - EMA(26)
    DEA = EMA(DIF, 9)
    MACD = (DIF - DEA) * 2
    """
    close = df['close']

    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()

    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal_period, adjust=False).mean()
    macd = (dif - dea) * 2

    return {'DIF': dif, 'DEA': dea, 'MACD': macd}


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, pd.Series]:
    """
    计算布林带

    中轨 = MA(period)
    上轨 = 中轨 + std_dev * 标准差
    下轨 = 中轨 - std_dev * 标准差
    """
    close = df['close']

    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()

    upper = middle + std_dev * std
    lower = middle - std_dev * std

    return {'upper': upper, 'middle': middle, 'lower': lower}


# ============ 新增指标 ============

def calculate_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> Dict[str, pd.Series]:
    """
    计算KDJ随机指标

    RSV = (收盘价 - N日最低价) / (N日最高价 - N日最低价) * 100
    K = SMA(RSV, M1)
    D = SMA(K, M2)
    J = 3K - 2D

    Args:
        df: 包含 'high', 'low', 'close' 列的DataFrame
        n: RSV周期，默认9
        m1: K值平滑周期，默认3
        m2: D值平滑周期，默认3

    Returns:
        字典包含 'K', 'D', 'J' 三个Series

    信号说明：
    - K > D：看涨
    - K < D：看跌
    - K、D > 80：超买
    - K、D < 20：超卖
    - J > 100：严重超买
    - J < 0：严重超卖
    """
    low_n = df['low'].rolling(window=n).min()
    high_n = df['high'].rolling(window=n).max()

    rsv = (df['close'] - low_n) / (high_n - low_n) * 100
    rsv = rsv.fillna(50)

    # K值 = RSV的M1日移动平均
    k = rsv.ewm(alpha=1/m1, adjust=False).mean()

    # D值 = K值的M2日移动平均
    d = k.ewm(alpha=1/m2, adjust=False).mean()

    # J值 = 3K - 2D
    j = 3 * k - 2 * d

    return {'K': k, 'D': d, 'J': j}


def calculate_wr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算威廉指标 (Williams %R)

    WR = (N日最高价 - 收盘价) / (N日最高价 - N日最低价) * 100

    Args:
        df: 包含 'high', 'low', 'close' 列的DataFrame
        period: 周期，默认14

    Returns:
        WR Series

    信号说明：
    - WR < -20：超买区域
    - WR > -80：超卖区域
    - WR从超买区回落：卖出信号
    - WR从超卖区回升：买入信号
    """
    high_n = df['high'].rolling(window=period).max()
    low_n = df['low'].rolling(window=period).min()

    wr = (high_n - df['close']) / (high_n - low_n) * 100
    wr = wr * (-1)  # 转为负值表示

    return wr


def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    计算顺势指标 (Commodity Channel Index)

    TP = (最高价 + 最低价 + 收盘价) / 3
    CCI = (TP - TP的N日简单平均) / (0.015 * TP的N日平均绝对偏差)

    Args:
        df: 包含 'high', 'low', 'close' 列的DataFrame
        period: 周期，默认20

    Returns:
        CCI Series

    信号说明：
    - CCI > 100：超买，多头市场
    - CCI < -100：超卖，空头市场
    - CCI从下向上突破100：买入信号
    - CCI从上向下跌破100：卖出信号
    """
    tp = (df['high'] + df['low'] + df['close']) / 3

    tp_ma = tp.rolling(window=period).mean()
    tp_mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

    cci = (tp - tp_ma) / (0.015 * tp_mad)

    return cci


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算真实波幅 (Average True Range)

    TR = max(最高价-最低价, |最高价-昨收|, |最低价-昨收|)
    ATR = TR的N日移动平均

    Args:
        df: 包含 'high', 'low', 'close' 列的DataFrame
        period: 周期，默认14

    Returns:
        ATR Series

    用途：
    - 衡量市场波动性
    - 用于设置止损位（如：买入价 - 2*ATR）
    - ATR增大表示波动加剧
    """
    prev_close = df['close'].shift(1)

    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - prev_close)
    tr3 = abs(df['low'] - prev_close)

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr


def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    计算能量潮指标 (On Balance Volume)

    今日OBV = 昨日OBV + 今日成交量
    - 如果今日收盘价 > 昨日收盘价，成交量取正
    - 如果今日收盘价 < 昨日收盘价，成交量取负

    Args:
        df: 包含 'close', 'vol' 列的DataFrame

    Returns:
        OBV Series

    信号说明：
    - OBV上升，价格上升：趋势确认
    - OBV下降，价格下降：趋势确认
    - OBV上升，价格下降：底背离，可能反弹
    - OBV下降，价格上升：顶背离，可能回调
    """
    close = df['close']
    volume = df['vol']

    # 计算价格变动方向
    direction = np.where(close > close.shift(1), 1,
                         np.where(close < close.shift(1), -1, 0))

    obv = (volume * direction).cumsum()

    return pd.Series(obv, index=df.index)


def calculate_volume_ma(df: pd.DataFrame, periods: Tuple[int, ...] = (5, 10, 20)) -> Dict[str, pd.Series]:
    """
    计算成交量均线

    Args:
        df: 包含 'vol' 列的DataFrame
        periods: 周期列表

    Returns:
        字典，键为 'VOL_MA{period}'
    """
    result = {}
    for period in periods:
        result[f'VOL_MA{period}'] = df['vol'].rolling(window=period).mean()
    return result


def calculate_dmi(df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
    """
    计算动向指标 (Directional Movement Index)

    +DM = 最高价 - 昨日最高价（如果大于最低价-昨日最低价）
    -DM = 昨日最低价 - 最低价（如果大于最高价-昨日最高价）
    +DI = +DM的N日指数移动平均 / ATR
    -DI = -DM的N日指数移动平均 / ATR
    DX = |+DI - -DI| / (+DI + -DI) * 100
    ADX = DX的N日移动平均

    Args:
        df: 包含 'high', 'low', 'close' 列的DataFrame
        period: 周期，默认14

    Returns:
        字典包含 '+DI', '-DI', 'ADX', 'ADXR'

    信号说明：
    - +DI > -DI：多头市场
    - +DI < -DI：空头市场
    - ADX > 25：趋势明确
    - ADX < 20：震荡市场
    - ADX从下向上突破-DI：买入信号
    - ADX从上向下跌破+DI：卖出信号
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # 计算+DM和-DM
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    # 计算ATR
    atr = calculate_atr(df, period)

    # 计算+DI和-DI
    plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / atr

    plus_di.index = df.index
    minus_di.index = df.index

    # 计算DX和ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()

    # ADXR (ADX Rating)
    adxr = (adx + adx.shift(period)) / 2

    return {
        '+DI': plus_di,
        '-DI': minus_di,
        'ADX': adx,
        'ADXR': adxr
    }


def calculate_psy(df: pd.DataFrame, period: int = 12) -> pd.Series:
    """
    计算心理线 (Psychological Line)

    PSY = N日内上涨天数 / N * 100

    Args:
        df: 包含 'close' 列的DataFrame
        period: 周期，默认12

    Returns:
        PSY Series

    信号说明：
    - PSY > 75：超买
    - PSY < 25：超卖
    """
    close = df['close']
    up_days = (close > close.shift(1)).astype(int)

    psy = up_days.rolling(window=period).sum() / period * 100

    return psy


def calculate_bbi(df: pd.DataFrame) -> pd.Series:
    """
    计算多空指标 (Bull and Bear Index)

    BBI = (MA3 + MA6 + MA12 + MA24) / 4

    Args:
        df: 包含 'close' 列的DataFrame

    Returns:
        BBI Series

    信号说明：
    - 价格 > BBI：多头市场
    - 价格 < BBI：空头市场
    """
    close = df['close']

    ma3 = close.rolling(window=3).mean()
    ma6 = close.rolling(window=6).mean()
    ma12 = close.rolling(window=12).mean()
    ma24 = close.rolling(window=24).mean()

    bbi = (ma3 + ma6 + ma12 + ma24) / 4

    return bbi


# ============ 新增趋势类指标 ============

def calculate_sar(
    df: pd.DataFrame,
    af_start: float = 0.02,
    af_increment: float = 0.02,
    af_max: float = 0.20
) -> pd.Series:
    """
    计算抛物线转向指标 (Parabolic SAR)

    SAR(n+1) = SAR(n) + AF * (EP - SAR(n))
    - AF：加速因子，从af_start开始，每次创新高/低加af_increment，最大af_max
    - EP：极值点（多头时为最高价，空头时为最低价）

    Args:
        df: 包含 'high', 'low', 'close' 列的DataFrame
        af_start: 初始加速因子，默认0.02
        af_increment: 加速因子增量，默认0.02
        af_max: 最大加速因子，默认0.20

    Returns:
        SAR Series

    信号说明：
    - 价格 > SAR：多头持仓，SAR为止损位
    - 价格 < SAR：空头持仓，SAR为止损位
    - 价格触及SAR：趋势反转信号
    - SAR由上转下：买入信号
    - SAR由下转上：卖出信号
    """
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    length = len(df)

    sar = np.zeros(length)
    ep = np.zeros(length)
    af = np.zeros(length)
    trend = np.ones(length)  # 1为多头，-1为空头

    # 初始化：使用前4天判断初始趋势
    if close[3] > close[0]:
        trend[0] = 1
        sar[0] = min(low[0], low[1], low[2])
        ep[0] = max(high[0], high[1], high[2])
    else:
        trend[0] = -1
        sar[0] = max(high[0], high[1], high[2])
        ep[0] = min(low[0], low[1], low[2])

    af[0] = af_start

    for i in range(1, length):
        # 计算当日SAR
        sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])

        # 多头趋势
        if trend[i-1] == 1:
            sar[i] = min(sar[i], low[i-1], low[i-2] if i >= 2 else low[i-1])
            if low[i] < sar[i]:
                # 反转为空头
                trend[i] = -1
                sar[i] = ep[i-1]
                ep[i] = low[i]
                af[i] = af_start
            else:
                trend[i] = 1
                if high[i] > ep[i-1]:
                    ep[i] = high[i]
                    af[i] = min(af[i-1] + af_increment, af_max)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]

        # 空头趋势
        else:
            sar[i] = max(sar[i], high[i-1], high[i-2] if i >= 2 else high[i-1])
            if high[i] > sar[i]:
                # 反转为多头
                trend[i] = 1
                sar[i] = ep[i-1]
                ep[i] = high[i]
                af[i] = af_start
            else:
                trend[i] = -1
                if low[i] < ep[i-1]:
                    ep[i] = low[i]
                    af[i] = min(af[i-1] + af_increment, af_max)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]

    return pd.Series(sar, index=df.index)


def calculate_env(
    df: pd.DataFrame,
    period: int = 20,
    offset: float = 0.05
) -> Dict[str, pd.Series]:
    """
    计算包络线 (Envelope)

    上轨 = MA(N) * (1 + offset)
    下轨 = MA(N) * (1 - offset)

    Args:
        df: 包含 'close' 列的DataFrame
        period: 基准均线周期，默认20
        offset: 偏移百分比，默认0.05（5%）

    Returns:
        字典包含 'upper', 'middle', 'lower' 三个Series

    信号说明：
    - 价格触及上轨：短期超买，可能回调
    - 价格触及下轨：短期超卖，可能反弹
    - 价格在中轨附近：趋势平稳
    - 上轨与下轨收窄：波动减小，可能突破
    """
    close = df['close']

    middle = close.rolling(window=period).mean()
    upper = middle * (1 + offset)
    lower = middle * (1 - offset)

    return {'upper': upper, 'middle': middle, 'lower': lower}


# ============ 新增成交量类指标 ============

def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算资金流量指标 (Money Flow Index)

    TP = (最高价 + 最低价 + 收盘价) / 3
    MF = TP * 成交量
    PMF = 当TP上涨时的MF总和
    NMF = 当TP下跌时的MF总和
    MFI = 100 - 100 / (1 + PMF/NMF)

    Args:
        df: 包含 'high', 'low', 'close', 'vol' 列的DataFrame
        period: 周期，默认14

    Returns:
        MFI Series（范围0-100）

    信号说明：
    - MFI > 80：超买区域，资金流入过多，可能回调
    - MFI < 20：超卖区域，资金流出过多，可能反弹
    - MFI上穿20：买入信号
    - MFI下穿80：卖出信号
    - MFI与价格背离：趋势反转预警
    """
    tp = (df['high'] + df['low'] + df['close']) / 3
    mf = tp * df['vol']

    # 计算正/负资金流量
    tp_change = tp.diff()
    positive_mf = mf.where(tp_change > 0, 0)
    negative_mf = mf.where(tp_change < 0, 0)

    # 计算周期内的总和
    positive_sum = positive_mf.rolling(window=period).sum()
    negative_sum = negative_mf.rolling(window=period).sum()

    # 计算MFI
    mfi = 100 - (100 / (1 + positive_sum / negative_sum))

    return mfi


def calculate_vroc(df: pd.DataFrame, period: int = 12) -> pd.Series:
    """
    计算成交量变动率 (Volume Rate of Change)

    VROC = (今日成交量 - N日前成交量) / N日前成交量 * 100

    Args:
        df: 包含 'vol' 列的DataFrame
        period: 周期，默认12

    Returns:
        VROC Series

    信号说明：
    - VROC > 0：成交量增加
    - VROC < 0：成交量减少
    - VROC大幅上升（如>50）：成交量急剧放大，关注价格突破
    - VROC持续高位：成交活跃，趋势延续
    - VROC急剧下降：成交萎缩，趋势可能衰竭
    """
    volume = df['vol']
    vroc = (volume - volume.shift(period)) / volume.shift(period) * 100

    return vroc


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    计算成交量加权平均价 (Volume Weighted Average Price)

    VWAP = Σ(典型价格 × 成交量) / Σ成交量
    典型价格 = (最高价 + 最低价 + 收盘价) / 3

    Args:
        df: 包含 'high', 'low', 'close', 'vol' 列的DataFrame

    Returns:
        VWAP Series（累积计算）

    信号说明：
    - 价格 > VWAP：多头占优，适合持有或买入
    - 价格 < VWAP：空头占优，适合观望或卖出
    - VWAP是机构交易的重要参考价位
    - 价格从下方突破VWAP：买入信号
    - 价格从上方跌破VWAP：卖出信号
    """
    tp = (df['high'] + df['low'] + df['close']) / 3

    # 累积计算VWAP
    cumulative_tp_vol = (tp * df['vol']).cumsum()
    cumulative_vol = df['vol'].cumsum()

    vwap = cumulative_tp_vol / cumulative_vol

    return vwap


# ============ 新增动量类指标 ============

def calculate_roc(df: pd.DataFrame, period: int = 12) -> pd.Series:
    """
    计算变动率指标 (Rate of Change)

    ROC = (今日收盘价 - N日前收盘价) / N日前收盘价 * 100

    Args:
        df: 包含 'close' 列的DataFrame
        period: 周期，默认12

    Returns:
        ROC Series

    信号说明：
    - ROC > 0：价格上涨动量
    - ROC < 0：价格下跌动量
    - ROC上穿0线：买入信号
    - ROC下穿0线：卖出信号
    - ROC达到极端值（如±20）：趋势可能反转
    - ROC与价格背离：趋势减弱预警
    """
    close = df['close']
    roc = (close - close.shift(period)) / close.shift(period) * 100

    return roc


def calculate_mtm(df: pd.DataFrame, period: int = 12) -> pd.Series:
    """
    计算动量指标 (Momentum)

    MTM = 今日收盘价 - N日前收盘价

    Args:
        df: 包含 'close' 列的DataFrame
        period: 周期，默认12

    Returns:
        MTM Series

    信号说明：
    - MTM > 0：价格上涨动量
    - MTM < 0：价格下跌动量
    - MTM上穿0线：买入信号
    - MTM下穿0线：卖出信号
    - MTM持续上升：动量增强
    - MTM持续下降：动量减弱
    """
    close = df['close']
    mtm = close - close.shift(period)

    return mtm


def calculate_uos(
    df: pd.DataFrame,
    period1: int = 7,
    period2: int = 14,
    period3: int = 28
) -> pd.Series:
    """
    计算终极指标 (Ultimate Oscillator)

    TH = max(最高价, 昨日收盘)
    TL = min(最低价, 昨日收盘)
    ACC = Σ(TP-TL) / Σ(TH-TP)
    UOS = 100 * (ACC1*4 + ACC2*2 + ACC3) / 7

    Args:
        df: 包含 'high', 'low', 'close' 列的DataFrame
        period1: 短周期，默认7
        period2: 中周期，默认14
        period3: 长周期，默认28

    Returns:
        UOS Series（范围0-100）

    信号说明：
    - UOS > 70：超买区域
    - UOS < 30：超卖区域
    - UOS上穿35：买入信号（保守）
    - UOS下穿70：卖出信号（保守）
    - UOS从超卖区上升且价格背离：强烈买入信号
    - UOS从超买区下降且价格背离：强烈卖出信号
    - 三周期加权设计减少假信号
    """
    close = df['close']
    prev_close = close.shift(1)

    # 计算真实高低价
    th = pd.concat([df['high'], prev_close], axis=1).max(axis=1)
    tl = pd.concat([df['low'], prev_close], axis=1).min(axis=1)

    # 计算典型价格
    tp = (df['high'] + df['low'] + df['close']) / 3

    # 计算买入压力和真实波幅
    bp = tp - tl  # 买入压力
    tr = th - tl  # 真实波幅

    # 计算三个周期的累积值
    def calc_acc(bp, tr, period):
        bp_sum = bp.rolling(window=period).sum()
        tr_sum = tr.rolling(window=period).sum()
        return bp_sum / tr_sum

    acc1 = calc_acc(bp, tr, period1)
    acc2 = calc_acc(bp, tr, period2)
    acc3 = calc_acc(bp, tr, period3)

    # 计算终极指标
    uos = 100 * (acc1 * 4 + acc2 * 2 + acc3) / 7

    return uos


# ============ 新增情绪类指标 ============

def calculate_vr(df: pd.DataFrame, period: int = 26) -> pd.Series:
    """
    计算容量比率 (Volume Ratio)

    VR = (上涨日成交量总和 + 下跌日成交量/2) / (下跌日成交量总和 + 上涨日成交量/2) * 100

    Args:
        df: 包含 'close', 'vol' 列的DataFrame
        period: 周期，默认26

    Returns:
        VR Series

    信号说明：
    - VR > 450：过度超买，高风险区域
    - VR 300-450：强势区域，多头活跃
    - VR 150-300：正常上升区域
    - VR 70-150：正常震荡区域
    - VR 40-70：弱势区域，空头活跃
    - VR < 40：过度超卖，反弹机会
    - VR上穿40：买入信号
    - VR下穿450：卖出信号
    """
    close = df['close']
    volume = df['vol']

    # 判断上涨/下跌/持平
    up = close > close.shift(1)
    down = close < close.shift(1)
    flat = close == close.shift(1)

    # 计算各类成交量
    up_vol = volume.where(up, 0)
    down_vol = volume.where(down, 0)
    flat_vol = volume.where(flat, 0)

    # 周期内累积
    up_sum = up_vol.rolling(window=period).sum()
    down_sum = down_vol.rolling(window=period).sum()
    flat_sum = flat_vol.rolling(window=period).sum()

    # 计算VR
    vr = (up_sum + flat_sum / 2) / (down_sum + flat_sum / 2) * 100

    return vr


def calculate_arbr(df: pd.DataFrame, period: int = 26) -> Dict[str, pd.Series]:
    """
    计算人气意愿指标 (AR and BR)

    AR = Σ(最高价-开盘价) / Σ(开盘价-最低价) * 100
    BR = Σ(最高价-昨日收盘) / Σ(昨日收盘-最低价) * 100

    Args:
        df: 包含 'open', 'high', 'low', 'close' 列的DataFrame
        period: 周期，默认26

    Returns:
        字典包含 'AR', 'BR' 两个Series

    信号说明（AR）：
    - AR > 150：市场人气过热，可能回调
    - AR 80-120：市场人气正常
    - AR < 50：市场人气低迷，可能反弹

    信号说明（BR）：
    - BR > 300：市场意愿过热，高风险
    - BR 70-150：市场意愿正常
    - BR < 50：市场意愿低迷，超卖信号

    组合信号：
    - AR和BR同时处于极端高位：强烈卖出信号
    - AR和BR同时处于极端低位：强烈买入信号
    - BR > AR且BR高位：多头情绪高涨
    """
    open_price = df['open']
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)

    # 计算AR
    ar_ho = high - open_price  # 高-开
    ar_ol = open_price - low   # 开-低
    ar_ho_sum = ar_ho.rolling(window=period).sum()
    ar_ol_sum = ar_ol.rolling(window=period).sum()
    ar = ar_ho_sum / ar_ol_sum * 100

    # 计算BR（注意：使用昨日收盘）
    br_hc = high - prev_close  # 高-昨收
    br_cl = prev_close - low   # 昨收-低
    br_hc_sum = br_hc.rolling(window=period).sum()
    br_cl_sum = br_cl.rolling(window=period).sum()
    br = br_hc_sum / br_cl_sum * 100

    return {'AR': ar, 'BR': br}


# ============ 汇总函数 ============

def calculate_all_indicators(df: pd.DataFrame) -> Dict:
    """
    计算所有技术指标

    Args:
        df: 包含 'open', 'high', 'low', 'close', 'vol' 列的DataFrame

    Returns:
        包含所有技术指标的字典
    """
    indicators = {}

    # 基础指标
    indicators['ma'] = calculate_ma(df)
    indicators['ema'] = calculate_ema(df)
    indicators['rsi'] = calculate_rsi(df)
    indicators['macd'] = calculate_macd(df)
    indicators['bollinger'] = calculate_bollinger_bands(df)

    # 随机指标
    indicators['kdj'] = calculate_kdj(df)
    indicators['wr'] = calculate_wr(df)
    indicators['cci'] = calculate_cci(df)

    # 波动率指标
    indicators['atr'] = calculate_atr(df)

    # 成交量指标
    indicators['obv'] = calculate_obv(df)
    indicators['volume_ma'] = calculate_volume_ma(df)
    indicators['mfi'] = calculate_mfi(df)
    indicators['vroc'] = calculate_vroc(df)
    indicators['vwap'] = calculate_vwap(df)

    # 趋势指标
    indicators['dmi'] = calculate_dmi(df)
    indicators['sar'] = calculate_sar(df)
    indicators['env'] = calculate_env(df)

    # 心理指标
    indicators['psy'] = calculate_psy(df)
    indicators['bbi'] = calculate_bbi(df)

    # 动量指标
    indicators['roc'] = calculate_roc(df)
    indicators['mtm'] = calculate_mtm(df)
    indicators['uos'] = calculate_uos(df)

    # 情绪指标
    indicators['vr'] = calculate_vr(df)
    indicators['arbr'] = calculate_arbr(df)

    return indicators


def get_latest_values(indicators: Dict, df: pd.DataFrame) -> Dict:
    """
    获取最新的指标值

    Args:
        indicators: calculate_all_indicators 返回的字典
        df: 原始数据DataFrame

    Returns:
        包含最新指标值的字典
    """
    latest = {}
    last_idx = len(df) - 1

    # 安全获取值的辅助函数
    def safe_get(series, idx, default=None):
        try:
            val = series.iloc[idx]
            if pd.isna(val):
                return default
            return val
        except:
            return default

    # MA值
    latest['ma'] = {
        'MA5': round(safe_get(indicators['ma']['MA5'], last_idx), 2),
        'MA10': round(safe_get(indicators['ma']['MA10'], last_idx), 2),
        'MA20': round(safe_get(indicators['ma']['MA20'], last_idx), 2),
        'MA60': round(safe_get(indicators['ma']['MA60'], last_idx), 2) if safe_get(indicators['ma']['MA60'], last_idx) else None
    }

    # EMA值
    latest['ema'] = {
        'EMA12': round(safe_get(indicators['ema']['EMA12'], last_idx), 2),
        'EMA26': round(safe_get(indicators['ema']['EMA26'], last_idx), 2)
    }

    # RSI值
    latest['rsi'] = round(safe_get(indicators['rsi'], last_idx), 2)

    # MACD值
    latest['macd'] = {
        'DIF': round(safe_get(indicators['macd']['DIF'], last_idx), 4),
        'DEA': round(safe_get(indicators['macd']['DEA'], last_idx), 4),
        'MACD': round(safe_get(indicators['macd']['MACD'], last_idx), 4)
    }

    # 布林带值
    latest['bollinger'] = {
        'upper': round(safe_get(indicators['bollinger']['upper'], last_idx), 2),
        'middle': round(safe_get(indicators['bollinger']['middle'], last_idx), 2),
        'lower': round(safe_get(indicators['bollinger']['lower'], last_idx), 2)
    }

    # KDJ值
    latest['kdj'] = {
        'K': round(safe_get(indicators['kdj']['K'], last_idx), 2),
        'D': round(safe_get(indicators['kdj']['D'], last_idx), 2),
        'J': round(safe_get(indicators['kdj']['J'], last_idx), 2)
    }

    # WR值
    latest['wr'] = round(safe_get(indicators['wr'], last_idx), 2)

    # CCI值
    latest['cci'] = round(safe_get(indicators['cci'], last_idx), 2)

    # ATR值
    latest['atr'] = round(safe_get(indicators['atr'], last_idx), 4)

    # OBV值
    latest['obv'] = round(safe_get(indicators['obv'], last_idx), 0)

    # 成交量均线
    latest['volume_ma'] = {
        'VOL_MA5': round(safe_get(indicators['volume_ma']['VOL_MA5'], last_idx), 0),
        'VOL_MA10': round(safe_get(indicators['volume_ma']['VOL_MA10'], last_idx), 0)
    }

    # DMI值
    latest['dmi'] = {
        '+DI': round(safe_get(indicators['dmi']['+DI'], last_idx), 2),
        '-DI': round(safe_get(indicators['dmi']['-DI'], last_idx), 2),
        'ADX': round(safe_get(indicators['dmi']['ADX'], last_idx), 2)
    }

    # PSY值
    latest['psy'] = round(safe_get(indicators['psy'], last_idx), 2)

    # BBI值
    latest['bbi'] = round(safe_get(indicators['bbi'], last_idx), 2)

    # ========== 新增指标 ==========

    # SAR值
    latest['sar'] = round(safe_get(indicators['sar'], last_idx), 2)

    # ENV值（包络线）
    latest['env'] = {
        'upper': round(safe_get(indicators['env']['upper'], last_idx), 2),
        'middle': round(safe_get(indicators['env']['middle'], last_idx), 2),
        'lower': round(safe_get(indicators['env']['lower'], last_idx), 2)
    }

    # MFI值（资金流量指标）
    latest['mfi'] = round(safe_get(indicators['mfi'], last_idx), 2)

    # VROC值（成交量变动率）
    latest['vroc'] = round(safe_get(indicators['vroc'], last_idx), 2)

    # VWAP值（成交量加权平均价）
    latest['vwap'] = round(safe_get(indicators['vwap'], last_idx), 2)

    # ROC值（变动率指标）
    latest['roc'] = round(safe_get(indicators['roc'], last_idx), 2)

    # MTM值（动量指标）
    latest['mtm'] = round(safe_get(indicators['mtm'], last_idx), 2)

    # UOS值（终极指标）
    latest['uos'] = round(safe_get(indicators['uos'], last_idx), 2)

    # VR值（容量比率）
    latest['vr'] = round(safe_get(indicators['vr'], last_idx), 2)

    # ARBR值（人气意愿指标）
    latest['arbr'] = {
        'AR': round(safe_get(indicators['arbr']['AR'], last_idx), 2),
        'BR': round(safe_get(indicators['arbr']['BR'], last_idx), 2)
    }

    return latest