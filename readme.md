# python-microservice

Пример json-rpc сервиса на python-flask, с выгрузкой метрик в prometheus, 
регистрацией в консуле.

python 3.7, другие версии не тестировал
  
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
если environment развернут в */env, то:
env/bin/python -m pip --version должен вывести версию, а не ругаться)

3) в venv ставим всё из requirements.txt (например:
env/bin/python -m pip install -r requirements.txt)

4) настраиваем конфиг, в скрипте service_manager2.sh в переменной 
config_filename (в самом начале) записан путь до него, образец - env_wars.ini
