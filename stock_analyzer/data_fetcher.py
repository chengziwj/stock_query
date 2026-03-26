"""数据获取模块 - 股票代码解析和历史数据下载（使用akshare）"""

import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

import akshare as ak
import pandas as pd


class StockCodeParser:
    """股票代码解析器，支持多种输入格式"""

    # 上海交易所代码前缀
    SH_PREFIXES = ('60', '68', '50', '51')
    # 深圳交易所代码前缀
    SZ_PREFIXES = ('00', '30', '12', '15')

    # 已知股票名称到代码的映射（常用股票）
    STOCK_NAME_MAP = {
        '平安银行': '000001',
        '万科A': '000002',
        '国农科技': '000004',
        '世纪星源': '000005',
        '深振业A': '000006',
        '浦发银行': '600000',
        '邯郸钢铁': '600001',
        '白云机场': '600004',
        '中国石化': '600028',
        '招商银行': '600036',
        '贵州茅台': '600519',
        '中国平安': '601318',
        '工商银行': '601398',
        '建设银行': '601939',
        '中国石油': '601857',
        '中国银行': '601988',
        '农业银行': '601288',
        '中国人寿': '601628',
        '中国神华': '601088',
        '比亚迪': '002594',
        '宁德时代': '300750',
        '中国中免': '601888',
        '隆基绿能': '601012',
        '五粮液': '000858',
        '中国建筑': '601668',
        '海康威视': '002415',
        '美的集团': '000333',
        '格力电器': '000651',
        '中芯国际': '688981',
    }

    @classmethod
    def parse(cls, input_code: str) -> str:
        """
        解析股票代码输入，返回6位代码

        支持格式：
        - 6位数字: '000001' -> '000001'
        - 完整代码: '000001.SZ' -> '000001'
        - 中文简称: '平安银行' -> '000001'

        Args:
            input_code: 用户输入的股票代码或名称

        Returns:
            6位股票代码

        Raises:
            ValueError: 无法解析的股票代码
        """
        input_code = input_code.strip()

        # 检查是否为中文名称
        if cls._is_chinese(input_code):
            if input_code in cls.STOCK_NAME_MAP:
                return cls.STOCK_NAME_MAP[input_code]
            raise ValueError(f"未知的股票名称: {input_code}")

        # 完整格式 (如 000001.SZ)
        if '.' in input_code:
            code, _ = input_code.split('.')
            if len(code) == 6 and code.isdigit():
                return code
            raise ValueError(f"无效的股票代码格式: {input_code}")

        # 6位数字代码
        if len(input_code) == 6 and input_code.isdigit():
            return input_code

        raise ValueError(f"无法解析的股票代码: {input_code}")

    @classmethod
    def _is_chinese(cls, text: str) -> bool:
        """检查字符串是否包含中文字符"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)

    @classmethod
    def get_exchange(cls, code: str) -> str:
        """
        根据代码判断交易所

        Args:
            code: 6位股票代码

        Returns:
            交易所标识: 'sh' 或 'sz'
        """
        if code.startswith(cls.SH_PREFIXES):
            return 'sh'
        elif code.startswith(cls.SZ_PREFIXES):
            return 'sz'
        else:
            return 'sz'  # 默认深交所

    @classmethod
    def get_standard_code(cls, code: str) -> str:
        """获取标准格式代码（带交易所后缀）"""
        exchange = cls.get_exchange(code)
        return f"{code}.{exchange.upper()}"

    @classmethod
    def get_stock_name(cls, code: str) -> str:
        """获取股票名称（如果已知）"""
        reverse_map = {v: k for k, v in cls.STOCK_NAME_MAP.items()}
        return reverse_map.get(code, "未知")


class DataFetcher:
    """股票数据获取类（使用akshare）"""

    MAX_RETRIES = 3
    RETRY_INTERVAL = 2  # 秒

    def __init__(self):
        """初始化数据获取器"""
        pass

    def fetch_daily_data(
        self,
        stock_code: str,
        months: int = 6
    ) -> Tuple[pd.DataFrame, str, str]:
        """
        获取指定股票的日线数据

        Args:
            stock_code: 股票代码（可以是任意支持的格式）
            months: 获取最近几个月的数据，默认6个月

        Returns:
            Tuple[DataFrame, 标准代码, 股票名称]
            DataFrame包含列: trade_date, open, high, low, close, vol

        Raises:
            ValueError: 股票代码无效
            RuntimeError: 数据获取失败
        """
        # 解析股票代码
        code = StockCodeParser.parse(stock_code)
        standard_code = StockCodeParser.get_standard_code(code)
        stock_name = StockCodeParser.get_stock_name(code)

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 31)
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        # 重试机制获取数据
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                df = self._fetch_with_akshare(code, start_str, end_str)
                if df is not None and len(df) > 0:
                    return self._process_data(df), standard_code, stock_name
                raise RuntimeError(f"未获取到数据: {standard_code}")

            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_INTERVAL)

        raise RuntimeError(f"数据获取失败: {last_error}")

    def _fetch_with_akshare(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        使用akshare获取日线数据

        Args:
            code: 6位股票代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD

        Returns:
            原始DataFrame或None
        """
        # 判断交易所
        exchange = StockCodeParser.get_exchange(code)

        # 使用akshare获取A股日线数据
        # akshare的stock_zh_a_hist接口
        symbol = code
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=""  # 不复权
        )

        return df

    def _process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理和清洗原始数据

        Args:
            df: 原始数据

        Returns:
            处理后的数据，按日期升序排列
        """
        # akshare返回的列名: 日期, 开盘, 收盘, 最高, 最低, 成交量, ...
        # 重命名列
        column_map = {
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol'
        }

        # 选择需要的列并重命名
        df = df.rename(columns=column_map)

        # 只保留需要的列
        columns = ['trade_date', 'open', 'high', 'low', 'close', 'vol']
        df = df[columns].copy()

        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        # 按日期升序排列
        df = df.sort_values('trade_date').reset_index(drop=True)

        # 检查数据完整性
        if len(df) < 30:
            raise RuntimeError(f"数据不足30天，无法进行有效分析")

        return df


def fetch_stock_data(stock_code: str, months: int = 6) -> Tuple[pd.DataFrame, str, str]:
    """
    便捷函数：获取股票数据

    Args:
        stock_code: 股票代码（支持多种格式）
        months: 获取最近几个月的数据

    Returns:
        Tuple[DataFrame, 标准代码, 股票名称]
    """
    fetcher = DataFetcher()
    return fetcher.fetch_daily_data(stock_code, months)