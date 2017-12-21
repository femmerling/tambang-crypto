import time
import telepot
from os import environ
from telepot.loop import MessageLoop

def set_default_config():
  environ.setdefault("TELEGRAM_BOT_TOKEN", "472836801:AAGQgDhB0dg471Nvqc9RjqiXZJ4K2qnieHQ") # @BabixBot hosted by Sendy

set_default_config()

#SET VALUE
TELEGRAM_BOT_TOKEN = environ.get('TELEGRAM_BOT_TOKEN')

bot = telepot.Bot(TELEGRAM_BOT_TOKEN)
def handle(msg):
  if msg['text'] == '/start':
    id = msg['from']['id']
    message = 'Telegram User ID: %s' % id
    bot.sendMessage(id, message)

MessageLoop(bot, handle).run_as_thread()
print('I\'m listening...')

while 1:
  time.sleep(1)