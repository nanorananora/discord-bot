import os
import discord
from discord.ext import commands
import datetime
import re

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

FORUM_CHANNEL_ID = 1486702737008885781
LIST_DISPLAY_CHANNEL_ID = 1467530008518983968

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# タグ判定
# =========================
def get_category_from_tags(thread):
    for tag in thread.applied_tags:
        if tag.name == "カサゴ募集中":
            return "カサゴ"
        if tag.name == "チゴフグ募集中":
            return "チゴフグ"
    return None

def is_closed(thread):
    for tag in thread.applied_tags:
        if tag.name == "募集〆":
            return True
    return False

# =========================
# 日時解析（終了時間対応）
# =========================
def parse_datetime(title):
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)

    date_match = re.search(r'(\d{1,2})/(\d{1,2})', title)
    time_match = re.search(r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', title)

    if not date_match or not time_match:
        return None, "未定"

    month, day = int(date_match.group(1)), int(date_match.group(2))
    sh, sm = int(time_match.group(1)), int(time_match.group(2))
    eh, em = int(time_match.group(3)), int(time_match.group(4))

    try:
        dt = now.replace(month=month, day=day, hour=sh, minute=sm, second=0, microsecond=0)

        if dt < now:
            dt = dt.replace(year=dt.year + 1)

        # 曜日
        week = ["月", "火", "水", "木", "金", "土", "日"]
        wd = week[dt.weekday()]

        display = f"{month}/{day}({wd}){sh:02d}:{sm:02d}-{eh:02d}:{em:02d}"
        return dt, display

    except Exception as e:
        print(f"日時解析エラー: {e}")
        return None, "未定"

# =========================
# 一覧作成（カテゴリ分け）
# =========================
async def create_forum_list_embed():
    forum = bot.get_channel(FORUM_CHANNEL_ID)
    if not forum:
        print("フォーラム取得失敗")
        return None

    threads = list(forum.threads)
    threads += [t async for t in forum.archived_threads(limit=50)]

    kasago = []
    chigofugu = []

    for thread in threads:
        try:
            if is_closed(thread):
                continue

            category = get_category_from_tags(thread)
            if not category:
                continue

            try:
                starter_message = await thread.fetch_message(thread.id)
                owner_name = starter_message.author.display_name
            except:
                owner_name = "不明"

            dt, display_time = parse_datetime(thread.name)

            data = {
                "owner": owner_name,
                "datetime": dt,
                "display_time": display_time,
                "url": thread.jump_url
            }

            if category == "カサゴ":
                kasago.append(data)
            elif category == "チゴフグ":
                chigofugu.append(data)

        except Exception as e:
            print(e)
            continue

    # ソート
    kasago.sort(key=lambda x: (x["datetime"] is None, x["datetime"]))
    chigofugu.sort(key=lambda x: (x["datetime"] is None, x["datetime"]))

    embed = discord.Embed(title="🎣 募集中一覧", color=0x2f3136)

    # -------------------------
    # カサゴ
    # -------------------------
    if kasago:
        text = ""
        for r in kasago:
            text += (
                f"👤 {r['owner']}\n"
                f"⌚ {r['display_time']}\n"
                f"🔗 {r['url']}\n\n"
            )
    else:
        text = "現在募集中なし"

    embed.add_field(
        name="🐟 カサゴ 募集一覧",
        value=text,
        inline=False
    )

    # -------------------------
    # チゴフグ
    # -------------------------
    if chigofugu:
        text = ""
        for r in chigofugu:
            text += (
                f"👤 {r['owner']}\n"
                f"⌚ {r['display_time']}\n"
                f"🔗 {r['url']}\n\n"
            )
    else:
        text = "現在募集中なし"

    embed.add_field(
        name="🐡 チゴフグ 募集一覧",
        value=text,
        inline=False
    )

    return embed

# =========================
# 投稿
# =========================
async def update_list():
    channel = bot.get_channel(LIST_DISPLAY_CHANNEL_ID)
    if not channel:
        print("チャンネル取得失敗")
        return

    embed = await create_forum_list_embed()
    if not embed:
        return

    await channel.send(embed=embed)

# =========================
# 起動
# =========================
@bot.event
async def on_ready():
    print("起動完了")

    try:
        await update_list()
    except Exception as e:
        print(e)

    await bot.close()

bot.run(TOKEN)
