async def create_forum_list_embed(bot):
    forum = bot.get_channel(FORUM_CHANNEL_ID)
    if not forum:
        return None

    threads = list(forum.threads)
    threads += [t async for t in forum.archived_threads(limit=50)]

    recruits = []

    for thread in threads:
        try:
            # 終了スキップ
            if is_closed(thread):
                continue

            # カテゴリ（タグのみ）
            category = get_category_from_tags(thread)
            if not category:
                continue  # タグがないものは除外

            # 日時解析
            dt, display_time = parse_datetime(thread.name)

            recruits.append({
                "owner": thread.owner.display_name if thread.owner else "不明",
                "datetime": dt,
                "display_time": display_time,
                "category": category,
                "url": thread.jump_url
            })

        except:
            continue

    # 🔥 日時ソート（ここが追加ポイント）
    recruits.sort(key=lambda x: (x["datetime"] is None, x["datetime"]))

    # Embed作成
    embed = discord.Embed(
        title="🎣 募集中一覧",
        color=0x2f3136
    )

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
