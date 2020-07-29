import requests
import datetime
import random

from answers import answers 

botName = "@ChatIconRotBot"

class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=1000):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text, reply_to_message_id):
        params = {'chat_id': chat_id, 'text': text, 'reply_to_message_id': reply_to_message_id}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_last_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = get_result[len(get_result)]

        return last_update

    def set_chat_photo(self, chat_id, photo):
    	method = 'setChatPhoto'
    	params = {'chat_id': chat_id, 'photo': photo}

    	resp = requests.post(self.api_url + method, params)

    	return resp

def botWasMentioned(entities, text):
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

		if 'text' in last_update['message']:
			last_message_text = last_update['message']['text']

			if 'entities' in last_update['message']:
				last_message_entities = last_update['message']['entities']
			else:
				last_message_entities = dict()

			isBotWasMentioned = botWasMentioned(last_message_entities, last_message_text)


			if (last_update_id > offset):
				if isBotWasMentioned:
					greet_bot.send_message(last_chat_id, random.choice(answers), last_message_id)
				offset = last_update_id;

if __name__ == '__main__':  
	try:
		main()
	except KeyboardInterrupt:
		exit()