#!/bin/bash
# author: Alex Tamilin, popovalex402@gmail.com
# help по скрипту: . ./название_этого_файла.sh --help
# путь до конфига: config_filename (↓) 
config_filename="/home/aptac01/python_microservice/env_vars_w.ini"

help_message="
usage:
. ${BASH_SOURCE[0]} [flags] - предпочтительный вариант
${BASH_SOURCE[0]} [flags]   - возможно будет работать и так, но не тестировалось

Если поймали любой неизвестный аргумент - ничего не будет сделано
------------------------------------------------------------------------------------------------------

-a| --action     действие, их список - ниже
-c| --consul     bool(1|0), регистрация/дерегистрация в консуле при запуске/остановке
-r| --relog      bool(1|0), удалить существующие вторичные логи
-h| --help       если есть, будет показан этот меседж, без оглядки на остальные аргументы
------------------------------------------------------------------------------------------------------

Если для флаг(-c или -r) не был передан - вместо него будет использовано дефолтное значение. 
Дефолтные значения флагов - в конфиге:
-c  -  CONSUL_REG
-r  -  DELETE_RELOG_FILES

Если не указан --action - действия не будет.

Идея использования этого скрипта состоит в том, чтобы максимально упростить 
развертывание и использование микросервисов на python написанных с использованием 
Flask и запускаемых через uwsgi путем сведения всех управляющих манипуляций к 
одному файлу, а все настройки в один конфиг. 

--action:

start    - запускает сервис через uwsgi
stop     - останавливает сервис по pid-файлу, который в папке tmp
hardstop - убивает сервис по порту, прописанному в конфиге
restart  - выполняет stop, ждёт пока освободится порт, а затем start
status   - проверяет текущий статус сервиса предполагая, что конфиг 
	 после запуска не менялся, выводит текущий хэш из гита

tests    - прогоняет тесты описанные в service_manager_lib.test_api
relog    - обрабатывает логи, название которых указано в RELOG_FILES
         (в виде регулярного выражения).
         service_manager_lib.relog
	 результаты помещает в */relogs/:
	        exceptions.log       = непойманные исключения
	        internal_errors.log  = пойманные исключения и ошибки отданные клиенту
Конфиг:

скрипт читает параметры из конфигурационного файла, имя которого записано 
 в $config_filename. Ожидается, что он написан по таким правилам:
   1) переменные в формате:
        название_переменной=значение
        название_другой_переменной=значение
        (каждая на новой строке)
   2) значения переменных указываются без кавычек
   3) между названием переменной и знаком равно может быть 0 или несколько 
 пробелов (табы и другие пробельные символы не работают, только пробелы).
 Между знаком равно и значением, знаков пробела быть не может.
   4) можно писать коментарии, строка начинающаяся с символа "#" игнорируется
"
POSITIONAL=()

# Выводит переданный аргумент на экран и в лог-файл в качестве сообщения
log_msg() 
{
	echo $*
	echo $* >> ${nohup_out_log}
}

# список переменных из конфига делает переменными среды
# аргументы:
# первый - путь до файла с конфигом, полный или относительно текущей папки
export_env_vars() 
{
	if [ "$#" -eq 0 ]
	then
		log_msg "No filename was provided, can't set env vars, exiting without changes"
		return 
	fi
	# имя файла, которое передано в аргументе
	filename=$1

	# достаем содержимое файла
	vars=$(<$filename)

	# убираем лишние пробелы, если не убрать - работать не будет
	vars=$(echo "$vars" | sed 's/ //g' )
	
	# убираем все строки начинающиеся с символа "#", если не убрать - работать не будет
	vars=$(echo "$vars" | sed '/^#/ d' )
	
	#echo "$vars"
	
	# выполняем содержимое файла, 
	# после этой стороки к каждой переменной описанной в файле 
	# здесь можно обращаться как $variable
	eval "$vars"
	
	# экспортируем список переменных 
	# команда после export выдает в результате выполнения список вида
	# var1
	# var2 и т.д., каждая переменная на новой строке
	export $(echo "$vars"  | cut -d= -f1)

}

export config_filename

# экспортируем конфиг в переменные среды
export_env_vars "$config_filename"

# создаем временные папки
create_dirs=$(cat <<'EOF'
from service_manager_lib import create_temp_dirs

create_temp_dirs()
EOF
)
${env_python_exec} -c "$create_dirs"

log_msg "----------------- Service managing operation start -----------------"

log_msg "Exported env vars from $config_filename"

log_msg "Got these arguments: $*"

timestamp=$(date +"%Y.%m.%d %H:%M:%S")
log_msg "Timestamp: $timestamp"

# если аргументов нет - ничего не делаем и выходим
if [ "$#" -eq 0 ]
then
	log_msg "No arguments provided, exiting without any changes."
	log_msg "================= Service managing operation finish ================"
return
fi

# Формирует конфиг uwsgi из template и записывает его в файл переданный 
# в 1-м аргументе
# аргументы:
# первый - путь до файла куда записать конфиг, полный или относительно 
#	текущей папки
form_uwsgi_ini_string()
{

	if [ "$#" -eq 0 ]
	then
		log_msg "No filename was provided, can't set uwsgi config, exiting without changes"
		return 
	fi
	# имя файла, которое передано в аргументе
	filename=$1

	echo "
[uwsgi]
chdir=${uwsgi_conf_chdir}
virtualenv=${uwsgi_conf_virtualenv}
pythonpath=${uwsgi_conf_pythonpath}
module=${uwsgi_conf_module}
callable=${uwsgi_conf_callable}
processes=${uwsgi_conf_processes}
http=${uwsgi_conf_http}
master=${uwsgi_conf_master}
pidfile=${uwsgi_conf_pidfile}
vacuum=${uwsgi_conf_vacuum}
max-requests=${uwsgi_conf_max_requests}
disable-logging=${uwsgi_conf_disable_logging}
logto=${uwsgi_conf_logto}
log-maxsize=${uwsgi_conf_log_maxsize}
log-date=${uwsgi_conf_log_date}

# из-за того, как работают environment переменные, uwsgi должен 
# сам их устанавливать.
# внутренний механизм uwsgi, для каждой строки из конфига
# пишет в этот конфиг строку вида env = %строка из env_vars.ini%
for-readline = $config_filename
  env = %(_)
endfor ="  > $filename
}

# запускает процедуру регистрации в консуле
reg_in_consul()
{
	reg_proc=$(cat <<'EOF'
from service_manager_lib import register_in_consul

register_in_consul()
EOF
)
	${env_python_exec} -c "$reg_proc"
}

# запускает процедуру дерегистрации в консуле
dereg_in_consul()
{
	reg_proc=$(cat <<'EOF'
from service_manager_lib import deregister_in_consul

deregister_in_consul()
EOF
)
	${env_python_exec} -c "$reg_proc"
}

# запускает сервис
# первый параметр - регистрироваться ли в консуле или нет - 1 или 0 соответсвенно
start_service()
{
	cd ${api_directory}
	
	reg_in_consul=$1
	if [ $reg_in_consul == 1 ]
	then 
		# регистрируем сервис в консуле
		reg_in_consul
	fi

	# формируем конфиг uwsgi
	form_uwsgi_ini_string "${uwsgi_config_file}"
	# запускаем сервис через uwsgi
	nohup $uwsgi_exec --ini "${uwsgi_config_file}" >> ${nohup_out_log} 2>>${nohup_out_log} &
	
	log_msg "Service started succesfully on ${SERVER_ADDRESS}:${SERVER_PORT}"
}

# останавливает сервис
# первый параметр - дерегистрироваться ли в консуле или нет - 1 или 0 соответсвенно
stop_service()
{
	cd ${api_directory}
	
	reg_in_consul=$1
	if [ $reg_in_consul == 1 ]
	then 
		# разрегистрируем сервис из консула
		dereg_in_consul
	fi
	
	# смотрим, есть ли pid файл
	# при наличии - останавливаем запущенный uWSGI через него
	# иначе - убиваем то, что работает на порту из конфига
	if [ -e ${pid_file} ]
	then
		${uwsgi_exec} --stop ${pid_file}
	else 
		kill -9 $(${lsof_command} -t -i tcp:${SERVER_PORT})
		# нужно подождать, пока не освободится порт
		log_msg "Waiting for port ${SERVER_PORT} to get free"
		while ${lsof_command} -ti:${SERVER_PORT}
		do   
			sleep 0.3s
		done
		log_msg "WARNING: Couldn't find pid file, thing working with tcp:${SERVER_PORT} was killed"
	fi
	# удаляем временные файлы prometheus_flask_exporter'a
	rm ${prometheus_multiproc_dir}/*
	
	log_msg "Service on ${SERVER_ADDRESS}:${SERVER_PORT} stopped succesfully"
}

admiral_ackbar()
{
	admiral=$(cat <<'EOF'
import gzip
import base64
import re
aa=b'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'
def decode(b64):
    unb64ed = base64.b64decode(b64)
    ungzipped = gzip.decompress(unb64ed)
    return ungzipped.decode("utf-8")

res = re.findall('.{1,200}', decode(aa))
for each in res:
    print(each)
EOF
)

	${env_python_exec} -c "$admiral"
}

# убивает сервис
# первый параметр - дерегистрироваться ли в консуле или нет - 1 или 0 соответсвенно
hardstop_service()
{
	cd ${api_directory}
	
	reg_in_consul=$1
	if [ $reg_in_consul == 1 ]
	then 
		# разрегистрируем сервис из консула
		dereg_in_consul
	fi
	
	# убиваем то, что работает на порту из конфига
	kill -9 $(${lsof_command} -t -i tcp:${SERVER_PORT})
	
	# ждём, пока не освободится порт
	log_msg "Waiting for port ${SERVER_PORT} to get free"
	while ${lsof_command} -ti:${SERVER_PORT}
	do   
		sleep 0.3s
	done
	log_msg "Thing working with tcp:${SERVER_PORT} was killed"
	
	# удаляем временные файлы prometheus_flask_exporter'a
	rm ${prometheus_multiproc_dir}/*
	
	log_msg "Service on ${SERVER_ADDRESS}:${SERVER_PORT} was hardstopped"
}

# проверяет зарегистрированность сервиса в консуле
check_consul_reg()
{
	check_conc=$(cat <<'EOF'
from service_manager_lib import check_consul_reg

check_consul_reg()
EOF
)

	${env_python_exec} -c "$check_conc"
	
	# $? - exit code из последнего подпроцесса
	return $?
}

# проверяет текущее состояние сервиса
check_status()
{

	# hash текущего коммита в git
	current_version=$(git rev-parse HEAD)
	log_msg "Current hash in GIT: ${current_version}"

	# смотрим, зарегистрирован ли сервис в консуле
	check_consul_reg
	
	# если 0 - сервис зарегистрирован в консуле, 1 - не зарегистрирован
	reg_in_consul=$?

	# если на указанном в кофиге порту есть процесс - service_instance 
	# будет содержать pid этого процесса, иначе - будет пуста
	service_instance=$(${lsof_command} -ti:${SERVER_PORT})
	
	if [ $reg_in_consul -eq 1 ]
	then
		log_msg "${SERVICE_NAME} NOT found in consul on ${CONSUL_ADDRESS}:${CONSUL_PORT} with address ${SERVER_ADDRESS}:${SERVER_PORT}"

		if [ "$service_instance" != "" ]
		then
			log_msg "${SERVICE_NAME} IS WORKING on tcp:${SERVER_PORT}"
			log_msg "Conclusion: ${SERVICE_NAME} is running in DEVELOPMENT mode"
		else
			log_msg "${SERVICE_NAME} is NOT WORKING on tcp:${SERVER_PORT}"
			log_msg "Conclusion: ${SERVICE_NAME} is NOT running at all"
		fi
	
	elif [ $reg_in_consul -eq 0 ]
	then
		log_msg "Found ${SERVICE_NAME} in consul on ${CONSUL_ADDRESS}:${CONSUL_PORT} with address ${SERVER_ADDRESS}:${SERVER_PORT}"
		
		if [ "$service_instance" != "" ]
		then
			log_msg "${SERVICE_NAME} IS WORKING on tcp:${SERVER_PORT}"
			log_msg "Conclusion: ${SERVICE_NAME} is running in DEPLOYED mode"
		else
			log_msg "${SERVICE_NAME} is NOT WORKING on tcp:${SERVER_PORT}"
			log_msg "Conclusion: WARNING: ${SERVICE_NAME} is registered in consul, but NOT running!"
		fi
	fi
	
}

# выполнить тесты
do_tests()
{
	test_proc=$(cat <<'EOF'
from service_manager_lib import test_api
test_api()
EOF
)
	${env_python_exec} -c "$test_proc"
}

# выполнить релог
do_relog()
{
	relog_proc1=$(cat <<'EOF'
from service_manager_lib import execute_relog
execute_relog(
EOF
)
	relog_proc2=$(cat <<'EOF'
)
EOF
)

	${env_python_exec} -c "$relog_proc1 $relog_del $relog_proc2"
}

help_message()
{
	echo -e "${help_message}"
}

always_do_this_on_exit()
{
	log_msg "Something went wrong, exiting after this message"
	log_msg "================= Service managing operation finish ================"
	exit 1
}
#=================================

# аргументы
action=""
consul_reg=2
relog_del=2
trap=0
user_needs_help=0

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
	-h|--help|\?)
	user_needs_help=1
	shift # past argument
	;;
	-a|--action)
	action="$2"
	shift # past argument
	shift # past value
	;;
	-c|--consul)
	consul_reg="$2"
	shift # past argument
	shift # past value
	;;
	-t|--trap)
	trap=1
	shift # past argument
	;;
	-r|--relog)
	relog_del="$2"
	shift # past argument
	shift # past value
	;;
	*)    # unknown option
	POSITIONAL+=("$1") # save it in an array for later
	shift # past argument
	;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [ "$user_needs_help" == 1 ]
then
	log_msg "Got help flag, only showing documentation and exiting"
	help_message
	log_msg "================= Service managing operation finish ================"
	return
fi

if [ "$trap" == 1 ]
then
	log_msg "IT'S A TRAP!!!1"
	admiral_ackbar
	log_msg "================= Service managing operation finish ================"
	return
fi

if [ "${#POSITIONAL[@]}" != 0 ]; then
	echo "Unknown args found, exiting"
	log_msg "================= Service managing operation finish ================"
	return
fi

if [ $consul_reg == 2 ]
then 
	consul_reg=${CONSUL_REG}
fi

#пока не до конца разобрался, как оно работает, нужно будет доковырять когда-нибудь
#trap always_do_this_on_exit EXIT

# выполняем action и проводим регистрацию в консуле
# в соответствии с аргументами
if [ "$action" == "start" ] 
then
	start_service $consul_reg

elif [ "$action" == "stop" ] 
then
	stop_service $consul_reg

elif [ "$action" == "hardstop" ] 
then
	hardstop_service $consul_reg

elif [ "$action" == "restart" ] 
then
	stop_service $consul_reg
	
	# просто так остановить и запустить сервис заново нельзя, 
	# нужно подождать, пока не освободится порт
	log_msg "Waiting for port ${SERVER_PORT} to get free"
	while ${lsof_command} -ti:${SERVER_PORT}
	do   
		sleep 0.3s
	done
	
	start_service $consul_reg

elif [ "$action" == "status" ] 
then
	check_status
	
elif [ "$action" == "tests" ] 
then
	do_tests
	
elif [ "$action" == "relog" ] 
then
	do_relog
	
else
	log_msg "invalid action, try . ${BASH_SOURCE[0]} -h for help"
fi
	

log_msg "================= Service managing operation finish ================"
