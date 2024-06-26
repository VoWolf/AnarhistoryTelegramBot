import json

import telebot.apihelper
from telebot.types import InlineKeyboardMarkup

from MODULES.constants.reg_variables.BOT import GUARD
from telebot.types import InlineKeyboardButton

from MODULES.domain.pre_send.page_compiler import PageLoader


def button(text, call_data) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=call_data)


def send(chat_id, type, kwargs_json, markup=InlineKeyboardMarkup(), **additional_buttons: list[InlineKeyboardButton]):
    kwargs = json.loads(kwargs_json)
    for row in additional_buttons.values():
        markup.row(row)

    match type:
        case 'text':
            GUARD.send_message(chat_id=chat_id, **kwargs, reply_markup=markup)
        case 'photo':
            GUARD.send_photo(chat_id=chat_id, **kwargs, reply_markup=markup)
        case 'audio':
            GUARD.send_audio(chat_id=chat_id, **kwargs, reply_markup=markup)
        case 'document':
            GUARD.send_document(chat_id=chat_id, **kwargs, reply_markup=markup)
        case 'video':
            GUARD.send_video(chat_id=chat_id, **kwargs, reply_markup=markup)
        case 'animation':
            GUARD.send_animation(chat_id=chat_id, **kwargs, reply_markup=markup)
        case _:
            raise NotImplementedError(f'Тип сообщений >>{type}<< не может быть отправлен данным методом!')


def safe_edit(func):
    def inner(mid, chat_id, *args, **kwargs):
        try:
            func(mid, chat_id, *args, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            send(chat_id, **PageLoader(11)(str(e)).to_dict)
            func(mid+1, chat_id, *args, **kwargs)

    return inner


@safe_edit
def edit(message_id, chat_id, type, kwargs_json, markup, **additional_buttons: list[InlineKeyboardButton]):
    kwargs = json.loads(kwargs_json)
    for row in additional_buttons.values():
        markup.row(row)

    match type:
        case 'text':
            GUARD.edit_message_text(message_id=message_id, chat_id=chat_id, **kwargs, reply_markup=markup)
        case _ as unsupported_type:
            raise NotImplementedError(f'Тип медиа ->{unsupported_type}<- не поддерживается!')


def remove_punctuation(s: str):
    punctuation = ['.', ',', '!', '?', '-', '(', ')', '"', "'"]
    for p in punctuation:
        s = s.replace(p, "")

    return s
