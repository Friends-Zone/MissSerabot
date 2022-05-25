import html

from typing import List

from telegram import Bot, Update, ParseMode
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

from cinderella import ALLOW_EXCL, dispatcher, CustomCommandHandler
from cinderella.modules.disable import DisableAbleCommandHandler
from cinderella.modules.helper_funcs.chat_status import user_admin, bot_can_delete, dev_plus, connection_status
from cinderella.modules.sql import cleaner_sql as sql

CMD_STARTERS = ('/', '!') if ALLOW_EXCL else '/'
BLUE_TEXT_CLEAN_GROUP = 15
CommandHandlerList = (CommandHandler, CustomCommandHandler, DisableAbleCommandHandler)
command_list = ["cleanbluetext", "ignorecleanbluetext", "unignorecleanbluetext", "listcleanbluetext", "ignoreglobalcleanbluetext", "unignoreglobalcleanbluetext"]

for handler_list in dispatcher.handlers:
    for handler in dispatcher.handlers[handler_list]:
        if any(isinstance(handler, cmd_handler) for cmd_handler in CommandHandlerList):
            command_list += handler.command


@run_async
def clean_blue_text_must_click(bot: Bot, update: Update):

    chat = update.effective_chat
    message = update.effective_message

    if chat.get_member(bot.id).can_delete_messages and sql.is_enabled(chat.id):
        fst_word = message.text.strip().split(None, 1)[0]

        if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):

            command = fst_word[1:].split('@')
            chat = update.effective_chat

            if ignored := sql.is_command_ignored(chat.id, command[0]):
                return

            if command[0] not in command_list:
                message.delete()


@run_async
@connection_status
@bot_can_delete
@user_admin
def set_blue_text_must_click(bot: Bot, update: Update, args: List[str]):

    chat = update.effective_chat
    message = update.effective_message

    if args:
        val = args[0].lower()
        if val in ["off", "no"]:
            sql.set_cleanbt(chat.id, False)
            reply = f"Bluetext cleaning has been disabled for <b>{html.escape(chat.title)}</b>"

            message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val in ["yes", "on"]:
            sql.set_cleanbt(chat.id, True)
            reply = f"Bluetext cleaning has been enabled for <b>{html.escape(chat.title)}</b>"

            message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "Invalid argument.Accepted values are 'yes', 'on', 'no', 'off'"
            message.reply_text(reply)
    else:
        clean_status = sql.is_enabled(chat.id)
        clean_status = "Enabled" if clean_status else "Disabled"
        reply = f"Bluetext cleaning for <b>{chat.title}</b> : <b>{clean_status}</b>"
        message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_bluetext_ignore(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message
    chat = update.effective_chat

    if args:
        val = args[0].lower()
        if added := sql.chat_ignore_command(chat.id, val):
            reply = f"<b>{args[0]}</b> has been added to bluetext cleaner ignore list."
        else:
            reply = "Command is already ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be ignored."
        message.reply_text(reply)


@run_async
@user_admin
def remove_bluetext_ignore(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message
    chat = update.effective_chat

    if args:
        val = args[0].lower()
        if removed := sql.chat_unignore_command(chat.id, val):
            reply = f"<b>{args[0]}</b> has been removed from bluetext cleaner ignore list."
        else:
            reply = "Command isn't ignored currently."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be unignored."
        message.reply_text(reply)


@run_async
@user_admin
def add_bluetext_ignore_global(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message

    if args:
        val = args[0].lower()
        if added := sql.global_ignore_command(val):
            reply = f"<b>{args[0]}</b> has been added to global bluetext cleaner ignore list."

        else:
            reply = "Command is already ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be ignored."
        message.reply_text(reply)


@run_async
@dev_plus
def remove_bluetext_ignore_global(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message

    if args:
        val = args[0].lower()
        if removed := sql.global_unignore_command(val):
            reply = f"<b>{args[0]}</b> has been removed from global bluetext cleaner ignore list."

        else:
            reply = "Command isn't ignored currently."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be unignored."
        message.reply_text(reply)


@run_async
@dev_plus
def bluetext_ignore_list(bot: Bot, update: Update):

    message = update.effective_message
    chat = update.effective_chat

    global_ignored_list, local_ignore_list = sql.get_all_ignored(chat.id)
    text = ""

    if global_ignored_list:
        text = "The following commands are currently ignored globally from bluetext cleaning :\n"

        for x in global_ignored_list:
            text += f" - <code>{x}</code>\n"

    if local_ignore_list:
        text += "\nThe following commands are currently ignored locally from bluetext cleaning :\n"

        for x in local_ignore_list:
            text += f" - <code>{x}</code>\n"

    if text == "":
        text = "No commands are currently ignored from bluetext cleaning."
        message.reply_text(text)
        return

    message.reply_text(text, parse_mode=ParseMode.HTML)
    return


__help__ = """
 - /cleanbluetext <on/off/yes/no> - clean commands after sending
 - /ignorecleanbluetext <word> - prevent auto cleaning of the command
 - /unignorecleanbluetext <word> - remove prevent auto cleaning of the command
 - /listcleanbluetext - list currently whitelisted commands
"""

SET_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("cleanbluetext", set_blue_text_must_click, pass_args=True)
ADD_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("ignorecleanbluetext", add_bluetext_ignore, pass_args=True)
REMOVE_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("unignorecleanbluetext", remove_bluetext_ignore, pass_args=True)
ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler("ignoreglobalcleanbluetext", add_bluetext_ignore_global, pass_args=True)
REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler("unignoreglobalcleanbluetext", remove_bluetext_ignore_global, pass_args=True)
LIST_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("listcleanbluetext", bluetext_ignore_list)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(Filters.command & Filters.group, clean_blue_text_must_click)

dispatcher.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(LIST_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)

__mod_name__ = "Bluetext Cleaning"
__handlers__ = [SET_CLEAN_BLUE_TEXT_HANDLER, ADD_CLEAN_BLUE_TEXT_HANDLER, REMOVE_CLEAN_BLUE_TEXT_HANDLER,
                ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER, REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
                LIST_CLEAN_BLUE_TEXT_HANDLER, (CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)]
