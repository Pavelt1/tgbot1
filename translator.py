import requests

url = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
token = ""


def translate_word(word: str) -> str:
    param = {'key': token,
             'lang': 'ru-en',
             'text': word,
             'ui': 'ru'
             }
    response = requests.get(url=url, params=param).json()
    trans_word = response['def'][0]['tr'][0]['text']
    return trans_word