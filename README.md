# kubectl-get-job Study Bot

Discord 스터디 서버 운영을 위해 만든 Python 봇입니다.

기상 챌린지, 코딩테스트 인증, 데일리 기록, 주간 통계를 슬래시 커맨드와 정기 스케줄로 관리합니다.

## 기능

- 신규 멤버 입장 시 서버 활용 가이드 안내
- 기상 챌린지 참여자 모집
- 리액션 기반 참여 등록/취소
- 평일 기상 인증 스레드 생성
- 기상 미인증자 리마인드
- 코딩테스트 인증 스레드 생성
- 데일리 인증 기록
- 개인별 주간/누적 통계 조회
- 주간 전체 통계 발행

## 사용 기술

- Python
- discord.py
- APScheduler
- SQLite
- python-dotenv

## 프로젝트 구조

```text
.
├── bot.py                 # 봇 실행 진입점, 이벤트 핸들러, cog 로딩
├── scheduler.py           # 정기 실행 작업
├── database.py            # SQLite 연결 및 테이블 초기화
├── config.py              # 환경변수, 채널 ID, KST 시간 처리
├── run_once_recruit.py    # 기상 챌린지 모집 메시지 수동 발행 스크립트
├── cogs/
│   ├── wake.py            # /기상인증
│   ├── coding.py          # /코테인증
│   ├── daily.py           # /데일리인증
│   └── stats.py           # /통계
└── requirements.txt
```

## 실행 방법

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

기상 챌린지 모집 메시지만 수동으로 보내야 할 때는 아래 스크립트를 실행합니다.

```bash
python run_once_recruit.py
```

## 환경 변수

`.env` 파일 또는 실행 환경에 아래 값을 설정합니다.

```env
DISCORD_TOKEN=
GUILD_ID=

CH_WAKE=
CH_CODING=
CH_DAILY=
CH_STATS=
CH_FREE=
CH_WELCOME=

WELCOME_GUIDE_URL=
```

| 변수 | 설명 |
|---|---|
| `DISCORD_TOKEN` | Discord Bot Token |
| `GUILD_ID` | Discord 서버 ID |
| `CH_WAKE` | 기상 챌린지 채널 ID |
| `CH_CODING` | 코딩테스트 인증 채널 ID |
| `CH_DAILY` | 데일리 인증 채널 ID |
| `CH_STATS` | 통계 채널 ID |
| `CH_FREE` | 자유 채널 ID |
| `CH_WELCOME` | 신규 멤버 환영 채널 ID |
| `WELCOME_GUIDE_URL` | 서버 활용 가이드 링크 |

`DISCORD_TOKEN`은 필수입니다. 채널 ID가 비어 있으면 해당 채널을 사용하는 기능은 동작하지 않습니다.

## 데이터 저장

인증 기록은 로컬 SQLite 파일(`bot.db`)에 저장합니다.

- `weekly_participants`: 주간 기상 챌린지 참여자
- `wake_logs`: 기상 인증 기록
- `ct_logs`: 코딩테스트 인증 기록
- `daily_logs`: 데일리 인증 기록
- `wake_recruit_messages`: 기상 챌린지 모집 메시지
- `ct_threads`: 날짜별 코딩테스트 인증 스레드

## 주요 명령어

| 명령어 | 설명 |
|---|---|
| `/기상인증` | 기상 인증 사진을 등록합니다. |
| `/코테인증` | 코딩테스트 풀이 인증 사진을 등록합니다. |
| `/데일리인증` | 오늘 진행한 일을 텍스트로 기록합니다. |
| `/통계` | 개인별 주간/누적 인증 현황을 조회합니다. |

## 참고

- 스케줄러는 `Asia/Seoul` 기준으로 실행합니다.
- 인증 기록은 SQLite 날짜 조회와 맞추기 위해 KST 기준 offset 없는 datetime으로 저장합니다.
- 데이터가 로컬 `bot.db`에 저장되므로 서버를 옮길 때는 DB 파일 백업이 필요합니다.
