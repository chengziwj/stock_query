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

    # 新增指标
    indicators['kdj'] = calculate_kdj(df)
    indicators['wr'] = calculate_wr(df)
    indicators['cci'] = calculate_cci(df)
    indicators['atr'] = calculate_atr(df)
    indicators['obv'] = calculate_obv(df)
    indicators['volume_ma'] = calculate_volume_ma(df)
    indicators['dmi'] = calculate_dmi(df)
    indicators['psy'] = calculate_psy(df)
    indicators['bbi'] = calculate_bbi(df)

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

    # MA值
    latest['ma'] = {
        'MA5': round(indicators['ma']['MA5'].iloc[last_idx], 2),
        'MA10': round(indicators['ma']['MA10'].iloc[last_idx], 2),
        'MA20': round(indicators['ma']['MA20'].iloc[last_idx], 2),
        'MA60': round(indicators['ma']['MA60'].iloc[last_idx], 2) if not pd.isna(indicators['ma']['MA60'].iloc[last_idx]) else None
    }

    # RSI值
    latest['rsi'] = round(indicators['rsi'].iloc[last_idx], 2)

    # MACD值
    latest['macd'] = {
        'DIF': round(indicators['macd']['DIF'].iloc[last_idx], 4),
        'DEA': round(indicators['macd']['DEA'].iloc[last_idx], 4),
        'MACD': round(indicators['macd']['MACD'].iloc[last_idx], 4)
    }

    # 布林带值
    latest['bollinger'] = {
        'upper': round(indicators['bollinger']['upper'].iloc[last_idx], 2),
        'middle': round(indicators['bollinger']['middle'].iloc[last_idx], 2),
        'lower': round(indicators['bollinger']['lower'].iloc[last_idx], 2)
    }

    # KDJ值
    latest['kdj'] = {
        'K': round(indicators['kdj']['K'].iloc[last_idx], 2),
        'D': round(indicators['kdj']['D'].iloc[last_idx], 2),
        'J': round(indicators['kdj']['J'].iloc[last_idx], 2)
    }

    # WR值
    latest['wr'] = round(indicators['wr'].iloc[last_idx], 2)

    # CCI值
    latest['cci'] = round(indicators['cci'].iloc[last_idx], 2)

    # ATR值
    latest['atr'] = round(indicators['atr'].iloc[last_idx], 4)

    # OBV值
    latest['obv'] = round(indicators['obv'].iloc[last_idx], 0)

    # 成交量均线
    latest['volume_ma'] = {
        'VOL_MA5': round(indicators['volume_ma']['VOL_MA5'].iloc[last_idx], 0),
        'VOL_MA10': round(indicators['volume_ma']['VOL_MA10'].iloc[last_idx], 0)
    }

    # DMI值
    latest['dmi'] = {
        '+DI': round(indicators['dmi']['+DI'].iloc[last_idx], 2),
        '-DI': round(indicators['dmi']['-DI'].iloc[last_idx], 2),
        'ADX': round(indicators['dmi']['ADX'].iloc[last_idx], 2)
    }

    # PSY值
    latest['psy'] = round(indicators['psy'].iloc[last_idx], 2)

    # BBI值
    latest['bbi'] = round(indicators['bbi'].iloc[last_idx], 2)

    return latest