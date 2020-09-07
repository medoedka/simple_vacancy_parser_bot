import config
import re
import requests
import telebot
from datetime import datetime
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'your_user_agent'
}


def date():
    '''Returns the current date'''

    months = ('января',
              'февраля',
              'марта',
              'апреля',
              'мая',
              'июня',
              'июля',
              'августа',
              'сентября',
              'октября',
              'ноября',
              'декабря')
    return str(datetime.now().day) + '\xa0' + str(months[datetime.now().month - 1])


def job_finder(jobs_webpage):
    '''Returns the list of links, leading to the vacancies'''

    jobs_webpage_html = requests.get(jobs_webpage, headers=headers)
    position = 0
    date_pattern = re.compile('vacancy-serp-item__publication-date">' + date())
    link_pattern = re.compile('href="(.*?)"')
    vacancies_list = []
    next_pos = date_pattern.search(jobs_webpage_html.text[position:])
    while next_pos is not None:
        position += next_pos.end()
        link = link_pattern.search(jobs_webpage_html.text[position:]).groups()[0]
        vacancies_list.append(link)
        next_pos = date_pattern.search(jobs_webpage_html.text[position:])
    vacancies_list = [link for link in vacancies_list if 'http' in link]
    return vacancies_list


def get_vacancy_info(vacancy_link):
    '''Returns the description of the vacancy with the link to website'''

    vacancy_html = requests.get(vacancy_link, headers=headers).text
    vacancy_header_pattern = re.compile('og:description" content="(.*?)"')
    vacancy_header_html = vacancy_header_pattern.search(vacancy_html)
    if vacancy_header_html is not None:
        vacancy_header = vacancy_header_html.groups()[0]
    else:
        vacancy_header = '   '
    vacancy_description_pattern = re.compile('qa="vacancy-description"([\w\W]*?)"')
    vacancy_description_html = vacancy_description_pattern.search(vacancy_html)
    if vacancy_description_html is not None:
        vacancy_description = BeautifulSoup(vacancy_description_html.groups()[0], features='lxml').get_text()
    else:
        vacancy_description = '   '
    return f'*{vacancy_header}*' + '\n\n' + vacancy_description[1:] + '\n\n' + vacancy_link


bot = telebot.TeleBot(config.bot_api_token)


@bot.message_handler(commands=['start'])
def start_message(message):
    '''Greeting and further instructions'''

    bot.send_message(message.chat.id, 'Здравствуйте! Пожалуйста, введите интересующую вас должность!')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def vacancy_sender(message):
    '''Send the vacancies to the user'''

    job_title = '+'.join(message.text.split())
    vacancy_links = []
    jobs_url = f'https://jobs.tut.by/search/vacancy?clusters=true&area=1002&order_by=publication_time&search_field=name\
                 &enable_snippets=true&search_period=1&salary=&st=searchVacancy&text={job_title}'
    if not job_finder(jobs_url):
        bot.send_message(message.chat.id, f'Сегодня новых вакансий по запросу {job_title} нет :(')
    else:
        for vacancy_link in job_finder(jobs_url):
            vacancy_links.append(get_vacancy_info(vacancy_link))
        for vacancy_description in vacancy_links:
            bot.send_message(message.chat.id, vacancy_description, parse_mode="Markdown")


if __name__ == '__main__':
    bot.polling(none_stop=True)
