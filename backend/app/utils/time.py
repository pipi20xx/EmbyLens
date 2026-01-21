from datetime import datetime
import pytz

def get_local_time():
    """获取本地时间 (Asia/Shanghai)"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)
