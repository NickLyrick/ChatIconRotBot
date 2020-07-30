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

def main():  
	token = "1378900357:AAFSpECCd0kejOM22-RdQyK3RYCbXSKLxU8"
	greet_bot = BotHandler(token)  
	print("{}".format(greet_bot.api_url))
	
	now = datetime.datetime.now()
	offset = 0
	today = now.day
	hour = now.hour

	while True:
		greet_bot.get_updates(offset)

		last_update = greet_bot.get_last_update()

		print(last_update)

		last_update_id = last_update['update_id']
		last_message_id = last_update['message']['message_id']
		last_chat_id = last_update['message']['chat']['id']

		if 'photo' in last_update['message']:
			photo_sizes = last_update['message']['photo']
			file_id = photo_sizes[0]['file_id']
			
			print(greet_bot.get_file(file_id))
			
			isBotWasMentioned = botWasMentioned(last_update['message']['caption_entities'], last_update['message']['caption'], greet_bot.name)

			if (last_update_id > offset):
				if isBotWasMentioned:
					print(greet_bot.set_chat_photo(last_chat_id, {'type':'photo', 'media': file_id}))
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