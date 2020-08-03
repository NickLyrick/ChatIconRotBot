import requests

class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self.api_file = "https://api.telegram.org/file/bot{}/".format(token)
        self.name = self.get_me()['username']

    def get_updates(self, offset=None, timeout=1000):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def get_me(self):
    	method = 'getMe'
    	params = {}
    	resp = requests.post(self.api_url + method, params)
    	result_json = resp.json()['result']
    	return result_json

    def send_message(self, chat_id, text, reply_to_message_id=None):
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
        params = {'chat_id': chat_id}
        files = {'photo': photo}

        resp = requests.post(self.api_url + method, data=params, files=files)

        return resp.json()

    def get_file(self, file_id):
    	method = 'getFile'
    	params = {'file_id': file_id}
    	
    	resp = requests.post(self.api_url + method, params)
    	result_json = resp.json()['result']
    	return result_json

    def get_file_url(self, file_id):
        file = self.get_file(file_id)

        return self.api_file + file['file_path']

    def delete_chat_photo(self, chat_id):
        method = 'deleteChatPhoto'
        params = {'chat_id': chat_id}

        resp = requests.post(self.api_url + method, params)

        resp = requests.post(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

        