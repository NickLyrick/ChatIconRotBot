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
	def __init__(self, hunter, game, chat_id, photo_id):
		super(PlatinumRecord, self).__init__()
		self.hunter = hunter
		self.game = game
		self.chat_id = chat_id
		self.photo_id = photo_id

	def __str__(self):
		return "{} {}".format(self.hunter, self.game)

	def __repr__(self):
		return "PlatinumRecord({}, {}, {}, {})".format(self.hunter, self.game, self.chat_id, self.photo_id)

	def __eq__(self, other):
		return (self.hunter == other.hunter) and (self.game == other.game) and (self.chat_id == other.chat_id)

class Worker(object):
	"""docstring for Worker"""
	def __init__(self, bot):
		super(Worker, self).__init__()
		self.bot = bot
		self.platinum = deque()
		self.offset = 0
		self.time_change = datetime.now(timezone.utc).time()
	
	def start(self):
		while True:
			self.bot.get_updates(self.offset)

			last_update = self.bot.get_last_update()

			last_update_id = last_update['update_id']
			if 'message' in last_update:
				last_message = last_update['message']
				last_message_id = last_message['message_id']
				last_chat_id = last_message['chat']['id']

				if 'photo' in last_update['message']:
					isBotWasMentioned = self.botWasMentioned(last_message['caption_entities'], 
						last_message['caption'])

					if (last_update_id > self.offset):
						if isBotWasMentioned:
							photo_sizes = last_message['photo']
							file_id = photo_sizes[-1]['file_id']
							username = last_message['from']['username']
							game = self.get_game_name(last_message['caption'], last_message['caption_entities'][0])
							
							self.add_recrod(PlatinumRecord(username, game, last_chat_id, file_id))
							self.bot.send_message(last_chat_id, random.choice(answers['photo']), last_message_id)
							print(self.platinum)

							
						self.offset = last_update_id

				if 'text' in last_update['message']:
					last_message_text = last_update['message']['text']

					if 'entities' in last_update['message']:
						last_message_entities = last_update['message']['entities']
					else:
						last_message_entities = dict()

					isBotWasMentioned = self.botWasMentioned(last_message_entities, last_message_text)


					if (last_update_id > self.offset):
						if isBotWasMentioned:
							self.bot.send_message(last_chat_id, random.choice(answers['text']), last_message_id)
						self.offset = last_update_id

			now = datetime.now(timezone.utc).time()
			if now.minute - self.time_change.minute == 1:
				self.change_avatar()
				self.time_change = now

	def add_recrod(self, record):
		try:
			position = self.platinum.index(record)
			self.platinum[position].photo_id = record.photo_id
		except ValueError:
			self.platinum.append(record)
	
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
	

	def download_file(self, url):
	    resp = requests.get(url)
	    return resp.content

	def change_avatar(self):
		try:
			record = self.platinum.popleft()
		except IndexError:
			return False

		photo_url = self.bot.get_file_url(record.photo_id)
		photo = self.download_file(photo_url)
		self.bot.set_chat_photo(record.chat_id, photo)

		return True


def main():

	with open('config.json') as cfg:
		config = json.load(cfg)

	token = environ.get('TOKEN')
	bot = BotHandler(token)
	worker = Worker(bot)
	print("{}".format(bot.api_url))

	worker.start()
	

if __name__ == '__main__':  
	try:
		main()
	except KeyboardInterrupt:
		exit()