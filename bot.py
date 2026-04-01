# =========================
# 一覧作成（日時非表示版）
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

    # ソート（内部ではそのまま使う）
    kasago.sort(key=lambda x: (x["datetime"] is None, x["datetime"]))
    chigofugu.sort(key=lambda x: (x["datetime"] is None, x["datetime"]))

    embed = discord.Embed(title="🎣 募集中一覧", color=0x2f3136)

    # カサゴ
    if kasago:
        text = ""
        for r in kasago:
            text += (
                f"👤 {r['owner']}\n"
                f"🔗 {r['url']}\n\n"
            )
    else:
        text = "現在募集中なし"

    embed.add_field(
        name="🐟 カサゴ 募集一覧",
        value=text,
        inline=False
    )

    # チゴフグ
    if chigofugu:
        text = ""
        for r in chigofugu:
            text += (
                f"👤 {r['owner']}\n"
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
