import requests
import datetime
import random

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


def download_file(url):
    resp = requests.get(url)
    return resp.content

def main():  
	token = "1378900357:AAFSpECCd0kejOM22-RdQyK3RYCbXSKLxU8"
	greet_bot = BotHandler(token)  
	print("{}".format(greet_bot.api_url))
	
	now = datetime.datetime.now()
	offset = 0
	today = now.day
	hour = now.hour

	photos_id = list()

	while True:
		greet_bot.get_updates(offset)

		last_update = greet_bot.get_last_update()

		last_update_id = last_update['update_id']
		last_message_id = last_update['message']['message_id']
		last_chat_id = last_update['message']['chat']['id']

		if 'photo' in last_update['message']:
			photo_sizes = last_update['message']['photo']
			file_id = photo_sizes[-1]['file_id']
			photos_id.append(file_id)
			
			isBotWasMentioned = botWasMentioned(last_update['message']['caption_entities'], 
				last_update['message']['caption'], greet_bot.name)

			if (last_update_id > offset):
				if isBotWasMentioned:
					greet_bot.set_chat_photo(last_chat_id, download_file(greet_bot.get_file_url(file_id)))
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