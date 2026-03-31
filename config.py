from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")

_KR_WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

def format_date(dt):
    """datetime을 '03/31(월)' 형식으로 반환"""
    return dt.strftime("%m/%d") + f"({_KR_WEEKDAYS[dt.weekday()]})"

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

_CHANNEL_VARS = {
    "CH_WAKE": "기상 챌린지",
    "CH_CODING": "코테 인증",
    "CH_DAILY": "데일리 인증",
    "CH_STATS": "주간 통계",
    "CH_FREE": "자유",
}

CH_WAKE   = int(os.getenv("CH_WAKE", 0))
CH_CODING = int(os.getenv("CH_CODING", 0))
CH_DAILY  = int(os.getenv("CH_DAILY", 0))
CH_STATS  = int(os.getenv("CH_STATS", 0))
CH_FREE   = int(os.getenv("CH_FREE", 0))

for var, name in _CHANNEL_VARS.items():
    if not globals()[var]:
        logger.warning(f"{var} 환경변수가 설정되지 않았습니다. {name} 채널 기능이 비활성화됩니다.")