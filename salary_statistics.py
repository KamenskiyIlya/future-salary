import requests
from terminaltables import AsciiTable
from environs import Env


def get_hh_vacancies(prog_language):
    url = 'https://api.hh.ru/vacancies'
    vacancies = []
    city_code = '1'
    page = 0
    pages_number = 1
    vacancies_per_page = 50  # не может быть больше 100
    period_in_days = 30
    while page < pages_number:
        params = {
            'area': city_code,
            'page': page,
            "text": f"Программист {prog_language}",
            "text": f"Разработчик {prog_language}",
            "search_field": 'name',
            "per_page": vacancies_per_page,
            "period": period_in_days
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        response_payload = response.json()

        for vacancy in response_payload["items"]:
            vacancies.append(vacancy)

        pages_number = response_payload["pages"]
        page += 1
    return vacancies


def get_hh_vacancies_salary(vacancies):
    vacancies_salaries = []
    for vacancy in vacancies:
        vacancies_salaries.append(predict_hh_rub_salary(vacancy))
    return vacancies_salaries


def predict_hh_rub_salary(vacancy):
    salary = vacancy["salary"]
    if not vacancy["salary"]:
        return
    elif salary["currency"] != 'RUR':
        return
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


def get_hh_vacancies_statistics(prog_languages):
    vacancies_statistics = {}
    for lang in prog_languages:
        vacancies = get_hh_vacancies(lang)
        salaries = get_hh_vacancies_salary(vacancies)
        vacancies_statistics[lang] = {
            "vacancies_found": len(vacancies),
            "vacancies_processed": count_vacancies_with_salary(salaries),
            "average_salary": get_average_salary(salaries)
        }
    return vacancies_statistics


def get_sj_vacancies(prog_language, superjob_token):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': superjob_token
    }
    vacancies = []
    city_code = 4
    industry_code = 48
    period_in_days = 30
    page = 0
    next_page = True
    while next_page:
        params = {
            'town': city_code,
            'catalogues': industry_code,
            'keyword': f'{prog_language}',
            'period': period_in_days,
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


def get_sj_vacancies_salary(vacancies):
    vacancies_salaries = []
    for vacancy in vacancies:
        vacancies_salaries.append(predict_sj_rub_salary(vacancy))
    return vacancies_salaries


def predict_sj_rub_salary(vacancy):
    if (
        vacancy['currency'] != 'rub'
        or vacancy['payment_from'] == 0
        and vacancy['payment_to'] == 0
    ):
        return
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


def get_sj_vacancies_statistics(prog_languages, superjob_token):
    vacancies_statistics = {}
    for lang in prog_languages:
        vacancies = get_sj_vacancies(lang, superjob_token)
        salaries = get_sj_vacancies_salary(vacancies)
        vacancies_statistics[lang] = {
            "vacancies_found": len(vacancies),
            "vacancies_processed": count_vacancies_with_salary(salaries),
            "average_salary": get_average_salary(salaries)
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
        return


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
    return (table)


def main():
    env = Env()
    env.read_env()
    superjob_token = env.str('SJ_TOKEN')
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

    hh_vacancies_statistics = get_hh_vacancies_statistics(prog_languages)
    sj_vacancies_statistics = get_sj_vacancies_statistics(
        prog_languages,
        superjob_token
    )

    hh_table = create_table(hh_vacancies_statistics, 'HeadHunter Moscow')
    sj_table = create_table(sj_vacancies_statistics, 'SuperJob Moscow')
    print(hh_table.table)
    print()
    print(sj_table.table)


if __name__ == '__main__':
    main()
