# Copyright (C) 2021 Catuserbot <https://github.com/sandy1709/catuserbot>
# Ported by @mrismanaziz
# FROM Man-Userbot <https://github.com/mrismanaziz/Man-Userbot>
# t.me/SharingUserbot & t.me/Lunatic0de

import re
from collections import defaultdict
from datetime import datetime
from typing import Optional, Union

from telethon import Button, events
from telethon.errors import UserIsBlockedError
from telethon.events import CallbackQuery, StopPropagation
from telethon.utils import get_display_name

from userbot import (
    BOT_USERNAME,
    BOTLOG,
    BOTLOG_CHATID,
    CHANNEL,
    GROUP,
    SUDO_USERS,
    tgbot,
    user,
)
from userbot.core import check_owner, pool
from userbot.modules.botmanagers import ban_user_from_bot
from userbot.modules.sql_helper.bot_blacklists import check_is_black_list
from userbot.modules.sql_helper.bot_pms_sql import (
    add_user_to_db,
    get_user_id,
    get_user_logging,
    get_user_reply,
)
from userbot.modules.sql_helper.bot_starters import (
    add_starter_to_db,
    get_starter_details,
)
from userbot.modules.sql_helper.globals import delgvar, gvarstatus
from userbot.utils import _format, reply_id
from userbot.utils.logger import logging

LOGS = logging.getLogger(__name__)

botusername = gvarstatus("BOT_USERNAME") or BOT_USERNAME
OWNER_ID = user.id


class FloodConfig:
    BANNED_USERS = set()
    USERS = defaultdict(list)
    MESSAGES = 3
    SECONDS = 5
    ALERT = defaultdict(dict)
    AUTOBAN = 7


async def check_bot_started_users(user, event):
    if user.id == OWNER_ID:
        return
    check = get_starter_details(user.id)
    if check is None:
        start_date = str(datetime.now().strftime("%B %d, %Y"))
        notification = f"**First Name:** {_format.mentionuser(user.first_name , user.id)} \
                \n**User ID: **`{user.id}`\
                \n**Action: **Telah Memulai saya."
    else:
        start_date = check.date
        notification = f"**First Name:** {_format.mentionuser(user.first_name , user.id)}\
                \n**ID: **`{user.id}`\
                \n**Action: **Telah Me-Restart saya"
    try:
        add_starter_to_db(user.id, get_display_name(user), start_date, user.username)
    except Exception as e:
        LOGS.error(str(e))
    if BOTLOG:
        await event.client.send_message(BOTLOG_CHATID, notification)


@tgbot.on(
    events.NewMessage(
        pattern=f"^/start({botusername})?([\\s]+)?$", func=lambda e: e.is_private
    )
)
async def bot_start(event):
    chat = await event.get_chat()
    user = await event.client.get_me()
    if check_is_black_list(chat.id):
        return
    reply_to = await reply_id(event)
    mention = f"[{chat.first_name}](tg://user?id={chat.id})"
    my_mention = f"[{user.first_name}](tg://user?id={user.id})"
    first = chat.first_name
    last = chat.last_name
    fullname = f"{first} {last}" if last else first
    username = f"@{chat.username}" if chat.username else mention
    userid = chat.id
    my_first = user.first_name
    my_last = user.last_name
    my_fullname = f"{my_first} {my_last}" if my_last else my_first
    my_username = f"@{user.username}" if user.username else my_mention
    if chat.id != OWNER_ID:
        customstrmsg = gvarstatus("START_TEXT") or None
        if customstrmsg is not None:
            start_msg = customstrmsg.format(
                mention=mention,
                first=first,
                last=last,
                fullname=fullname,
                username=username,
                userid=userid,
                my_first=my_first,
                my_last=my_last,
                my_fullname=my_fullname,
                my_username=my_username,
                my_mention=my_mention,
            )
        else:
            start_msg = f"**👋 Hai** {mention}**!**\
                        \n\n**Saya adalah {my_first}** \
                        \n**Anda dapat Menghubungi [{user.first_name}](tg://user?id={user.id}) dari sini.**\
                        \n**Jangan Melakukan Spam Atau anda akan diBanned**\
                        \n\n**Powered by** [UserBot](https://github.com/mrismanaziz/Man-Userbot)"
        buttons = [
            (
                Button.url("ɢʀᴏᴜᴘ", f"https://t.me/{GROUP}"),
                Button.url(
                    "ᴄʜᴀɴɴᴇʟ",
                    f"https://t.me/{CHANNEL}",
                ),
            )
        ]
    else:
        start_msg = "**Halo Master!\
            \nApa ada yang bisa saya Bantu?\
            \nSilahkan Ketik /help Bila butuh Bantuan**"
        buttons = None
    try:
        await event.client.send_message(
            chat.id,
            start_msg,
            link_preview=False,
            buttons=buttons,
            reply_to=reply_to,
        )
    except Exception as e:
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"**ERROR:** Saat Pengguna memulai Bot anda.\\\x1f                \n`{e}`",
            )

    else:
        await check_bot_started_users(chat, event)


@tgbot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def bot_pms(event):
    chat = await event.get_chat()
    if check_is_black_list(chat.id):
        return
    if chat.id != OWNER_ID:
        msg = await event.forward_to(OWNER_ID)
        try:
            add_user_to_db(msg.id, get_display_name(chat), chat.id, event.id, 0, 0)
        except Exception as e:
            LOGS.error(str(e))
            if BOTLOG:
                await event.client.send_message(
                    BOTLOG_CHATID,
                    f"**ERROR:** Saat menyimpan detail pesan di database\n`{str(e)}`",
                )
    else:
        if event.text.startswith("/"):
            return
        reply_to = await reply_id(event)
        if reply_to is None:
            return
        users = get_user_id(reply_to)
        if users is None:
            return
        for usr in users:
            user_id = int(usr.chat_id)
            reply_msg = usr.reply_id
            user_name = usr.first_name
            break
        if user_id is not None:
            try:
                if event.media:
                    msg = await event.client.send_file(
                        user_id, event.media, caption=event.text, reply_to=reply_msg
                    )
                else:
                    msg = await event.client.send_message(
                        user_id, event.text, reply_to=reply_msg, link_preview=False
                    )
            except UserIsBlockedError:
                return await event.reply("❌ 𝗧𝗵𝗶𝘀 𝗯𝗼𝘁 𝘄𝗮𝘀 𝗯𝗹𝗼𝗰𝗸𝗲𝗱 𝗯𝘆 𝘁𝗵𝗲 𝘂𝘀𝗲𝗿.")
            except Exception as e:
                return await event.reply(f"**ERROR:** `{e}`")
            try:
                add_user_to_db(
                    reply_to, user_name, user_id, reply_msg, event.id, msg.id
                )
            except Exception as e:
                LOGS.error(str(e))
                if BOTLOG:
                    await event.client.send_message(
                        BOTLOG_CHATID,
                        f"**ERROR:** Saat menyimpan detail pesan di database\n`{e}`",
                    )


@tgbot.on(events.MessageEdited(outgoing=True))
async def bot_pms_edit(event):
    chat = await event.get_chat()
    if check_is_black_list(chat.id):
        return
    if chat.id != OWNER_ID:
        users = get_user_reply(event.id)
        if users is None:
            return
        reply_msg = None
        for user in users:
            if user.chat_id == str(chat.id):
                reply_msg = user.message_id
                break
        if reply_msg:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"⬆️ **Pesan ini Telah diedit oleh** {_format.mentionuser(get_display_name(chat) , chat.id)} **sebagai:**",
                reply_to=reply_msg,
            )
            msg = await event.forward_to(BOTLOG_CHATID)
            try:
                add_user_to_db(msg.id, get_display_name(chat), chat.id, event.id, 0, 0)
            except Exception as e:
                LOGS.error(str(e))
                if BOTLOG:
                    await event.client.send_message(
                        BOTLOG_CHATID,
                        f"**ERROR:** Saat Menyimpan Detail pesan di Database\n`{e}`",
                    )

    else:
        reply_to = await reply_id(event)
        if reply_to is not None:
            users = get_user_id(reply_to)
            result_id = 0
            if users is None:
                return
            for usr in users:
                if event.id == usr.logger_id:
                    user_id = int(usr.chat_id)
                    reply_msg = usr.reply_id
                    result_id = usr.result_id
                    break
            if result_id != 0:
                try:
                    await event.client.edit_message(
                        user_id, result_id, event.text, file=event.media
                    )
                except Exception as e:
                    LOGS.error(str(e))


@tgbot.on(events.MessageDeleted)
async def handler(event):
    for msg_id in event.deleted_ids:
        users_1 = get_user_reply(msg_id)
        users_2 = get_user_logging(msg_id)
        if users_2 is not None:
            result_id = 0
            for usr in users_2:
                if msg_id == usr.logger_id:
                    user_id = int(usr.chat_id)
                    result_id = usr.result_id
                    break
            if result_id != 0:
                try:
                    await event.client.delete_messages(user_id, result_id)
                except Exception as e:
                    LOGS.error(str(e))
        if users_1 is not None:
            reply_msg = None
            for user in users_1:
                if user.chat_id != OWNER_ID:
                    reply_msg = user.message_id
                    break
            try:
                if reply_msg:
                    users = get_user_id(reply_msg)
                    for usr in users:
                        user_id = int(usr.chat_id)
                        user_name = usr.first_name
                        break
                    if check_is_black_list(user_id):
                        return
                    await event.client.send_message(
                        BOTLOG_CHATID,
                        f"⬆️ **Pesan ini Telah dihapus oleh** {_format.mentionuser(user_name , user_id)}",
                        reply_to=reply_msg,
                    )
            except Exception as e:
                LOGS.error(str(e))


@tgbot.on(events.NewMessage(pattern="^/uinfo$", from_users=OWNER_ID))
async def bot_start(event):
    reply_to = await reply_id(event)
    if not reply_to:
        return await event.reply(
            "**Silahkan Balas ke pesan untuk mendapatkan info pesan**"
        )
    info_msg = await event.client.send_message(
        event.chat_id,
        "`🔎 Sedang Mencari di Database...`",
        reply_to=reply_to,
    )
    users = get_user_id(reply_to)
    if users is None:
        return await info_msg.edit(
            "**ERROR: Maaf! Tidak Dapat Menemukan pengguna ini di database saya 🥺**"
        )
    for usr in users:
        user_id = int(usr.chat_id)
        user_name = usr.first_name
        break
    if user_id is None:
        return await info_msg.edit(
            "**ERROR: Maaf! Tidak Dapat Menemukan pengguna ini di database saya 🥺**"
        )
    uinfo = f"**Pesan ini dikirim oleh**\
            \n**First Name:** {_format.mentionuser(user_name , user_id)}\
            \n**User ID:** `{user_id}`"
    await info_msg.edit(uinfo)


async def send_flood_alert(user_) -> None:
    buttons = [
        (
            Button.inline("🚫 BAN", data=f"bot_pm_ban_{user_.id}"),
            Button.inline(
                "➖ Bot Antiflood [OFF]",
                data="toggle_bot-antiflood_off",
            ),
        )
    ]
    found = False
    if FloodConfig.ALERT and (user_.id in FloodConfig.ALERT.keys()):
        found = True
        try:
            FloodConfig.ALERT[user_.id]["count"] += 1
        except KeyError:
            found = False
            FloodConfig.ALERT[user_.id]["count"] = 1
        except Exception as e:
            if BOTLOG:
                await tgbot.send_message(
                    BOTLOG_CHATID,
                    f"**ERROR:** Saat Memperbarui Jumlah Flood\n`{e}`",
                )

        flood_count = FloodConfig.ALERT[user_.id]["count"]
    else:
        flood_count = FloodConfig.ALERT[user_.id]["count"] = 1

    flood_msg = (
        r"⚠️ **#Flood_Warning**"
        "\n\n"
        f"  First Name: {_format.mentionuser(get_display_name(user_), user_.id)}"
        f"  User ID: `{user_.id}`\n"
        f"\n\n**Is spamming your bot !** ->  [ Flood Rate ({flood_count}) ]\n"
        "**Quick Action:** Diabaikan dari Bot untuk sementara waktu."
    )

    if found:
        if flood_count >= FloodConfig.AUTOBAN:
            if user_.id in SUDO_USERS:
                sudo_spam = (
                    f"**Sudo User** {_format.mentionuser(user_.first_name , user_.id)}:\n **User ID:** `{user_.id}`\n\n"
                    "**Membanjiri bot Anda!, Ketik** `.delsudo` **untuk menghapus pengguna dari Sudo.**"
                )
                if BOTLOG:
                    await tgbot.send_message(BOTLOG_CHATID, sudo_spam)
            else:
                await ban_user_from_bot(
                    user_,
                    f"**Anda Telah TerBanned Otomatis Karena** [Melebihi Batas Flood ({FloodConfig.AUTOBAN})]",
                )
                FloodConfig.USERS[user_.id].clear()
                FloodConfig.ALERT[user_.id].clear()
                FloodConfig.BANNED_USERS.remove(user_.id)
            return
        fa_id = FloodConfig.ALERT[user_.id].get("fa_id")
        if not fa_id:
            return
        try:
            msg_ = await tgbot.get_messages(BOTLOG_CHATID, fa_id)
            if msg_.text != flood_msg:
                await msg_.edit(flood_msg, buttons=buttons)
        except Exception as fa_id_err:
            LOGS.debug(fa_id_err)
            return
    else:
        if BOTLOG:
            fa_msg = await tgbot.send_message(
                BOTLOG_CHATID,
                flood_msg,
                buttons=buttons,
            )
        try:
            chat = await tgbot.get_entity(BOTLOG_CHATID)
            await tgbot.send_message(
                OWNER_ID,
                f"⚠️  **[Bot Flood Warning !](https://t.me/c/{chat.id}/{fa_msg.id})**",
            )
        except UserIsBlockedError:
            if BOTLOG:
                await tgbot.send_message(
                    BOTLOG_CHATID, "**Silahkan Buka Blokir Bot anda!**"
                )
    if FloodConfig.ALERT[user_.id].get("fa_id") is None and fa_msg:
        FloodConfig.ALERT[user_.id]["fa_id"] = fa_msg.id


@tgbot.on(CallbackQuery(data=re.compile(b"bot_pm_ban_([0-9]+)")))
@check_owner
async def bot_pm_ban_cb(c_q: CallbackQuery):
    user_id = int(c_q.pattern_match.group(1))
    try:
        user = await event.client.get_entity(user_id)
    except Exception as e:
        await c_q.answer(f"**ERROR:** `{e}`")
    else:
        await c_q.answer(f"**Banning UserID** -> `{user_id}`", alert=False)
        await ban_user_from_bot(user, "Spamming Bot")
        await c_q.edit(f"✅ **Berhasil dibanned** User ID: `{user_id}`")


def time_now() -> Union[float, int]:
    return datetime.timestamp(datetime.now())


@pool.run_in_thread
def is_flood(uid: int) -> Optional[bool]:
    """Checks if a user is flooding"""
    FloodConfig.USERS[uid].append(time_now())
    if (
        len(
            list(
                filter(
                    lambda x: time_now() - int(x) < FloodConfig.SECONDS,
                    FloodConfig.USERS[uid],
                )
            )
        )
        > FloodConfig.MESSAGES
    ):
        FloodConfig.USERS[uid] = list(
            filter(
                lambda x: time_now() - int(x) < FloodConfig.SECONDS,
                FloodConfig.USERS[uid],
            )
        )
        return True


@tgbot.on(CallbackQuery(data=re.compile(b"toggle_bot-antiflood_off$")))
@check_owner
async def settings_toggle(c_q: CallbackQuery):
    if gvarstatus("bot_flood") is None:
        return await c_q.answer("Bot Antiflood sudah dinonaktifkan.", alert=False)
    delgvar("bot_flood")
    await c_q.answer("Bot Antiflood dinonaktifkan.", alert=False)
    await c_q.edit("BOT_ANTILOOD sekarang dinonaktifkan!")


@tgbot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
@tgbot.on(events.MessageEdited(outgoing=True, func=lambda e: e.is_private))
async def antif_on_msg(event):
    if gvarstatus("bot_flood") is None:
        return
    chat = await event.get_chat()
    if chat.id == OWNER_ID:
        return
    user_id = chat.id
    if check_is_black_list(user_id):
        raise StopPropagation
    if await is_flood(user_id):
        await send_flood_alert(chat)
        FloodConfig.BANNED_USERS.add(user_id)
        raise StopPropagation
    if user_id in FloodConfig.BANNED_USERS:
        FloodConfig.BANNED_USERS.remove(user_id)
