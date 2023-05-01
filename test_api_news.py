from requests import get

'''Получить новость с определённым id'''
print(get('http://127.0.0.1:5000/api/v2/news&1').json())
'''Получить все новости'''
print(get('http://127.0.0.1:5000/api/v2/news').json())
