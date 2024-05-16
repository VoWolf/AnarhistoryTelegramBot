from telebot.types import CallbackQuery


class Call:
    def __call__(self, call: CallbackQuery, obj=None):
        name, *args = call.data.split()
        print(name)
        call = getattr(obj if obj else self, name, self.default_call)

        call(*args)

    @staticmethod
    def default_call(*args, **kwargs):
        pass