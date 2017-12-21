import time
import telepot
from telepot.loop import MessageLoop

bot = telepot.Bot('472836801:AAGQgDhB0dg471Nvqc9RjqiXZJ4K2qnieHQ') # @BabixBot hosted by Sendy

def handle(msg):
  if msg['text'] == '/start':
    id = msg['from']['id']
    message = 'Telegram User ID: %s' % id
    bot.sendMessage(id, message)

MessageLoop(bot, handle).run_as_thread()
print('I\'m listening...')

while 1:
  time.sleep(1)