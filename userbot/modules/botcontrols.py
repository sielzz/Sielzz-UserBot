# Copyright (C) 2021 Catuserbot <https://github.com/sandy1709/catuserbot>
# Ported by @mrismanaziz
# FROM Man-Userbot <https://github.com/mrismanaziz/Man-Userbot>
# t.me/SharingUserbot & t.me/Lunatic0de

import asyncio
from datetime import datetime

from telethon import events
from telethon.errors import BadRequestError, FloodWaitError, ForbiddenError

from userbot import BOT_USERNAME, BOTLOG, BOTLOG_CHATID, CMD_HELP, OWNER_ID, tgbot
from userbot.events import register
from userbot.modules.botmanagers import (
    ban_user_from_bot,
    get_user_and_reason,
    progress_str,
    unban_user_from_bot,
)
from userbot.modules.sql_helper.bot_blacklists import (
    check_is_black_list,
    get_all_bl_users,
)
from userbot.modules.sql_helper.bot_starters import (
    del_starter_from_db,
    get_all_starters,
)
from userbot.modules.sql_helper.globals import addgvar, delgvar, gvarstatus
from userbot.utils import _format, edit_delete, edit_or_reply, reply_id, time_formatter
from userbot.utils.logger import logging

LOGS = logging.getLogger(__name__)
botusername = gvarstatus("BOT_USERNAME") or BOT_USERNAME

@tgbot.on(events.NewMessage(pattern=r"^/help$", from_users=OWNER_ID))
async def bot_help(event):
    await event.reply(
        f"""**Perintah di Bot ini adalah:**\n
**NOTE: Perintah ini hanya berfungsi di **{botusername}**\n
 • **Command : **/uinfo <reply ke pesan>
 • **Function : **__Untuk Mencari Info Pengirim Pesan.__\n
 • **Command : **/ban <alasan> atau /ban <username/userid> <alasan>
 • **Function : **__Untuk Membanned Pengguna dari BOT.(Gunakan alasan saat ban)__\n
 • **Command : **/unban <alasan> atau /unban <username/userid>
 • **Function : **__Membuka Banned pengguna dari bot, agar bisa mengirim pesan lagi dibot.__
 • **NOTE : **__Untuk memeriksa daftar pengguna yang dibanned Ketik__ `.bblist`\n
 • **Command : **/broadcast
 • **Function : **__Balas ke pesan untuk diBroadcast ke setiap pengguna yang memulai bot Anda. Untuk mendapatkan daftar pengguna Ketik__ `.botuser`\n
 • **NOTE : ** Jika pengguna menghentikan/memblokir bot maka dia akan dihapus dari database Anda yaitu dia akan dihapus dari daftar bot_starters
"""
    )


@tgbot.on(events.NewMessage(pattern="^/broadcast$", from_users=OWNER_ID))
async def bot_broadcast(event):
    replied = await event.get_reply_message()
    if not replied:
        return await event.reply("**Mohon Balas Ke Pesan Yang ingin di Broadcast!**")
    start_ = datetime.now()
    br_cast = await replied.reply("`Broadcasting...`")
    blocked_users = []
    count = 0
    bot_users_count = len(get_all_starters())
    if bot_users_count == 0:
        return await event.reply("**Belum ada yang memulai bot Anda.** 🥺")
    users = get_all_starters()
    if users is None:
        return await event.reply("**Terjadi Error saat mengambil daftar pengguna.**")
    for user in users:
        try:
            await event.client.send_message(
                int(user.user_id), "🔊 You received a **new** Broadcast."
            )
            await event.client.send_message(int(user.user_id), replied)
            await asyncio.sleep(0.8)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except (BadRequestError, ValueError, ForbiddenError):
            del_starter_from_db(int(user.user_id))
        except Exception as e:
            LOGS.error(str(e))
            if BOTLOG:
                await event.client.send_message(
                    BOTLOG_CHATID, f"**Terjadi Error Saat Broadcast**\n`{e}`"
                )

        else:
            count += 1
            if count % 5 == 0:
                try:
                    prog_ = (
                        "🔊 **Broadcasting...**\n\n"
                        + progress_str(
                            total=bot_users_count,
                            current=count + len(blocked_users),
                        )
                        + f"\n\n• ✔️ **Berhasil** :  `{count}`\n"
                        + f"• ✖️ **Gagal** :  `{len(blocked_users)}`"
                    )
                    await br_cast.edit(prog_)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
    end_ = datetime.now()
    b_info = f"🔊 <b>Berhasil Mengirim Broadcast Pesan Ke</b> ➜ <code>{count}</code> <b>Users.</b>"
    if len(blocked_users) != 0:
        b_info += f"\n🚫 <code>{len(blocked_users)}</code> <b>user memblokir bot Anda baru-baru ini, jadi telah dihapus.</b>"
    b_info += f"\n⏳ <b>Dalam Waktu</b>  <code>{time_formatter((end_ - start_).seconds)}</code>."
    await br_cast.edit(b_info, parse_mode="html")


@register(outgoing=True, pattern=r"^\.botuser$")
async def ban_starters(event):
    "To get list of users who started bot."
    ulist = get_all_starters()
    if len(ulist) == 0:
        return await edit_delete(event, "**Belum ada yang memulai bot Anda.** 🥺")
    msg = "**Daftar Pengguna yang Memulai Bot Anda adalah:\n\n**"
    for user in ulist:
        msg += f"• **First Name:** {_format.mentionuser(user.first_name , user.user_id)}\n**User ID:** `{user.user_id}`\n**Tanggal: **{user.date}\n\n"
    await edit_or_reply(event, msg)


@tgbot.on(events.NewMessage(pattern="^/ban\\s+([\\s\\S]*)", from_users=OWNER_ID))
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id,
            "**Saya tidak dapat menemukan user untuk dibanned**",
            reply_to=reply_to,
        )
    if not reason:
        return await event.client.send_message(
            event.chat_id,
            "**Untuk Membanned User mohon Berikan alasan terlebih dahulu**",
            reply_to=reply_to,
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**ERROR:**\n`{e}`")
    if user_id == OWNER_ID:
        return await event.reply("**Saya Tidak Bisa Membanned Master** 🥺")
    check = check_is_black_list(user.id)
    if check:
        return await event.client.send_message(
            event.chat_id,
            f"**#Already_Banned**\
            \n**Pengguna sudah ada di Daftar Banned saya.**\
            \n**Alasan diBanned:** `{check.reason}`\
            \n**Tanggal:** `{check.date}`",
        )
    msg = await ban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@tgbot.on(events.NewMessage(pattern="^/unban(?:\\s|$)([\\s\\S]*)", from_users=OWNER_ID))
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id,
            "**Saya tidak dapat menemukan pengguna untuk di unbanned**",
            reply_to=reply_to,
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**Error:**\n`{e}`")
    check = check_is_black_list(user.id)
    if not check:
        return await event.client.send_message(
            event.chat_id,
            f"**#User_Not_Banned**\
            \n• {_format.mentionuser(user.first_name , user.id)} **Tidak ada di List Banned saya.**",
        )
    msg = await unban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@register(outgoing=True, pattern=r"^\.bblist$")
async def ban_starters(event):
    "To get list of users who are banned in bot."
    ulist = get_all_bl_users()
    if len(ulist) == 0:
        return await edit_delete(event, "**Belum ada yang dibanned di bot Anda.**")
    msg = "**Daftar Pengguna Yang diBanned di Bot Anda adalah:\n\n**"
    for user in ulist:
        msg += f"• **Nama:** {_format.mentionuser(user.first_name , user.chat_id)}\n**User ID:** `{user.chat_id}`\n**Tanggal: **{user.date}\n**Karena:** {user.reason}\n\n"
    await edit_or_reply(event, msg)


@register(outgoing=True, pattern=r"^\.botflood (on|off)$")
async def ban_antiflood(event):
    "To enable or disable bot antiflood."
    input_str = event.pattern_match.group(1)
    if input_str == "on":
        if gvarstatus("bot_flood") is not None:
            return await edit_delete(event, "**Bot Antiflood sudah diaktifkan.**")
        addgvar("bot_flood", True)
        await edit_delete(event, "**Bot Antiflood Berhasil diaktifkan.**")
    elif input_str == "off":
        if gvarstatus("bot_flood") is None:
            return await edit_delete(event, "**Bot Antiflood sudah dinonaktifkan.**")
        delgvar("bot_flood")
        await edit_delete(event, "**Bot Antiflood Berhasil dinonaktifkan.**")


CMD_HELP.update(
    {
        "pmbot": "**Plugin : **`pmbot`\
        \n\n  •  **Syntax :** `.botflood` <on/off>\
        \n  •  **Function : **Untuk mengaktfikan anti flood di bot.\
        \n\n  •  **Syntax :** `.bblist`\
        \n  •  **Function : **Untuk Melihat Daftar pengguna yang dibanned di bot Anda.\
        \n\n  •  **Syntax :** `.botuser`\
        \n  •  **Function : **Untuk Melihat Daftar Pengguna yang Memulai Bot Anda.\
        \n\n  •  **Cara Mengaktfikan Pesan Pribadi dengan Bot.**\
    "
    }
)
