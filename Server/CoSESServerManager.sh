#!/bin/bash
#############################################################################
####### CoSESWeather 2019 by Miroslav Lach (miroslav.lach@tum.de) ###########
#############################################################################
#		This software is part of the CoSESWeather project.    
# Starts CoSESServer to establish a connection with Controllino and send EMail-Notification onError (starts Weather Station)
# Usage: sudo bash ./CoSESServerManager.sh [arg1 = path to CoSESWeather.ini]
#										   [arg2 (optional) = only used by crontab: 0 = no notification | 1 = send notification]


# this function checks if a status file exists. This is to prevent email flood when sending mail notifications.
function check_status_file_func()
{
	# read path from .ini: 'path_status_file' from section [config]
	remove_substring3="path_status_file="
	path_statusfile=$(grep -F $remove_substring3 $mse_ini_path)
	path_statusfile=${path_statusfile/$remove_substring3/""}
	
	if [ -f $path_statusfile ]; then # status file exists
		local var="1"
		echo "$var"
	else # status file does not exist
		touch $path_statusfile # create an emtpy status file
		local var="2"
		echo "$var"
	fi
}


if [[ $# -eq 0 || $# -gt 2 ]] # check if provided arguments are valid
then
	echo "[ERROR] Please provide valid arguments! Arguments: [path to CoSESWeather.ini][only for crontab: 0=do not notify | 1=notify]"
else
	if [[ $2 -eq 0 || $2 -eq 1 ]] # provided arguments are valid
	then
		mse_ini_path=$1 # first argument that is passed to this bash script (path to .ini file)
		if [ -f $mse_ini_path ]; then # file exists
		
			# read path from .ini
			remove_substring="path_revpiserver=" # "path_revpiserver" from section: [python_paths] (CoSESServer.py)
			file_path_server=$(grep -F $remove_substring $mse_ini_path)
			file_path_server=${file_path_server/$remove_substring/""}
			
			# read path from .ini: 'path_notification' from section [config] (user_notification.txt)
			remove_substring1="path_notification="
			file_path=$(grep -F $remove_substring1 $mse_ini_path)
			file_path=${file_path/$remove_substring1/""}
			
			# read path from .ini: 'path_weewx_root' from section [weewx_paths] (opt/CoSESWeather/weewx)
			remove_substring2="path_weewx_root="
			root_weewx=$(grep -F $remove_substring2 $mse_ini_path)
			root_weewx=${root_weewx/$remove_substring2/""}
			
			# read path from .ini
			remove_substringapp="path_app=" # "path_app" from section: [python_paths] (CoSESWeatherApp.py)
			file_path_server_app=$(grep -F $remove_substringapp $mse_ini_path)
			file_path_server_app=${file_path_server_app/$remove_substringapp/""}			
			
			if [ -f $file_path_server ]; then # python file exists
				if [ -f $root_weewx"/bin/weewxd" ] && [ -f $root_weewx"/weewx.conf" ]; then # weewx files exist
					if [ -f $file_path_server_app ]; then # app file exists
						if [ $# -eq 1 ] # One input arguments passed to script = Executed by User
						then
							if [ $EUID != 0 ] # not root
							then
								echo "[ERROR] Please run script as admin."
								exit
							else # root
								echo "[Info] User is admin."
								# check if CoSESServer is running
								if [[ $(pgrep -a python | grep 'CoSESServer.py') ]]; then
									echo "[Info] CoSESServer is already running."
								else
									echo "[Info] Starting CoSESServer ..."
									python $file_path_server & # start server and send process to background
									echo "[Info] Done."
								fi
								# check if weewx is running
								if [[ $(pgrep -a weewxd | grep 'weewxd') ]]; then
									echo "[Info] WeeWx is already running."
								else
									echo "[Info] Starting WeeWx ..."
									$root_weewx"/bin/weewxd" $root_weewx"/weewx.conf" & # start weewx and send process to background
									echo "[Info] Done."
								fi	
								# check if CoSESWeatherApp is running
								if [[ $(pgrep -a python | grep 'CoSESWeatherApp.py') ]]; then
									echo "[Info] CoSESWeatherApp is already running."
									exit
								else
									echo "[Info] Starting CoSESWeatherApp ..."
									su -c "python $file_path_server_app &" - coses # start app as user 'coses' and send process to background
									echo "[Info] Done."
									exit
								fi
							fi
						else # Multiple input arguments passed to script = Executed by Crontab
							if [ $EUID != 0 ] # not root
							then	
								if [ $2 -eq 1 ]; then # If arg2=1 (notify via email)
									return_code=$(check_status_file_func)
									if [[ $return_code -eq 2 ]]; then # status file does not exist, send mail			
										while read line_mail_address; do # one email per mail address
											if [ "$line_mail_address" ]; then # skip blank lines in file
												# send email notification to system administrators
												mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Error] CoSESServerManager.sh Script needs admin permissions to be executed! Please check if the CoSESServer is running correctly.'
											fi
										done < "$file_path"	
										exit				
									fi	
								fi	
							else # root
								# check if CoSESServer is running
								if [[ $(pgrep -a python | grep 'CoSESServer.py') ]]; then # Script is running, do nothing
									:
								else # Script is not running	
									if [ $2 -eq 1 ]; then # If arg2=1 (notify via email)
										return_code=$(check_status_file_func)
										if [[ $return_code -eq 2 ]]; then # status file does not exist, send mail			
											while read line_mail_address; do # one email per mail address
												if [ "$line_mail_address" ]; then # skip blank lines in file
													mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Info] CoSESServer crashed and had to be restarted by Crontab! Please check if system is running properly.'
												fi
											done < "$file_path"			
										fi	
									fi	
									python $file_path_server & # start server and send process to background	
								fi
								# check if weewx is running
								if [[ $(pgrep -a weewxd | grep 'weewxd') ]]; then # WeeWx is running, do nothing
									:
								else # WeeWx is not running
									if [ $2 -eq 1 ]; then # If arg2=1 (notify via email)
										return_code=$(check_status_file_func)
										if [[ $return_code -eq 2 ]]; then # status file does not exist, send mail			
											while read line_mail_address; do # one email per mail address
												if [ "$line_mail_address" ]; then # skip blank lines in file
													mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Info] WeeWx crashed and had to be restarted by Crontab! Please check if system is running properly.'
												fi
											done < "$file_path"				
										fi	
									fi	
									$root_weewx"/bin/weewxd" $root_weewx"/weewx.conf" & # start weewx and send process to background							
								fi
								# check if CoSESWeatherApp is running
								if [[ $(pgrep -a python | grep 'CoSESWeatherApp.py') ]]; then # App is running, do nothing
									:
								else # App is not running (start GUI)
									su -c "env DISPLAY=:0.0 python $file_path_server_app &" - coses # start app as user 'coses' and send process to background
								fi
							fi
						fi
					else # app file does not exist
						if [ ! $# -eq 1 ]; then # If not executed by user 
							if [ $2 -eq 1 ]; then # If arg2=1 (notify via email)
								return_code=$(check_status_file_func)
								if [[ $return_code -eq 2 ]]; then # status file does not exist, send mail			
									while read line_mail_address; do # one email per mail address
										if [ "$line_mail_address" ]; then # skip blank lines in file
											mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Info] CoSESServerManager.sh Script can not find CoSESWeatherApp.py! Please check the system installation.'
										fi
									done < "$file_path"	
									exit				
								fi	
							fi	
						else # If executed by user, just echo error message
							echo "[ERROR] Can not find CoSESWeatherApp.py! Please check the system installation."
							exit
						fi
					fi	
				else # weewx files do not exist		
					if [ ! $# -eq 1 ]; then # If not executed by user 
						if [ $2 -eq 1 ]; then # If arg2=1 (notify via email)
							return_code=$(check_status_file_func)
							if [[ $return_code -eq 2 ]]; then # status file does not exist, send mail			
								while read line_mail_address; do # one email per mail address
									if [ "$line_mail_address" ]; then # skip blank lines in file
										mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Info] CoSESServerManager.sh Script can not find WeeWx files! Please check the system installation.'
									fi
								done < "$file_path"	
								exit				
							fi	
						fi		
					else # If executed by user, just echo error message
						echo "[ERROR] Can not find WeeWx files! Please check the system installation."
						exit
					fi					
				fi
			else # python file does not exist
				if [ ! $# -eq 1 ]; then # If not executed by user 
					if [ $2 -eq 1 ]; then # If arg2=1 (notify via email)
						return_code=$(check_status_file_func)
						if [[ $return_code -eq 2 ]]; then # status file does not exist, send mail			
							while read line_mail_address; do # one email per mail address
								if [ "$line_mail_address" ]; then # skip blank lines in file
									mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Info] CoSESServerManager.sh Script can not find CoSESServer.py! Please check the system installation.'
								fi
							done < "$file_path"	
							exit				
						fi	
					fi	
				else # If executed by user, just echo error message
					echo "[ERROR] Can not find CoSESServer.py! Please check the system installation."
					exit
				fi				
			fi
		else # ini. file does not exist
			if [ ! $# -eq 1 ]; then # If not executed by user 
				if [ $2 -eq 1 ]; then # If arg2=1 (notify via email)
					if [ ! -f "/opt/CoSESWeather/RevPiStatus.txt" ]; then # if status file does not exist, send mail
						touch "/opt/CoSESWeather/RevPiStatus.txt" # create an emtpy status file
						while read line_mail_address; do # one email per mail address
							if [ "$line_mail_address" ]; then # skip blank lines in file
								mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Error] CoSESServerManager.sh Script can not find CoSESWeather.ini! Please check the system installation.'
							fi
						done < "/opt/CoSESWeather/user_notification.txt"	
						exit
					fi	
				fi	
			else # If executed by user, just echo error message
				echo "[ERROR] Can not find CoSESWeather.ini! Please check the system installation."
				exit
			fi
		fi
	else
		echo "[ERROR] Please provide valid arguments! Arguments: [path to CoSESWeather.ini][only crontab: 0=do not notify | 1=notify]"
	fi	
fi

