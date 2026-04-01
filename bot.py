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

# -----------------------------
# タグ判定
# -----------------------------
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

# -----------------------------
# 日時解析
# -----------------------------
def parse_datetime(title):
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)

    date_match = re.search(r'(\d{1,2})/(\d{1,2})', title)
    time_match = re.search(r'(\d{1,2}):(\d{2})', title)

    if not date_match or not time_match:
        return None, "未定"

    month, day = int(date_match.group(1)), int(date_match.group(2))
    hour, minute = int(time_match.group(1)), int(time_match.group(2))

    try:
        dt = now.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)

        if dt < now:
            dt = dt.replace(year=dt.year + 1)

        display = f"{month}/{day} {hour:02d}:{minute:02d}"
        return dt, display

    except:
        return None, "未定"

# -----------------------------
# 一覧作成
# -----------------------------
async def create_forum_list_embed():
    forum = bot.get_channel(FORUM_CHANNEL_ID)
    if not forum:
        return None

    threads = list(forum.threads)
    threads += [t async for t in forum.archived_threads(limit=50)]

    recruits = []

    for thread in threads:
        try:
            if is_closed(thread):
                continue

            category = get_category_from_tags(thread)
            if not category:
                continue

        starter_message = await thread.fetch_message(thread.id)
        owner_name = starter_message.author.display_name

            dt, display_time = parse_datetime(thread.name)

            recruits.append({
                "owner": owner_name,
                "datetime": dt,
                "display_time": display_time,
                "category": category,
                "url": thread.jump_url
            })

        except Exception as e:
            print(e)
            continue

    recruits.sort(key=lambda x: (x["datetime"] is None, x["datetime"]))

    embed = discord.Embed(title="🎣 募集中一覧", color=0x2f3136)

    for r in recruits:
        embed.add_field(
            name=f"■ {r['category']}",
            value=(
                f"👤 募集者: {r['owner']}\n"
                f"⌚ 日時: {r['display_time']}\n"
                f"🔗 [参加する]({r['url']})"
            ),
            inline=False
        )

    if not recruits:
        embed.description = "現在募集中の投稿はありません"

    return embed

# -----------------------------
# 投稿処理
# -----------------------------
async def update_list():
    channel = bot.get_channel(LIST_DISPLAY_CHANNEL_ID)
    if not channel:
        print("チャンネル取得失敗")
        return

    embed = await create_forum_list_embed()
    if not embed:
        print("Embed作成失敗")
        return

    await channel.send(embed=embed)

# -----------------------------
# 起動時処理（ここが重要）
# -----------------------------
@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")

    try:
        print("更新開始")
        await update_list()
        print("更新完了")
    except Exception as e:
        print(f"エラー: {e}")

    await bot.close()  # ← 超重要（終了）

# -----------------------------
# 実行
# -----------------------------
bot.run(TOKEN)
