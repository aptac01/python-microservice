# python-microservice

***You can easily translate those docs (and, for that matter, any docstrings you'll find inside) into english with [online translator](https://translate.google.com/#view=home&op=translate&sl=ru&tl=en).
While I actively work on this - its gonna be in russian, mostly for my convenience.***

Пример json-rpc сервиса на python-flask и uwsgi, с возможностью выгружать метрики в prometheus и
регистрацией в consul.

python 3.7, 3.8, другие версии не тестировал

Текущие задачи описаны в привязанном project'е.
  
Обычно такие сервисы достаточно плотно работают с БД, однако, тут этот аспект опущен, т.к. СУБД бывают разные, и ситуации бывают разные. Для каждого случая лучше использовать свои инструменты.

Для взаимодействия с сервисом в режиме администрирования можно пользоваться скриптом service_manager2.sh, документация по нему: ". ./service_manager2.sh -h" (без кавычек).

Деплой сервиса предполагается таким образом:

0) установи unix-like операционную систему, на windows ничего не получится

1) установи python 3.7 в virtual environment (например в поддиректорию с самим сервисом)

2) проверь наличие pip (например, если environment развернут в */env, то из директории с сервисом: env/bin/python -m pip --version должен вывести версию, а не ругаться ошибками)

3) установи всё из requirements.txt в venv (например: env/bin/python -m pip install -r requirements.txt)

4) настрой конфигурационный файл; в скрипте service_manager2.sh в переменной config_filename (в самом начале) записан путь до него, образец конфига - env_wars.ini

5) ***проверь правильность параметров***, заданных в конфиге, обычно, ошибки - в путях (в самом конфиге или в пути до файла конфига)

6) Если всё сделано правильно - можно юзать(. ./service_manager2.sh -h). Если остались какие-то проблемы - проверяй:

 * положение звёзд на небе
 * фазу луны
 * что там видно в хрустальном шаре
 * какую картинку видно в кофейной гуще и сверься со справочником, что она означает
