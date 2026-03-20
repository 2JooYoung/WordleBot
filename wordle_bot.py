import discord
from discord.ext import tasks
import httpx
from bs4 import BeautifulSoup
import re
from datetime import date, datetime, time
import pytz
import os
from deep_translator import GoogleTranslator

# ===== 설정 =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MW_API_KEY = os.getenv("MW_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TIMEZONE = "Asia/Seoul"

# ===== 봇 설정 =====
intents = discord.Intents.default()
bot = discord.Client(intents=intents)


# ===== 오늘의 Wordle 단어 가져오기 (스크래핑) =====
async def get_todays_wordle_word():
    today = date.today()
    month = today.strftime("%B").lower()   # march
    day = today.day                         # 20
    year = today.year                       # 2026

    url = f"https://insider-gaming.com/todays-wordle-hints-answer-{month}-{day}-{year}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=headers, timeout=15, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")

            # 페이지 전체 텍스트에서 "WORD is a noun/verb/adjective" 패턴 찾기
            text = soup.get_text()
            match = re.search(r'\b([A-Z]{5})\s+is (a|an)\s+\w+', text)
            if match:
                word = match.group(1)
                print(f"단어 가져오기 성공: {word}")
                return word

    except Exception as e:
        print(f"단어 가져오기 실패: {e}")

    return None


# ===== 한국어 번역 =====
def translate_to_korean(text: str) -> str:
    try:
        return GoogleTranslator(source='en', target='ko').translate(text)
    except Exception as e:
        print(f"번역 실패: {e}")
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

            meaning = None
            shortdefs = entry.get("shortdef", [])
            if shortdefs:
                meaning = shortdefs[0]

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
                                        clean = re.sub(r'\{[^}]+\}', '', raw)
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
    meaning_kr = translate_to_korean(meaning) if meaning else None

    lines = [
        f"🟩 **오늘의 Wordle: `{word}`**",
        "",
    ]

    if meaning:
        lines.append(f"📖 **뜻 (EN):** {meaning}")
    if meaning_kr:
        lines.append(f"📖 **뜻 (KR):** {meaning_kr}")
    if not meaning:
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
@tasks.loop(time=time(hour=0, minute=0))
async def daily_post():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    print(f"[{now}] 매일 포스팅 실행")
    await post_wordle()


@bot.event
async def on_ready():
    print(f"봇 로그인: {bot.user}")
    # 한국시간 오후 8시 = UTC 11:00
    daily_post.change_interval(time=time(hour=11, minute=0))
    daily_post.start()


bot.run(DISCORD_TOKEN)
