#!/usr/bin/env python
# coding=utf-8

from tgbot import TGBot
from tgbot.pluginbase import TGPluginBase, TGCommandBase
import argparse
import os


class PushItPlugin(TGPluginBase):
    def list_commands(self):
        return (
            TGCommandBase('token', self.token, 'view your API token'),
            TGCommandBase('revoke', self.revoke, 'revoke your API token and create a new one'),
            TGCommandBase('help', self.help, 'more information'),
        )

    def token(self, message, text):
        token = self.read_data(message.chat.id, 'token')
        if not token:
            token = self._new_token(message.chat.id)

        return self.bot.return_message(message.chat.id, '''\
You can use the following token to access the HTTP API:

*%s*

Please send /help command if you have any problem''' % token, parse_mode='Markdown')

    def revoke(self, message, text):
        token = self._new_token(message.chat.id)

        return self.bot.return_message(message.chat.id, '''\
Your _old_ token has been revoked.
You can now use the following token to access the HTTP API:

*%s*

Please send /help command if you have any problem''' % token, parse_mode='Markdown')

    def help(self, message, text):
        return self.bot.return_message(message.chat.id, u'''\
I'm PushIt Bot and I can help you integrate your scripts or website with Telegram.
Please read this manual before we begin:

 📖 http://fopina.github.com/tgbot-pushitbot/api-docs

Here is the commands list:

/token - view your API token
/revoke - revoke your API token and create a new one
''', parse_mode='Markdown')

    def chat(self, message, text):
        return self.bot.return_message(message.chat.id, u'''
I'm not really chatty. Give /help a try if you need something.
''')

    def _new_token(self, chat_id):
        token = os.urandom(16).encode('hex')
        self.save_data(chat_id, 'token', token)
        return token


def setup(db_url=None, token=None):
    p = PushItPlugin()
    tg = TGBot(
        token, plugins=[p],
        no_command=p, db_url=db_url,
    )
    return tg


def openshift_app():
    import os

    bot = setup(
        db_url='postgresql://%s:%s/%s' % (
            os.environ['OPENSHIFT_POSTGRESQL_DB_HOST'],
            os.environ['OPENSHIFT_POSTGRESQL_DB_PORT'],
            os.environ['PGDATABASE']
        ),
        token=os.environ['TGTOKEN']
    )
    bot.set_webhook('https://%s/update/%s' % (os.environ['OPENSHIFT_APP_DNS'], bot.token))

    from tgbot.webserver import wsgi_app
    return wsgi_app([bot])


def main():
    parser = build_parser()
    args = parser.parse_args()

    tg = setup(db_url=args.db_url, token=args.token)

    if args.list:
        tg.print_commands()
        return

    if args.create_db:
        tg.setup_db()
        print 'DB created'
        return

    tg.run_web(args.webhook[0], host='0.0.0.0', port=int(args.webhook[1]))


def build_parser():
    parser = argparse.ArgumentParser(description='Run PushItBot')

    parser.add_argument('--db_url', '-d', dest='db_url', default='sqlite:///pushitbot.sqlite3',
                        help='URL for database (default is sqlite:///pushitbot.sqlite3)')
    parser.add_argument('--list', '-l', dest='list', action='store_const',
                        const=True, default=False,
                        help='print commands (for BotFather)')
    parser.add_argument('--webhook', '-w', dest='webhook', nargs=2, metavar=('hook_url', 'port'),
                        help='use webhooks (instead of polling) - requires bottle')
    parser.add_argument('--create_db', dest='create_db', action='store_const',
                        const=True, default=False,
                        help='setup database')
    parser.add_argument('--token', '-t', dest='token',
                        help='token provided by @BotFather')
    return parser


if __name__ == '__main__':
    main()