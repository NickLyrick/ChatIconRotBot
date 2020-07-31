import requests
import datetime
import random
import json

from collections import deque

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
		return "PlatinumRecord({}, {}, {})".format(self.hunter, self.game, self.photo_id)

	def __eq__(self, other):
		return (self.hunter == other.hunter) and (self.game == other.game)

class Worker(object):
	"""docstring for Worker"""
	def __init__(self, bot):
		super(Worker, self).__init__()
		self.bot = bot
		self.platinum = deque()
		self.offset = 0
	
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
							
							self.add_recrod(PlatinumRecord(username, game, file_id))
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
							self.bot.send_message(last_chat_id, random.choice(answers), last_message_id)
						self.offset = last_update_id


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

	def change_avatar(self, chat_id):
		try:
			record = self.platinum.popleft()
		except IndexError:
			return False

		photo_url = self.bot.get_file_url(record.photo_id)
		photo = download_file(photo_url)
		self.bot.set_chat_photo(chat_id, photo)

		return True


def main():

	with open('config.json') as cfg:
		config = json.load(cfg)

	token = config['token']
	bot = BotHandler(token)
	worker = Worker(bot)
	print("{}".format(bot.api_url))
	
	now = datetime.datetime.now()
	today = now.day
	hour = now.hour

	worker.start()
	

if __name__ == '__main__':  
	try:
		main()
	except KeyboardInterrupt:
		exit()