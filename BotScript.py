import requests
import datetime

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

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
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

		last_update_id = last_update['update_id']
		last_chat_text = last_update['message']['text']
		last_chat_id = last_update['message']['chat']['id']
		last_chat_name = last_update['message']['chat']['first_name']

		print("{}\n{}\n{}\n{}\n".format(last_update_id, last_chat_text, last_chat_id, last_chat_name))
		if (last_update_id > offset):
			greet_bot.send_message(last_chat_id, "Пошел нахуй")
			offset = last_update_id;

if __name__ == '__main__':  
	try:
		main()
	except KeyboardInterrupt:
		exit()