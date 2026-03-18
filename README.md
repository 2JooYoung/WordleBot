# WordleBot

> 매일 오늘의 Wordle 단어, 뜻, 예문을 디스코드 채널에 자동으로 올려주는 봇

---

## 왜 만들었나?

친구들이랑 디스코드에서 매일 Wordle을 같이 하는데,  
끝나고 나면 "오늘 단어가 뭐였지? 무슨 뜻이야?" 하는 순간이 생겨서 만들습니다.

매일 정해진 시간에 자동으로 업데이트:

```
🟩 오늘의 Wordle: CRANE

📖 뜻: a large machine used for lifting and moving heavy objects
💬 예문: The crane lifted the steel beam into place.

🔗 오늘의 Wordle 하러 가기
📅 2026년 03월 18일
```

---


| 기술 | 용도 |
|------|------|
| Python + discord.py | 디스코드 봇 |
| NYT Wordle API | 오늘의 단어 가져오기 |
| Merriam-Webster API | 단어 뜻 & 예문 |
| Render.com | 24시간 무료 호스팅 |

---

## 기능

- 매일 자동으로 오늘의 Wordle 단어 포스팅
- 단어 뜻 (Merriam-Webster Collegiate Dictionary)
- 예문 포함
- 시간대 설정 가능 (현재 KST 기준)

---

## 설치 & 실행

```bash
pip install -r requirements.txt
```

환경변수 설정:
```
DISCORD_TOKEN=your_discord_bot_token
MW_API_KEY=your_merriam_webster_api_key
CHANNEL_ID=your_channel_id
```

실행:
```bash
python wordle_bot.py
```
