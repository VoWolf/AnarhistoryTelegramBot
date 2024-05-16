import time

from telebot.types import InlineKeyboardButton, Message, User

from MODULES.constants.reg_variables.BOT import GUARD
from MODULES.constants.reg_variables.MORPH import MORPH
from MODULES.database.models.stories import Stories, Views
from MODULES.domain.pre_send.call_data_handler import Call
from MODULES.domain.pre_send.page_compiler import PageLoader
from MODULES.domain.executors.graph_loader import Graph

from MODULES.database.models.users import Authors, Stats


def button(text, call_data) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=call_data)


class Exec(Call):
    def __init__(self, message: Message, user: User | None = None):
        self.message: Message = message
        self.user = message.from_user if user is None else user
        self.db_user = None
        self.load_db_user()

    def load_db_user(self):
        try:
            self.db_user = Authors.get(tg_id=self.user.id)
        except Exception as e:
            db_not_found_error = e
            stat = Stats.create()
            data = {
                'tg_id': self.user.id,
                'username': self.user.username,
                'stat': stat
            }
            self.db_user = Authors.create(**data)

    def send(self, data: dict):
        GUARD.send_message(chat_id=self.message.chat.id, **data)

    def edit(self, data: dict):
        try:
            GUARD.edit_message_text(chat_id=self.message.chat.id, message_id=self.message.id, **data)
        except Exception as e:
            error = e
            self.send(PageLoader(11)().to_dict)
            GUARD.edit_message_text(chat_id=self.message.chat.id, message_id=self.message.id+1, **data)

    def cancel(self, page):
        GUARD.clear_step_handler(self.message)
        page = getattr(self, page)
        page()

    def start(self):
        if self.db_user.is_regged:
            self.main()
            return
        self.send(PageLoader(1)().to_dict)

    def add_author_name(self):
        self.edit(PageLoader(2)().to_dict)
        GUARD.register_next_step_handler(self.message, callback=self.check_new_author_name)

    def check_new_author_name(self, message):
        GUARD.delete_message(self.message.chat.id, message.id)
        if len(message.text) > 16:
            self.edit(PageLoader(3)().to_dict)
            return

        other = Authors.select().where((Authors.author_name == message.text) & (Authors.tg_id != self.db_user.tg_id))
        if other:
            self.edit(PageLoader(4)().to_dict)
            return

        self.db_user.author_name = message.text
        self.db_user.is_regged = True
        Authors.save(self.db_user)
        self.edit(PageLoader(5)().to_dict)

    def main(self):
        self.edit(PageLoader(6)(
            self.db_user.author_name,
            self.db_user.stat.views,
            self.db_user.stat.respect,
            str(round((self.db_user.stat.respect / (self.db_user.stat.views + (1 if self.db_user.stat.views == 0 else 0)))*100, 2)).ljust(4, "0")
        ).to_dict)

    def change_author_name(self):
        self.edit(PageLoader(7)().to_dict)
        GUARD.register_next_step_handler(self.message, callback=self.check_changed_author_name)

    def check_changed_author_name(self, message):
        GUARD.delete_message(self.message.chat.id, message.id)
        if len(message.text) > 16:
            self.edit(PageLoader(8)().to_dict)
            return

        other = Authors.select().where((Authors.author_name == message.text) & (Authors.tg_id != self.db_user.tg_id))
        if other:
            self.edit(PageLoader(9)().to_dict)
            return

        self.db_user.author_name = message.text
        Authors.save(self.db_user)
        pld = PageLoader(10)
        for i in range(5, -1, -1):
            self.edit(pld(message.text, i).to_dict)
            time.sleep(1)
        self.main()

    def add_story(self):
        self.edit(PageLoader(12)().to_dict)
        GUARD.register_next_step_handler(self.message, callback=self.add_header)

    def add_header(self, message):
        GUARD.delete_message(self.message.chat.id, message.id)
        self.edit(PageLoader(13)().to_dict)
        GUARD.register_next_step_handler(self.message, self.check_text, message.text)

    def check_text(self, message, title):
        GUARD.delete_message(self.message.chat.id, message.id)
        stories = Stories.select()
        pld = PageLoader(14)
        grp = Graph(len(stories))
        for story in stories:
            same = 0
            for comp in zip(message.text.split(), story.text.split()):
                same += int(MORPH.parse(comp[0])[0].word == MORPH.parse(comp[1])[0].word)
            same_percent = (same / len(max([message.text.split(), story.text.split()], key=len))) * 100
            if same_percent < 89:
                grp += 1
                self.edit(pld(str(grp)).to_dict)
                continue
            self.final_add_story(False, '', '')
            return

        self.final_add_story(True, message.text, title)

    def final_add_story(self, add: bool, text, title):
        new = Stories(
            text=text,
            title=title,
            author=self.db_user
        )
        if add:
            new.save()
        self.edit(PageLoader(15)().to_dict)

    def next_story(self):
        v = list(map(lambda x: x.story.id, Views.select().where(Views.user == self.db_user)[:]))
        try:
            n: Stories = Stories.select().where((~Stories.id.in_(v)) & Stories.is_active)[0]
        except (IndexError, AttributeError):
            self.edit(PageLoader(16)().to_dict)
            return
        Views.create(user=self.db_user, story=n)
        n.author.stat.views += 1
        Stats.save(n.author.stat)

        pld = PageLoader(17)
        pld += [button('Указать уважение', f'respect 1 {n.author.id}')]
        if self.db_user.is_admin:
            pld += [button('Скрыть историю', f'hide_story {n.id}')]
        self.edit(pld(
            n.title,
            n.author.author_name,
            n.text
        ).to_dict)

    def hide_story(self, story_id):
        try:
            strr = Stories.get_by_id(int(story_id))
            strr.is_active = False
            Stories.save(strr)
            self.edit(PageLoader(19)().to_dict)
            time.sleep(1)
            self.send(PageLoader(11)().to_dict)
        except Exception as e:
            print(e)
        self.next_story()

    def clear_views(self):
        for v in Views.select().where(Views.user == self.db_user):
            try:
                Views.delete_by_id(v.id)
            except Exception as e:
                err = e
        self.edit(PageLoader(20)().to_dict)

    def respect(self, amount, author_id):
        try:
            ath = Authors.get_by_id(author_id)
            ath.stat.respect += int(amount)
            Stats.save(ath.stat)
            self.edit(PageLoader(18)(ath.author_name).to_dict)
            time.sleep(1)
        except Exception as e:
            print(e)
            error = e
        self.next_story()