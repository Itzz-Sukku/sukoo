from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

from IstkharMusic import YouTube, app
from IstkharMusic.core.call import Istu as Anony
from IstkharMusic.misc import db, SUDOERS
from IstkharMusic.utils import AdminRightsCheck, seconds_to_min
from IstkharMusic.utils.inline import close_markup
from config import BANNED_USERS

@app.on_message(
    filters.command(["seek", "cseek", "seekback", "cseekback"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def seek_comm(cli, message: Message, _, chat_id):
    if len(message.command) == 1:
        return await message.reply_text(_["admin_20"])
    query = message.text.split(None, 1)[1].strip()
    if not query.isnumeric():
        return await message.reply_text(_["admin_21"])
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await message.reply_text(_["admin_22"])
    file_path = playing[0]["file"]
    duration_played = int(playing[0]["played"])
    duration_to_skip = int(query)
    duration = playing[0]["dur"]
    if message.command[0][-2] == "c":
        if (duration_played - duration_to_skip) <= 10:
            return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played - duration_to_skip + 1
    else:
        if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
            return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played + duration_to_skip + 1
    mystic = await message.reply_text(_["admin_24"])
    if "vid_" in file_path:
        n, file_path = await YouTube.video(playing[0]["vidid"], True)
        if n == 0:
            return await message.reply_text(_["admin_22"])
    check = (playing[0]).get("speed_path")
    if check:
        file_path = check
    if "index_" in file_path:
        file_path = playing[0]["vidid"]
    try:
        await Anony.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(to_seek),
            duration,
            playing[0]["streamtype"],
        )
    except:
        return await mystic.edit_text(_["admin_26"], reply_markup=close_markup(_))
    if message.command[0][-2] == "c":
        db[chat_id][0]["played"] -= duration_to_skip
    else:
        db[chat_id][0]["played"] += duration_to_skip
    await mystic.edit_text(
        text=_["admin_25"].format(seconds_to_min(to_seek), message.from_user.mention),
        reply_markup=close_markup(_),
    )


#__________________________________[ SEEK AND SEEKBACK CALLBACKS ]_____________________________________

async def check_callback_admin(client, callback_query: CallbackQuery):
    if callback_query.from_user.id in BANNED_USERS:
        await callback_query.answer(
            "🚫 ʏᴏᴜ'ʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ!", show_alert=True
        )
        return False
    
    if callback_query.from_user.id in SUDOERS:
        return True
    
    try:
        chat_id = callback_query.message.chat.id
        member = await app.get_chat_member(chat_id, callback_query.from_user.id)
        if member.privileges and member.privileges.can_manage_video_chats:
            return True
    except Exception as e:
        print(f"Error checking admin status: {e}")
    
    await callback_query.answer(
        "ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛ's\n\nʀᴇʟᴏᴀᴅ ᴀᴅᴍɪɴs ᴄᴀᴄʜᴇ ᴠɪᴀ : /reload ",
        show_alert=True
    )
    return False


@app.on_callback_query(filters.regex("seek_forward_20"))
async def seek_forward_20_cb(client, callback_query: CallbackQuery):
    if not await check_callback_admin(client, callback_query):
        return

    try:
        chat_id = callback_query.message.chat.id
        playing = db.get(chat_id)

        if not playing or int(playing[0]["seconds"]) == 0:
            return await callback_query.answer(
                "🚫 ʙᴏᴛ ɪs ɴᴏᴛ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ!", show_alert=True
            )

        duration_seconds = int(playing[0]["seconds"])
        duration_played = int(playing[0]["played"])
        duration_to_skip = 20
        duration_str = seconds_to_min(duration_seconds)
        file_path = playing[0]["file"]

        if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
            return await callback_query.answer(
                f"⛔ ᴛᴏᴏ ᴄʟᴏsᴇ ᴛᴏ ᴛʜᴇ ᴇɴᴅ.\n\n▶️ ᴘʟᴀʏᴇᴅ : {seconds_to_min(duration_played)} / {duration_str}",
                show_alert=True
            )

        to_seek = duration_played + duration_to_skip + 1

        if "vid_" in file_path:
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await callback_query.answer(
                    "⛔ ᴠɪᴅᴇᴏ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ!", show_alert=True
                )

        check = playing[0].get("speed_path")
        if check:
            file_path = check
        if "index_" in file_path:
            file_path = playing[0]["vidid"]

        await Anony.seek_stream(
            chat_id, file_path, seconds_to_min(to_seek), playing[0]["dur"], playing[0]["streamtype"]
        )

        db[chat_id][0]["played"] += duration_to_skip
        await callback_query.answer(
            f"✅ sᴛʀᴇᴀᴍ sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴇᴋᴇᴅ → 20 sᴇᴄs!\n\n▶️ ᴘʟᴀʏᴇᴅ : {seconds_to_min(db[chat_id][0]['played'])} / {duration_str}",
            show_alert=True
        )

    except Exception as e:
        print(f"Error in seek_forward_20_cb: {e}")
        await callback_query.answer("🚫 ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴇᴋ ғᴏʀᴡᴀʀᴅ!", show_alert=True)


@app.on_callback_query(filters.regex("seek_backward_20"))
async def seek_backward_20_cb(client, callback_query: CallbackQuery):
    if not await check_callback_admin(client, callback_query):
        return

    try:
        chat_id = callback_query.message.chat.id
        playing = db.get(chat_id)

        if not playing or int(playing[0]["seconds"]) == 0:
            return await callback_query.answer(
                "🚫 ʙᴏᴛ ɪs ɴᴏᴛ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ!", show_alert=True
            )

        duration_seconds = int(playing[0]["seconds"])
        duration_played = int(playing[0]["played"])
        duration_to_skip = 20
        duration_str = seconds_to_min(duration_seconds)
        file_path = playing[0]["file"]

        if (duration_played - duration_to_skip) <= 10:
            return await callback_query.answer(
                f"⛔ ᴛᴏᴏ ᴄʟᴏsᴇ ᴛᴏ ᴛʜᴇ sᴛᴀʀᴛ.\n\n▶️ ᴘʟᴀʏᴇᴅ : {seconds_to_min(duration_played)} / {duration_str}",
                show_alert=True
            )

        to_seek = duration_played - duration_to_skip + 1

        if "vid_" in file_path:
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await callback_query.answer(
                    "⛔ ᴠɪᴅᴇᴏ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ!", show_alert=True
                )

        check = playing[0].get("speed_path")
        if check:
            file_path = check
        if "index_" in file_path:
            file_path = playing[0]["vidid"]

        await Anony.seek_stream(
            chat_id, file_path, seconds_to_min(to_seek), playing[0]["dur"], playing[0]["streamtype"]
        )

        db[chat_id][0]["played"] -= duration_to_skip
        await callback_query.answer(
            f"✅ sᴛʀᴇᴀᴍ sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴇᴋᴇᴅ ʙᴀᴄᴋ → 20 sᴇᴄs!\n\n▶️ ᴘʟᴀʏᴇᴅ : {seconds_to_min(db[chat_id][0]['played'])} / {duration_str}",
            show_alert=True
        )

    except Exception as e:
        print(f"Error in seek_backward_20_cb: {e}")
        await callback_query.answer("🚫 ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴇᴋ ʙᴀᴄᴋᴡᴀʀᴅ!", show_alert=True)

