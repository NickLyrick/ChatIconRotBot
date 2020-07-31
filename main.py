import requests
import datetime
import random

from collections import deque

from bot import BotHandler
from answers import answers 


def botWasMentioned(entities, text, name):
	botName = "@" + name
	for entity in entities:
		if entity['type'] == 'mention':
			offset_mention = int(entity['offset'])
			len_mention = int(entity['length'])

			if text[offset_mention:offset_mention+len_mention] == botName:
				return True
	
	return False

def get_game_name(text, entity):
	offset_mention = int(entity['offset'])
	len_mention = int(entity['length'])

	if offset_mention > 0:
		game = text[0 : offset_mention-1]
	else:
		len_text = len(text)
		game = text[offset_mention+len_mention+1:len_text]

	return game
	

def download_file(url):
    resp = requests.get(url)
    return resp.content


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

def add_recrod(platinum, record):
	try:
		position = platinum.index(record)
		platinum[position].photo_id = record.photo_id
	except ValueError:
		platinum.append(record)
		

def main():  
	token = "1378900357:AAFSpECCd0kejOM22-RdQyK3RYCbXSKLxU8"
	greet_bot = BotHandler(token)  
	print("{}".format(greet_bot.api_url))
	
	now = datetime.datetime.now()
	offset = 0
	today = now.day
	hour = now.hour

	platinum = deque()

	while True:
		greet_bot.get_updates(offset)

		last_update = greet_bot.get_last_update()

		last_update_id = last_update['update_id']
		if 'message' in last_update:
			last_message = last_update['message']
			last_message_id = last_message['message_id']
			last_chat_id = last_message['chat']['id']

			if 'photo' in last_update['message']:
				isBotWasMentioned = botWasMentioned(last_message['caption_entities'], 
					last_message['caption'], greet_bot.name)

				if (last_update_id > offset):
					if isBotWasMentioned:
						photo_sizes = last_message['photo']
						file_id = photo_sizes[-1]['file_id']
						username = last_message['from']['username']
						game = get_game_name(last_message['caption'], last_message['caption_entities'][0])
						
						add_recrod(platinum, PlatinumRecord(username, game, file_id))
						print(platinum)

						# greet_bot.set_chat_photo(last_chat_id, download_file(greet_bot.get_file_url(file_id)))
					offset = last_update_id

			if 'text' in last_update['message']:
				last_message_text = last_update['message']['text']

				if 'entities' in last_update['message']:
					last_message_entities = last_update['message']['entities']
				else:
					last_message_entities = dict()

				isBotWasMentioned = botWasMentioned(last_message_entities, last_message_text, greet_bot.name)


				if (last_update_id > offset):
					if isBotWasMentioned:
						greet_bot.send_message(last_chat_id, random.choice(answers), last_message_id)
					offset = last_update_id

if __name__ == '__main__':  
	try:
		main()
	except KeyboardInterrupt:
		exit()