import json

import requests
from terminaltables import AsciiTable
from environs import Env


def get_vacancies_amount_hh(url, prog_languages):
    vacancies_amount = {}
    for lang in prog_languages:
        params = {
            'area': '1',
            "text": f"Программист {lang}",
            "text": f"Разработчик {lang}",
            "search_field": 'name',
            # "only_with_salary": "true",
            "per_page": 20,
            "period": 30
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        response_payload = response.json()
        vacancies_amount[lang] = response_payload["found"]
    return vacancies_amount


def get_vacancies_hh(url, prog_language):
    vacancies = []
    page = 0
    pages_number = 1
    while page < pages_number:
        params = {
            'area': '1',
            'page': page,
            "text": f"Программист {prog_language}",
            "text": f"Разработчик {prog_language}",
            "search_field": 'name',
            # "only_with_salary": "true",
            "per_page": 20,
            "period": 30
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        response_payload = response.json()

        for vacancy in response_payload["items"]:
            vacancies.append(vacancy)

        pages_number = response_payload["pages"]
        page += 1
    return vacancies


def get_vacancies_salary_hh(vacancies):
    vacancies_salaries = []
    for vacancy in vacancies:
        vacancies_salaries.append(predict_rub_salary_hh(vacancy))
    return vacancies_salaries


def predict_rub_salary_hh(vacancy):
    salary = vacancy["salary"]
    if not vacancy["salary"] :
        return None
    elif salary["currency"] != 'RUR':
        return None
    else:
        if not salary['from']:
            salary_from = None
        else:
            salary_from = salary['from']
        if not salary['to']:
            salary_to = None
        else:
            salary_to = salary['to']
    
    salary_rub = predict_salary(salary_from, salary_to)
    return salary_rub


def get_vacancies_statistics_hh(url, prog_languages):
    vacancies_amount = get_vacancies_amount_hh(url, prog_languages)
    vacancies_statistics = {}
    for lang in prog_languages:
        salary_list = get_vacancies_salary_hh(get_vacancies_hh(url, lang))
        vacancies_statistics[lang] = {
            "vacancies_found": vacancies_amount[lang],
            "vacancies_processed": count_vacancies_with_salary(salary_list),
            "average_salary": get_average_salary(salary_list)
        }
    return vacancies_statistics


def get_vacancies_amount_sj(url, prog_languages, superjob_token):
    headers = {
        'X-Api-App-Id': superjob_token
    }
    vacancies_amount = {}
    for lang in prog_languages:
        params = {
            'town': 4,
            'catalogues': 48,
            'keyword':f'{lang}',
            'period': 30
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        response_payload = response.json()
        vacancies_amount[lang] = response_payload["total"]
    return vacancies_amount


def get_vacancies_sj(url, prog_language, superjob_token):
    headers = {
        'X-Api-App-Id': superjob_token
    }
    vacancies = []
    page = 0
    next_page = True
    while next_page:
        params = {
            'town': 4,
            'catalogues': 48,
            'keyword':f'{prog_language}',
            'period': 30,
            'page': page
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        response_payload = response.json()

        for vacancy in response_payload['objects']:
            vacancies.append(vacancy)

        next_page = response_payload['more']
        page += 1
    return vacancies


def get_vacancies_salary_sj(vacancies):
    vacancies_salaries = []
    for vacancy in vacancies:
        vacancies_salaries.append(predict_rub_salary_sj(vacancy))
    return vacancies_salaries


def predict_rub_salary_sj(vacancy):
    if (vacancy['currency'] != 'rub'
        or vacancy['payment_from'] == 0
        and vacancy['payment_to'] == 0
        ):
        return None
    if vacancy['payment_from'] == 0:
        salary_from = None
    else:
        salary_from = vacancy['payment_from']
    if vacancy['payment_to'] == 0:
        salary_to = None
    else:
        salary_to = vacancy['payment_to']

    salary_rub = predict_salary(salary_from, salary_to)
    return salary_rub


def get_vacancies_statistics_sj(url, prog_languages, superjob_token):
    vacancies_amount = get_vacancies_amount_sj(url, prog_languages, superjob_token)
    vacancies_statistics = {}
    for lang in prog_languages:
        salary_list = get_vacancies_salary_sj(get_vacancies_sj(url, lang, superjob_token))
        vacancies_statistics[lang] = {
            "vacancies_found": vacancies_amount[lang],
            "vacancies_processed": count_vacancies_with_salary(salary_list),
            "average_salary": get_average_salary(salary_list)
        } 
    return vacancies_statistics


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        salary_rub = (salary_from + salary_to)/2
        return int(salary_rub)
    elif salary_from and not salary_to:
        salary_rub = salary_from * 1.2
        return int(salary_rub)
    elif not salary_from and salary_to:
        salary_rub = salary_to * 0.8
        return int(salary_rub)


def get_average_salary(vacancies_salaries):
    vacancies_salaries = [salary for salary in vacancies_salaries if salary]
    if len(vacancies_salaries) != 0:
        avg_salary = sum(vacancies_salaries)/len(vacancies_salaries)
        return int(avg_salary)
    else:
        return None


def count_vacancies_with_salary(vacancies_salaries):
    vacancies_salaries = [salary for salary in vacancies_salaries if salary]
    return len(vacancies_salaries)


def create_table(vacancies_statistics, name_table):
    table_data = [
        [
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        ]
    ]    
    for lang, statistic in vacancies_statistics.items():
        table_data.append(
            [
                lang,
                statistic["vacancies_found"],
                statistic["vacancies_processed"],
                statistic["average_salary"]
            ]
        )
    table = AsciiTable(table_data, name_table)
    return(table)


def main():
    env = Env()
    env.read_env()
    superjob_token = env.str('SJ_TOKEN')
    url_hh = 'https://api.hh.ru/vacancies'
    url_sj = 'https://api.superjob.ru/2.0/vacancies/'
    prog_languages = [
        'Python',
        'Java',
        'JavaScript',
        'Rust',
        'C#',
        'C++',
        'Go',
        'Kotlin',
        'C',
        'PHP'
    ]

    vacancies_statistics_hh = get_vacancies_statistics_hh(url_hh, prog_languages)
    vacancies_statistics_sj = get_vacancies_statistics_sj(url_sj, prog_languages, superjob_token)

    table_hh = create_table(vacancies_statistics_hh, 'HeadHunter Moscow')
    table_sj = create_table(vacancies_statistics_sj, 'SuperJob Moscow')
    print(table_hh.table)
    print()
    print(table_sj.table)


if __name__ == '__main__':
    main()

    
    

    


