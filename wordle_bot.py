import discord
from discord.ext import tasks
import httpx
import asyncio
from datetime import date, datetime, time
import pytz
import os

# ===== 설정 =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")         # 디스코드 봇 토큰
MW_API_KEY = os.getenv("MW_API_KEY")               # Merriam-Webster API 키
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))          # 포스팅할 채널 ID
TIMEZONE = "Asia/Seoul"                             # 포스팅 시간대
POST_TIME = time(hour=9, minute=0)                  # 매일 오전 9시에 포스팅

# ===== 봇 설정 =====
intents = discord.Intents.default()
bot = discord.Client(intents=intents)


# ===== 오늘의 Wordle 단어 가져오기 =====
async def get_todays_wordle_word():
    today = date.today().isoformat()
    url = f"https://www.nytimes.com/svc/wordle/v2/{today}.json"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, timeout=10)
            data = r.json()
            return data.get("solution", "").upper()
        except Exception as e:
            print(f"Wordle 단어 가져오기 실패: {e}")
            return None


# ===== 단어 뜻/예문 가져오기 (Merriam-Webster) =====
async def get_definition(word: str):
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word.lower()}?key={MW_API_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, timeout=10)
            data = r.json()

            if not data or not isinstance(data[0], dict):
                return None, None

            entry = data[0]

            # 뜻 가져오기
            meaning = None
            shortdefs = entry.get("shortdef", [])
            if shortdefs:
                meaning = shortdefs[0]

            # 예문 가져오기
            example = None
            try:
                defs = entry.get("def", [])
                for d in defs:
                    for sseq in d.get("sseq", []):
                        for sense in sseq:
                            if sense[0] == "sense":
                                dt_list = sense[1].get("dt", [])
                                for dt in dt_list:
                                    if dt[0] == "vis":
                                        raw = dt[1][0].get("t", "")
                                        # {it}, {/it} 같은 태그 제거
                                        clean = raw.replace("{it}", "").replace("{/it}", "").replace("{ldquo}", '"').replace("{rdquo}", '"')
                                        example = clean
                                        break
                                if example:
                                    break
                        if example:
                            break
            except Exception:
                pass

            return meaning, example

        except Exception as e:
            print(f"뜻 가져오기 실패: {e}")
            return None, None


# ===== 채널에 포스팅 =====
async def post_wordle():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("채널을 찾을 수 없어요.")
        return

    word = await get_todays_wordle_word()
    if not word:
        await channel.send("⚠️ 오늘의 Wordle 단어를 가져오지 못했어요.")
        return

    meaning, example = await get_definition(word)

    # 메시지 구성
    lines = [
        f"🟩 **오늘의 Wordle: `{word}`**",
        "",
    ]

    if meaning:
        lines.append(f"📖 **뜻:** {meaning}")
    else:
        lines.append("📖 **뜻:** (정보 없음)")

    if example:
        lines.append(f"💬 **예문:** *{example}*")

    lines += [
        "",
        f"🔗 [오늘의 Wordle 하러 가기](https://www.nytimes.com/games/wordle/index.html)",
        f"📅 {date.today().strftime('%Y년 %m월 %d일')}",
    ]

    await channel.send("\n".join(lines))
    print(f"[{datetime.now()}] 포스팅 완료: {word}")


# ===== 매일 정해진 시간에 실행 =====
@tasks.loop(time=POST_TIME)  # UTC 기준이므로 아래에서 timezone 보정
async def daily_post():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    print(f"[{now}] 매일 포스팅 실행")
    await post_wordle()


@bot.event
async def on_ready():
    print(f"봇 로그인: {bot.user}")
    # 한국시간 오전 9시 = UTC 00:00
    daily_post.change_interval(time=time(hour=1, minute=30))  # UTC 00:00 = KST 09:00
    daily_post.start()


bot.run(DISCORD_TOKEN)
