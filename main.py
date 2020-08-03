import requests
import random
import json

from os import environ
from collections import deque
from datetime import datetime, timezone

from bot import BotHandler
from answers import answers 


class PlatinumRecord(object):
	"""docstring for PlatinumRecord"""
	def __init__(self, hunter, game, photo_id):
		super(PlatinumRecord, self).__init__()
		self.hunter = hunter
		self.game = game
		self.photo_id = photo_id

	def __str__(self):
		return "{} {}".format(self.hunter, self.game)

	def __repr__(self):
		return "PlatinumRecord({}, {}, {}, {})".format(self.hunter, self.game, self.chat_id, self.photo_id)

	def __eq__(self, other):
		return (self.hunter == other.hunter) and (self.game == other.game)

class Worker(object):
	"""docstring for Worker"""

	def __init__(self, bot, hour):
		super(Worker, self).__init__()
		self.bot = bot
		self.platinum = dict()
		self.where_run = list()
		self.offset = 0
		self.update_id = 0
		self.hour = hour
		self.can_update_ava = True
		self.commands = {'/help': self.help_command, '/start': self.start_command,
						'/showqueue': self.showqueue_command,
						'/deletegame': self.deletegame_command}
	
	def start(self):
		while True:
			self.bot.get_updates(self.offset)

			last_update = self.bot.get_last_update()

			self.update_id = last_update['update_id']
			if 'message' in last_update:
				self.message = last_update['message']
				last_chat_id = self.message['chat']['id']

				self.process_commands()

				if last_chat_id in self.where_run:
					self.process_message()

				self.offset = self.update_id

			now = datetime.now(timezone.utc).time()
			if (now.hour == self.hour) and self.can_update_ava:
				self.change_avatar()
				self.can_update_ava = False
			else:
				if now.hour - self.hour == 1:
					self.can_update_ava = True



	def process_message(self):
		last_chat_id = self.message['chat']['id']
		last_message_id = self.message['message_id']

		if 'photo' in self.message:
			isBotWasMentioned = self.botWasMentioned(self.message.get('caption_entities', list()), 
			self.message.get('caption'))

			if (self.update_id > self.offset):
				if isBotWasMentioned:
					photo_sizes = self.message['photo']
					file_id = photo_sizes[-1]['file_id']
					username = self.message['from']['username']
					game = self.get_game_name(self.message['caption'], self.message['caption_entities'][0])
					
					self.add_recrod(PlatinumRecord(username, game, file_id))
					self.bot.send_message(last_chat_id, random.choice(answers['photo']), last_message_id)

		if 'text' in self.message:
			last_message_text = self.message.get('text')

			isBotWasMentioned = self.botWasMentioned(self.message.get('entities', list()), last_message_text)

			if self.update_id > self.offset:
				if isBotWasMentioned:
					self.bot.send_message(last_chat_id, random.choice(answers['text']), last_message_id)

	def process_commands(self):
		chat_id = self.message['chat']['id']

		if 'text' in self.message:
			last_message_text = self.message.get('text')

			command = self.parse_commands(last_message_text, self.message.get('entities', list()))
			if self.update_id > self.offset:
				if command in self.commands:
					if command == "/start" :
						self.commands[command]()	
					elif chat_id in self.where_run:
						self.commands[command]()


	def add_recrod(self, record):
		chat_id = self.message['chat']['id']
		if chat_id in self.platinum:
			try:
				position = self.platinum[chat_id].index(record)
				self.platinum[chat_id][position].photo_id = record.photo_id
			except ValueError:
				self.platinum[chat_id].append(record)
		else:
			self.platinum[chat_id] = deque()
			self.platinum[chat_id].append(record)
	
	def get_game_name(self, text, entity):
		offset_mention = int(entity['offset'])
		len_mention = int(entity['length'])

		if offset_mention > 0:
			game = text[0 : offset_mention-1]
		else:
			len_text = len(text)
			game = text[offset_mention+len_mention+1:len_text]

		return game


	def botWasMentioned(self, entities, text):
		botName = "@" + self.bot.name
		for entity in entities:
			if entity['type'] == 'mention':
				offset_mention = int(entity['offset'])
				len_mention = int(entity['length'])

				if text[offset_mention:offset_mention+len_mention] == botName:
					return True
		
		return False
	
	def parse_commands(self, text, entities):
		for entity in entities:
			if entity['type'] == 'bot_command':
				words = text.split("@")
				if words[1] == self.bot.name:
					return words[0]
		return ""				

	def download_file(self, url):
	    resp = requests.get(url)
	    return resp.content

	def change_avatar(self):

		for chat_id in self.platinum.keys():
			try:
				record = self.platinum[chat_id].popleft()
			except IndexError:
				continue

			photo_url = self.bot.get_file_url(record.photo_id)
			photo = self.download_file(photo_url)
			self.bot.set_chat_photo(chat_id, photo)

			text = "Поздравляем @{} с платиной в игре \"{}\" !".format(record.hunter, record.game)
			self.bot.send_message(chat_id, text)

		return True


	def start_command(self):
		chat_id = self.message['chat']['id']

		if not chat_id in self.where_run:
			self.where_run.append(chat_id)
			self.bot.send_message(chat_id, "Да начнётся охота!")

	def help_command(self):
		text = """Для добавления фото в очередь нужно отправить в чат фото с комментарием следующего вида:

@{} <название игры>

Картинку необходимо подготовить таким образом, чтобы желаемая область была в центре. В идеале обрезать ее в пропорциях 1:1 оставив желаемую область.

У бота есть следующие команды:

\\start - запуск бота в чате

\\help - вывод справочной информации

\\showqueue - отобразить очередь выбитых платин на данный момент

\\deletegame - удалить последнюю добавленную тобой платину""".format(self.bot.name)

		chat_id = self.message['chat']['id']
		reply_to_message_id = self.message['message_id']

		return self.bot.send_message(chat_id, text, reply_to_message_id)

	def showqueue_command(self):
		chat_id = self.message['chat']['id']
		reply_to_message_id = self.message['message_id']

		text = "Очередь платин:\n"
		platinum_chat = self.platinum.get(chat_id, deque())
		text_record = "\n".join(str(record) for record in platinum_chat)

		return self.bot.send_message(chat_id, text+text_record, reply_to_message_id)

	def deletegame_command(self):
		chat_id = self.message['chat']['id']
		reply_to_message_id = self.message['message_id']
		username = self.message['from']['username']

		platinum_chat = self.platinum.get(chat_id, deque())
		records_user = [record for record in platinum_chat if record.hunter == username]

		try:
			self.platinum[chat_id].remove(records_user[-1])
			text = "Платина в игре {} игрока {} успешно удалена".format(records_user[-1].game, username)
		except IndexError:
			text = "Удалять у {} нечего. Поднажми!".format(username)
		except KeyError:
			text = "В данном чате ещё нет трофеев для удаления!"

		return self.bot.send_message(chat_id, text, reply_to_message_id)
		
def main():
	with open('config.json') as cfg:
		config = json.load(cfg)

	token = environ.get('TOKEN')
	bot = BotHandler(token)
	worker = Worker(bot, int(config['update_avatar_hour']))
	print("{}".format(bot.api_url))

	worker.start()


if __name__ == '__main__':  
	try:
		main()
	except KeyboardInterrupt:
		exit()