#!/bin/bash
#############################################################################
####### CoSESWeather 2019 by Miroslav Lach (miroslav.lach@tum.de) ###########
#############################################################################
#		This software is part of the CoSESWeather project.    				
# This bash script is used in order to create backups of the MySSQL Databases
# Usage: sudo bash ./MySQLBackUp.sh [arg1 = path to CoSESWeather.ini]
#									[arg2 = 0 : do not copy to server | 1 : copy to server]
#									[arg3 (optional) = only used by crontab: arbitrary int]
### MySQL Server Login Info ###

MySQL_USER="enter_username"
MySQL_PASS="enter_password"
MySQL_HOST="localhost"
# Specify the Databases that should be included in the backup creation
declare -a MySQL_DATABASES=("CoSESWeather_DB" "WeeWx_DB")

###############################


function notify_onError()
{
	ini_path=$1
	user_mode=$2
	message=$3
	
	if [ $user_mode -eq 0 ] # Executed by User
	then			
		echo "[ERROR] $message"
	else # Executed by crontab
	
		# read path from .ini: 'path_notification' from section [config] (user_notification.txt)
		remove_substring="path_notification="
		file_path=$(grep -F $remove_substring $ini_path)
		file_path=${file_path/$remove_substring/""}			
		
		# send email
		while read line_mail_address; do # one email per mail address
			if [ "$line_mail_address" ]; then # skip blank lines in file
				mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< "[Cronjob Info] Error on BackUp! ""$message"
			fi
		done < "$file_path"	
	fi	
}


if [[ $# -lt 2 || $# -gt 3 ]] # check if provided arguments are valid
then
	echo "[ERROR] Please provide valid arguments! Arguments: [path to CoSESWeather.ini][0:do not copy | 1:copy][only for crontab: arbitrary int]"
else
	if [[ $2 -eq 0 || $2 -eq 1 ]] # provided arguments are valid
	then
		if [ $EUID -eq 0 ] # user is admin
		then
		
			if [ $# -eq 2 ] # Two input arguments passed to script = Executed by User
			then	
				mode=0
			else # Executed by crontab
				mode=1
			fi
			
			mse_ini_path=$1 # first argument that is passed to this bash script (path to .ini file)
					
			if [ -f $mse_ini_path ]; then # file exists
			
				# read path from .ini
				remove_substring1="path_backup_local=" # "path_backup_local" from section: [backup]
				file_path_backup1=$(grep -F $remove_substring1 $mse_ini_path)
				file_path_backup1=${file_path_backup1/$remove_substring1/""}
				
				if [ -d "$file_path_backup1" ]; then # specified local backup location exists

					# read path from .ini
					remove_substring2="path_backup_remote=" # "path_backup_remote" from section: [backup]
					file_path_backup2=$(grep -F $remove_substring2 $mse_ini_path)
					file_path_backup2=${file_path_backup2/$remove_substring2/""}			
				
					# read path from .ini
					remove_substring3="path_backup_log=" # "path_backup_log" from section: [backup]
					file_path_backup_log=$(grep -F $remove_substring3 $mse_ini_path)
					file_path_backup_log=${file_path_backup_log/$remove_substring3/""}						
				
					if [ -d "$file_path_backup2" ]; then # specified remote backup location exists

						DATE_NOW=$(date +%Y-%m-%d) # get current date
						TIME_DATE_NOW=$(date +%Y-%m-%d_%H-%M-%S) # get current time and date

						msg="-------------------- BackUp on "$DATE_NOW" ----------------------------------------"
						echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 
						msg="[Info] Starting backup creation ..."
						echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 

						# if backup folder at local backup destination does not exist yet, create one
						[[ -d "$file_path_backup1"/$DATE_NOW ]] || mkdir "$file_path_backup1"/$DATE_NOW

						# create backup of specified databases
						for db in "${MySQL_DATABASES[@]}"
						do 
							msg="[Info] Creating backup of database $db (destination: $file_path_backup1) ..."
							echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 		
							
							# backup of database
							return_code=$((mysqldump -h ${MySQL_HOST} -u ${MySQL_USER} -p${MySQL_PASS} $db | gzip > \
							$file_path_backup1/$DATE_NOW/db__"$db"__"$TIME_DATE_NOW".sql.gz) 2>&1)

							if [[ "$return_code" = *"error"* ]]
							then # backup creation failed (if mysql command returns 'error' in message)
								msg="[Error] Database backup failed! Error: $return_code"
								echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 	
								notify_onError "$mse_ini_path" "$mode" "Error occurred while database backup creation! Please check the logs for more info."	
								exit								
							else # backup creation successful
								msg="[Info] Finished backup of database $db."
								echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log"	
							fi 											 	 
						done

						msg="[Info] Database backup successful."
						echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 

						if [ $2 -eq 1 ] # if backup should be copied to remote location
						then
							msg="[Info] Copying backup-files to remote backup location (destination: $file_path_backup2) ..."
							echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 	

							# if backup folder at remote backup destination does not exist yet, create one
							[[ -d "$file_path_backup2"/$DATE_NOW ]] || mkdir "$file_path_backup2"/$DATE_NOW
							# copy local backup files to the remote backup location
							cp "/$file_path_backup1/"$DATE_NOW/* "/$file_path_backup2/"$DATE_NOW 

							# check if copying backup files successful
							if [ $? -eq 0 ]; then
								msg="[Info] Moving database backup-files to remote backup location successful."
								echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 						
							else
								msg="[Error] Moving database backup-files to remote backup location failed! Error: "$$
								echo [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log" 	
								notify_onError "$mse_ini_path" "$mode" "Error occurred while moving database backup-files to remote backup location! Please check the logs for more info."
								exit
							fi	
						fi
						msg="[Info] BackUp-Cronjob exited successfully.\nDone."
						echo -e [$TIME_DATE_NOW]"$msg" >> "$file_path_backup_log"	
					else
						notify_onError "$mse_ini_path" "$mode" "Can not find specified remote backup location! Please check the specified path."
					fi			
				else
					notify_onError "$mse_ini_path" "$mode" "Can not find specified local backup location! Please check the specified path."
				fi
			else
				while read line_mail_address; do # one email per mail address
					if [ "$line_mail_address" ]; then # skip blank lines in file
						mail -s "[CoSESWeather] Cronjob Notification" $line_mail_address <<< '[Cronjob Error] MySQLBackUp.sh Script can not find CoSESWeather.ini! Please check the system installation.'
					fi
				done < "/opt/CoSESWeather/user_notification.txt"				
			fi
		else	
			echo "[ERROR] User is not admin!"
		fi	
	else
		echo "[ERROR] Please provide valid arguments! Arguments: [path to CoSESWeather.ini][0:do not copy | 1:copy][only for crontab: arbitrary int]"
	fi
fi	
