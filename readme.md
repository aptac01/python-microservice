# python-microservice

Пример json-rpc сервиса на python-flask и uwsgi, с выгрузкой метрик в prometheus, 
регистрацией в consul.

python 3.7, 3.8, другие версии не тестировал

Текущие задачи описаны в привязанном project'е.
  
Обычно такие сервисы достаточно плотно работают с БД, однако, тут этот момент
опущен, т.к. СУБД бывают разные, и ситуации бывают разные. Для каждого случая 
лучше использовать свои инструменты.

Для взаимодействия с сервисом в режиме администрирования можно пользоваться 
скриптом service_manager2.sh, документация по нему: ". ./service_manager2.sh -h"
(без кавычек).

Деплой сервиса предполагается таким образом:
1) ставим python 3.7 в virtual environment (например в поддиректорию с самим 
сервисом)

2) проверяем наличие pip (например,
если environment развернут в */env, то из директории с сервисом:
env/bin/python -m pip --version должен вывести версию, а не ругаться)

3) в venv ставим всё из requirements.txt (например:
env/bin/python -m pip install -r requirements.txt)

4) настраиваем конфиг, в скрипте service_manager2.sh в переменной 
config_filename (в самом начале) записан путь до него, образец конфига - env_wars.ini

5) проверяем правильность параметров, заданных в конфиге, обычно, ошибки - в путях (в самом конфиге и в пути до конфига)

6) Если всё сделали правильно - можно юзать(. ./service_manager2.sh -h). Если остались какие-то проблемы - проверяем:

 * положение звёзд на небе
 * фазу луны
 * что там видно в хрустальном шаре
 * какую картинку видно в кофейной гуще и свертесь со справочником, что она означает
