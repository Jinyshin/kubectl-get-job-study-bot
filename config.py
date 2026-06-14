from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from datetime import datetime
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")

def now_kst():
    """현재 KST 시간을 timezone offset 없이 반환 (SQLite DATE() 호환)"""
    return datetime.now(KST).replace(tzinfo=None)

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
    "CH_WELCOME": "환영",
}

CH_WAKE   = int(os.getenv("CH_WAKE", 0))
CH_CODING = int(os.getenv("CH_CODING", 0))
CH_DAILY  = int(os.getenv("CH_DAILY", 0))
CH_STATS  = int(os.getenv("CH_STATS", 0))
CH_FREE    = int(os.getenv("CH_FREE", 0))
CH_WELCOME = int(os.getenv("CH_WELCOME", 0))
GUILD_ID   = int(os.getenv("GUILD_ID", 0))

WELCOME_GUIDE_URL = os.getenv("WELCOME_GUIDE_URL", "")

# 활동 인정 채널 — "ID:표시이름" 쌍을 콤마로 나열 (실제 값은 .env의 CH_ACTIVITY)
#   자유 메시지로 참여하는 채널을 등록. 표시이름은 주간 통계 출력에 그대로 쓰인다.
#   커맨드로 집계되는 채널(기상·코테·데일리)과 잡담·공지 채널은 제외.
# partition(":")으로 첫 콜론만 분리 → 이름의 공백 보존. ID는 isdigit로 방어.
def _parse_activity_channels(raw):
    result = {}
    for pair in raw.split(","):
        cid, sep, name = pair.partition(":")
        cid, name = cid.strip(), name.strip()
        if sep and cid.isdigit() and name:
            result[int(cid)] = name
    return result

CH_ACTIVITY = _parse_activity_channels(os.getenv("CH_ACTIVITY", ""))  # {channel_id: 표시이름}

# 소환 모집단에서 제외할 역할 ID. 봇은 member.bot으로 별도 제외.
EXCLUDE_ROLE_IDS = {
    int(x.strip()) for x in os.getenv("EXCLUDE_ROLE_IDS", "").split(",") if x.strip().isdigit()
}

for var, name in _CHANNEL_VARS.items():
    if not globals()[var]:
        logger.warning(f"{var} 환경변수가 설정되지 않았습니다. {name} 채널 기능이 비활성화됩니다.")
