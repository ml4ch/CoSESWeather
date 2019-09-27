<?php
	/**
	* @author Miroslav Lach <miroslav.lach@tum.de>
	* 
	* *** Description ***
	*
	* This software is part of the CoSESWeather project.
	* This PHP-Script presents the API between the python code and the MySQL-Databases and performs various tasks:
	*
	* p_mode = 1  -> Saving sensor values provided by CoSESServer.py into the primary MySQL Database
	* p_mode = 2  -> Used by the WeeWx Framework in the driver in order to record and archive the sensor data into the WeeWx secondary SQL-Database
	* p_mode = 3  -> Get emails of registered users with admin status
	* p_mode = 4  -> Get latest sensor reading dataset from primary database to display in GUI 'current conditions'
	* p_mode = 5  -> Login user in CoSESWeather APP
	* p_mode = 6  -> Change user password
	* p_mode = 7  -> Add new user account
	* p_mode = 8  -> Delete user account
	* p_mode = 9  -> Change account password of a user
	* p_mode = 10 -> Send admin command: reset microcontroller
	* p_mode = 11 -> Send admin command: restart system	
	* p_mode = 12 -> Get admin log	
	* p_mode = 13 -> Get registered users
	* p_mode = 14 -> Check for submitted admin commands
	* p_mode = 15 -> Data Export
	*
	* *** Expected arguments **************************************************** 
	*
	* * for ['p_mode' = 1] (saving sensor datasets):
	* [p_mode]		-> 1
	* [p_temp] 		-> Temperature reported by the PT100.
	* [p_wind] 		-> Windspeed reported by the anemometer.
	* [p_spn1_radTot]  -> Total Sun Irradiation reported by the SPN1 pyranometer.
	* [p_spn1_radDiff]  -> Diffuse Sun Irradiation reported by the SPN1 pyranometer.
	* [p_spn1_sun]  -> Sunshine presence reported by the SPN1 pyranometer.
	* [p_rad_cmp1]  -> Sun Irradiation reported by the first CMP3 pyranometer.
	* [p_rad_cmp2]  -> Sun Irradiation reported by the second CMP3 pyranometer.
	* [p_rad_cmp3]  -> Sun Irradiation reported by the third CMP3 pyranometer.			
	* ***************************************************************************		
	* * for ['p_mode' = 2] (fetch datasets):
	* [p_mode]		-> 2	
	* ***************************************************************************		
	* * for ['p_mode' = 3] (Get emails of users with admin status):
	* [p_mode]		-> 3	
	* ***************************************************************************	
	* * for ['p_mode' = 4] (current conditions):
	* [p_mode]		-> 4			
	* ***************************************************************************		
	* * for ['p_mode' = 5] (login user account):
	* [p_mode]		-> 5
	* [p_user] 		-> The username
	* [p_pass] 		-> The password for the entered username	
	* ***************************************************************************		
	* * for ['p_mode' = 6] (change user password):
	* [p_mode]		-> 6	
	* [p_user] 		-> The username
	* [p_pass] 		-> The password for the entered username
	* [p_pass_new]	-> The new password for the entered username	
	* ***************************************************************************		
	* * for ['p_mode' = 7] (add new user account):
	* [p_mode]		-> 7
	* [p_user] 		-> Admin username (for authetication)
	* [p_pass] 		-> Admin password (for authetication)
	* [acc_user]	-> Full username of new account
	* [acc_pass]	-> Password of new account
	* [acc_email]	-> Email of new account
	* [acc_admin]	-> Status of new account (user/admin)	
	* ***************************************************************************		
	* * for ['p_mode' = 8] (delete user account):
	* [p_mode]		-> 8
	* [p_user] 		-> Admin username (for authetication)
	* [p_pass] 		-> Admin password (for authetication)
	* [acc_email]	-> Email account to be deleted
	* [a_reason]	-> Reason for action	
	* ***************************************************************************
	* * for ['p_mode' = 9] (change account password of a user):
	* [p_mode]		-> 9
	* [p_user] 		-> Admin username (for authetication)
	* [p_pass] 		-> Admin password (for authetication)
	* [acc_pass]	-> New account password
	* [acc_email]	-> Email of account
	* [a_reason]	-> Reason for action	
	* ***************************************************************************	
	* * for ['p_mode' = 10] (reset microcontroller):
	* [p_mode]		-> 10
	* [p_user] 		-> Admin username (for authetication)
	* [p_pass] 		-> Admin password (for authetication)
	* [a_reason]	-> Reason for action	
	* ***************************************************************************	
	* * for ['p_mode' = 11] (restart system):
	* [p_mode]		-> 11
	* [p_user] 		-> Admin username (for authetication)
	* [p_pass] 		-> Admin password (for authetication)
	* [a_reason]	-> Reason for action	
	* ***************************************************************************	
	* * for ['p_mode' = 12] (get admin log):
	* [p_mode]		-> 12
	* [p_user] 		-> Admin username (for authetication)
	* [p_pass] 		-> Admin password (for authetication)	
	* [a_prios] 	-> Priority of log entry		
	* ***************************************************************************				
	* * for ['p_mode' = 13] (Get registered users):
	* [p_mode]		-> 13
	* [p_user] 		-> Admin username (for authetication)
	* [p_pass] 		-> Admin password (for authetication)			
	* ***************************************************************************			
	* * for ['p_mode' = 14] (Check for submitted admin commands):
	* [p_mode]		-> 14	
	* ***************************************************************************		
	* * for ['p_mode' = 15] (Data exports):
		* * for ['d_export_mode' = 0] (export from primary database):
	* [p_mode]		  -> 15	
	* [p_user] 		  -> Username (for authetication)
	* [p_pass] 		  -> Password (for authetication)	
	* [d_export_mode] -> 0 (for export from primary database)
	* [d_sensors] 	  -> Sensor string for query (choosing sensors to be included in the export)	
	* [d_start] 	  -> Date/Time start
	* [d_stop] 		  -> Date/Time stop	
	* [d_step] 		  -> step/interval of measurements in seconds
		* * for ['d_export_mode' = 1] (export from secondary database):	
	* [p_mode]		  -> 15	
	* [p_user] 		  -> Username (for authetication)
	* [p_pass] 		  -> Password (for authetication)	
	* [d_export_mode] -> 1 (for export from secondary database)		
	* [d_sensors] 	  -> Sensor string for query (choosing sensors to be included in the export)	
	* [d_start] 	  -> Date/Time start
	* [d_stop] 		  -> Date/Time stop	
	* [d_step] 		  -> step/interval of measurements in seconds			
	* [d_hilo] 		  -> include hi/lo statistics in export if selected	
	* ***************************************************************************				
	*/
	if(isset($_POST['p_mode']))
	{
		$mode=$_POST['p_mode'];
		
		// get login data	
		include("db_config.php");
		
		// connect to database
		$connection1=mysqli_connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DB1) 
		or die("[ERROR_01_1] Could not connect to primary database!");

		switch($mode) // switch query jobs depending on request
		{			
			case 1: // Saving new sensor data received from Controllino over TCP socket into primary database
			{	
				// get posted values from variables
				$temp = isset($_POST['p_temp']) ? mysqli_real_escape_string($connection1, $_POST['p_temp']) : 'NULL';
				$wind = isset($_POST['p_wind']) ? mysqli_real_escape_string($connection1, $_POST['p_wind']) : 'NULL';
				$spn1_radTot = isset($_POST['p_spn1_radTot']) ? mysqli_real_escape_string($connection1, $_POST['p_spn1_radTot']) : 'NULL';
				$spn1_radDiff = isset($_POST['p_spn1_radDiff']) ? mysqli_real_escape_string($connection1, $_POST['p_spn1_radDiff']) : 'NULL';
				$spn1_sun = isset($_POST['p_spn1_sun']) ? mysqli_real_escape_string($connection1, $_POST['p_spn1_sun']) : 'NULL';
				$rad_cmp1 = isset($_POST['p_rad_cmp1']) ? mysqli_real_escape_string($connection1, $_POST['p_rad_cmp1']) : 'NULL';
				$rad_cmp2 = isset($_POST['p_rad_cmp2']) ? mysqli_real_escape_string($connection1, $_POST['p_rad_cmp2']) : 'NULL';
				$rad_cmp3 = isset($_POST['p_rad_cmp3']) ? mysqli_real_escape_string($connection1, $_POST['p_rad_cmp3']) : 'NULL';
				// build query
				mysqli_query($connection1, "INSERT INTO sensor_datasets 
				(temp, wind, spn1_radTot, spn1_radDiff, spn1_sun, rad_cmp1, rad_cmp2, rad_cmp3, t_unix, archived) 
				VALUES (".$temp.", ".$wind.", ".$spn1_radTot.", ".$spn1_radDiff.", ".$spn1_sun.", ".$rad_cmp1.", ".$rad_cmp2.", ".$rad_cmp3.", UNIX_TIMESTAMP(), '0')") 
				or die("[ERROR_02] Could not insert new dataset into the database!");
				echo "__SUCCESS;";
				break;
			}	
			case 2: // Fetching sensor data that has not yet been recorded and achived by WeeWx (used by WeeWx Driver)
			{		
				$sensor_data_array = array();
				// Select all datasets in primary database that have not been fetched by WeeWx yet
				$result_query = mysqli_query($connection1, "SELECT temp, wind, spn1_radTot, spn1_radDiff, spn1_sun, rad_cmp1, rad_cmp2, rad_cmp3, t_unix
				 FROM sensor_datasets WHERE archived='0'") or die("[ERROR_03] Could not fetch datasets from the database!");	 
				// If there are datasets that have not been fetched by WeeWx yet, mark them as fetched (set archived=1)	 
				$new_dataset_count = mysqli_num_rows($result_query); 
				if($new_dataset_count != 0)
				{ 
					mysqli_query($connection1, "UPDATE sensor_datasets SET archived='1' WHERE archived='0'") 
					or die("[ERROR_04] Could not modify archive status of datasets in the database!");								
					while($row = mysqli_fetch_assoc($result_query))
					{
						$sensor_data_array[] = array(
													 'temp' => $row['temp'],
													 'wind' => $row['wind'],
													 'spn1_radTot' => $row['spn1_radTot'],
													 'spn1_radDiff' => $row['spn1_radDiff'],
													 'spn1_sun' => $row['spn1_sun'],
													 'rad_cmp1' => $row['rad_cmp1'],
													 'rad_cmp2' => $row['rad_cmp2'],
													 'rad_cmp3' => $row['rad_cmp3'],
													 't_unix' => $row['t_unix']
													 );		
					}
					array_unshift($sensor_data_array, '__SUCCESS;'); // operation successful
					echo json_encode($sensor_data_array); // return data in json format						
				}
				else echo json_encode('__NO_ROWS_RETURNED;');
				mysqli_free_result($result_query);
				break;			
			}	
			case 3: // Get emails of registered users with admin status (in order to send notifications)
			{		
				$email_array = array();
				$result_query = mysqli_query($connection1, "SELECT email FROM users WHERE admin='1'") 
				or die("[ERROR_06] Failed to fetch emails from user table!");	
				while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
				{
					$email_array[] = $row['email'];   
				}	
				array_unshift($email_array, '__SUCCESS;');
				echo json_encode($email_array);	
				mysqli_free_result($result_query);	
				break;
			}		
			case 4: // Get latest sensor reading dataset from primary database to display in GUI 'current conditions'
			{		
				$sensor_dataset = array();
				$result_query = mysqli_query($connection1, "SELECT * FROM sensor_datasets ORDER BY id DESC LIMIT 1") 
				or die("[ERROR_07] Failed to fetch latest sensor dataset!");	
				$result_count = mysqli_num_rows($result_query); 
				if($result_count != 0)
				{ 				
					$row = mysqli_fetch_array($result_query, MYSQLI_ASSOC);
					$sensor_dataset[] = array(
											'temp' => $row['temp'],
											'wind' => $row['wind'],
											'spn1_radTot' => $row['spn1_radTot'],
											'spn1_radDiff' => $row['spn1_radDiff'],
											'spn1_sun' => $row['spn1_sun'],
											'rad_cmp1' => $row['rad_cmp1'],
											'rad_cmp2' => $row['rad_cmp2'],
											'rad_cmp3' => $row['rad_cmp3'],
											't_unix' => $row['t_unix']
											);			
					array_unshift($sensor_dataset, '__SUCCESS;'); // operation successful
					echo json_encode($sensor_dataset); // return data in json format	
				}
				else echo json_encode('__SUCCESS;__NO_ROWS_RETURNED;');						
				mysqli_free_result($result_query);	
				break;
			}	
			case 5: // Login user in CoSESWeather APP
			{	
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);		
		
				$result_query = mysqli_query($connection1, "SELECT user, pass, salt, admin, email, lastLogin FROM users 
				WHERE email='$user' Limit 1") or die("[ERROR_08] Failed to query user table in database!");
				if(!mysqli_num_rows($result_query)) // No account with specified username found in database
				{
					// log failed login attempts with priority '1' -> (Suspicious activity/Important notification)
					mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
					VALUES ('$user', 'Failed login attempt', 'Incorrect username', '1')");						
					echo json_encode('__SUCCESS;[ERROR_AUTH_1] Username or password incorrect!');	
				}
				else // username found in database
				{		
					$user_data = array();
					$row = mysqli_fetch_array($result_query, MYSQLI_ASSOC);
					$pass_db = $row['pass'];
					$salt_db = $row['salt'];
					$user_data[] = array(
										'user' => $row['user'], 
									    'admin' => $row['admin'],
									    'email' => $row['email'],
									    'lastLogin' => $row['lastLogin']
									    );					   				
					if(hash_equals($pass_db, sha1($pass.$salt_db))) // password is correct - login user
					{
						// update lastLogin timestamp of user
						mysqli_query($connection1, "UPDATE users SET lastLogin=CURRENT_TIMESTAMP() WHERE email='$user'") 
						or die("[ERROR_12] Could not modify user data in database!");	
						// log successful user logins with priority '0' -> (Info)
						mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
						VALUES ('$user', 'Successful login', '--', '0')");								
						// return user data as json		
						array_unshift($user_data, '__SUCCESS;'); // operation successful	
						echo json_encode($user_data);
					}
					else // password does not match - incorrect data entered by user! (hashes not equal!)
					{
						// log failed login attempts with priority '1' -> (Suspicious activity/Important notification)
						mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
						VALUES ('$user', 'Failed login attempt', 'Incorrect password', '1')");					
						echo json_encode('__SUCCESS;[ERROR_AUTH_2] Username or password incorrect!');	
					}
				}
				mysqli_free_result($result_query);
				break;
			}
			case 6: // Change user password
			{	
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
				$pass_new=mysqli_real_escape_string($connection1, $_POST['p_pass_new']);
							
				$result_query = mysqli_query($connection1, "SELECT salt FROM users WHERE email='$user' Limit 1") 
				or die("[ERROR_09] Failed to query user table in database!");
				if(!mysqli_num_rows($result_query)) // No account with specified username found in database
				{
					echo "[ERROR_AUTH_1] User not authenticated!";
				}
				else // username found in database
				{				
					$row = mysqli_fetch_array($result_query, MYSQLI_ASSOC);
					$salt_old = $row['salt']; // get old password salt from database
					$pass_old = sha1($pass.$salt_old);
					$result_query = mysqli_query($connection1, "SELECT id FROM users WHERE email='$user' AND pass='$pass_old' Limit 1") 
					or die("[ERROR_10] Failed to query user table in database!");
					if(!mysqli_num_rows($result_query)) // No account with specified username and password match found in database
					{
						echo "[ERROR_AUTH_2] User not authenticated!";
					}
					else // request valid - alter user data	in database
					{				
						$randomSalt = random_str(16); // create random string that will be used as a password salt (16 chars)
						$hash_pass = sha1($pass_new.$randomSalt); // hash salted password		
						// update user data			
						mysqli_query($connection1, "UPDATE users SET pass='$hash_pass', salt='$randomSalt' WHERE email='$user'") 
						or die("[ERROR_11] Could not modify user data in database!");	
						// log password changes with priority '0' -> (Info)
						mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
						VALUES ('$user', 'Password change', '--', '0')");								
						echo "__SUCCESS;";				
					}							
				}
				mysqli_free_result($result_query);
				break;
			}		
			case 7: // Administration Tab: Create new user account in CoSESWeather-APP
			{			
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
														
				if(is_user_request_valid($connection1, $user, $pass, true)) // authenticated, trusted user
				{				
					$new_user=mysqli_real_escape_string($connection1, $_POST['acc_user']);
					$new_pass=mysqli_real_escape_string($connection1, $_POST['acc_pass']);	
					$new_email=mysqli_real_escape_string($connection1, $_POST['acc_email']);
					$acc_status=mysqli_real_escape_string($connection1, $_POST['acc_admin']);
					
					$result_query = mysqli_query($connection1, "SELECT id FROM users WHERE email='$new_email' Limit 1") 
					or die("[ERROR_12] Failed to query user table in database!");
					echo "__SUCCESS;";	
					if(!mysqli_num_rows($result_query)) // ok - email does not exist yet
					{
						$randomSalt = random_str(16); // create random string that will be used as a password salt (16 chars)
						$hash_pass = sha1($new_pass.$randomSalt); // hash salted password		
						// create new user account in database						
						mysqli_query($connection1, "INSERT INTO users (user, pass, salt, admin, email) 
						VALUES ('$new_user', '$hash_pass', '$randomSalt', '$acc_status', '$new_email')") 
						or die("[ERROR_13] Could not modify user data in database!");					
						
						// log database activity with priority '0' -> (Info)
						mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
						VALUES ('$user', 'Added new user account: $new_email', '--', '0')");														
					}
					else // error - email column in database is unique
					{						
						echo "[ERROR_DUBLICATE] Email must be unique!";
					}								
				}	
				else echo "[ADMIN_ERROR_AUTH] User not authenticated!";
				mysqli_free_result($result_query);			
				break;
			}			
			case 8: // Administration Tab: Delete user account
			{			
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
														
				if(is_user_request_valid($connection1, $user, $pass, true)) // authenticated, trusted user
				{				
					$user_mail=mysqli_real_escape_string($connection1, $_POST['acc_email']);
					$reason=mysqli_real_escape_string($connection1, $_POST['a_reason']);	
					
					$result_query = mysqli_query($connection1, "SELECT id FROM users WHERE email='$user_mail' Limit 1") 
					or die("[ERROR_14] Failed to query user table in database!");
					echo "__SUCCESS;";	
					if(!mysqli_num_rows($result_query)) // error - user does not exist
					{	
						echo "[ERROR_ACC_NOT_FOUND] User not found in database!";						
					}
					else // ok - account with entered email found in database
					{						
						// delete user account from database						
						mysqli_query($connection1, "DELETE FROM users WHERE email='$user_mail'") 
						or die("[ERROR_15] Could not modify user data in database!");					
						
						// log database activity with priority '0' -> (Info)
						mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
						VALUES ('$user', 'Deleted user account: $user_mail', '$reason', '0')");							
					}								
				}	
				else echo "[ADMIN_ERROR_AUTH] User not authenticated!";
				mysqli_free_result($result_query);			
				break;
			}				
			case 9: // Administration Tab: Change account password
			{			
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
														
				if(is_user_request_valid($connection1, $user, $pass, true)) // authenticated, trusted user
				{				
					$user_mail=mysqli_real_escape_string($connection1, $_POST['acc_email']);	
					$new_acc_pass=mysqli_real_escape_string($connection1, $_POST['acc_pass']);	
					$reason=mysqli_real_escape_string($connection1, $_POST['a_reason']);
					
					$result_query = mysqli_query($connection1, "SELECT id FROM users WHERE email='$user_mail' Limit 1") 
					or die("[ERROR_16] Failed to query user table in database!");
					echo "__SUCCESS;";	
					if(!mysqli_num_rows($result_query)) // error - user does not exist
					{	
						echo "[ERROR_ACC_NOT_FOUND] User not found in database!";						
					}
					else // ok - account with entered email found in database
					{																	
						$randomSalt = random_str(16); // create random string that will be used as a password salt (16 chars)
						$hash_pass = sha1($new_acc_pass.$randomSalt); // hash salted password		
						// update user data			
						mysqli_query($connection1, "UPDATE users SET pass='$hash_pass', salt='$randomSalt' WHERE email='$user_mail'") 
						or die("[ERROR_17] Could not modify user data in database!");									
						
						// log database activity with priority '0' -> (Info)
						mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
						VALUES ('$user', 'Account password changed for: $user_mail', '$reason', '0')");							
					}								
				}	
				else echo "[ADMIN_ERROR_AUTH] User not authenticated!";
				mysqli_free_result($result_query);			
				break;
			}								
			case 10: // Administration Tab: Reset microcontroller
			{			
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
														
				if(is_user_request_valid($connection1, $user, $pass, true)) // authenticated, trusted user
				{						
					$reason=mysqli_real_escape_string($connection1, $_POST['a_reason']);
				
					// log system activity with priority '2' -> (System Event: Will be set from '99' to '2' when command processed)
					mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
					VALUES ('$user', 'Microcontroller reset', '$reason', '99')") or die("[ERROR_18] Failed to save system event!");	
					echo "__SUCCESS;";													
				}	
				else echo "[ADMIN_ERROR_AUTH] User not authenticated!";	
				break;
			}					
			case 11: // Administration Tab: Restart System
			{			
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
														
				if(is_user_request_valid($connection1, $user, $pass, true)) // authenticated, trusted user
				{						
					$reason=mysqli_real_escape_string($connection1, $_POST['a_reason']);
							
					// log system activity with priority '2' -> (System Event: Will be set from '99' to '2' when command processed)
					mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
					VALUES ('$user', 'System restart', '$reason', '99')") or die("[ERROR_19] Failed to save system event!");	
					echo "__SUCCESS;";																
				}	
				else echo "[ADMIN_ERROR_AUTH] User not authenticated!";		
				break;
			}			
			case 12: // Get admin log
			{			
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
													
				if(is_user_request_valid($connection1, $user, $pass, true)) // authenticated, trusted user
				{	
					$log_data = array();							
					$prios=mysqli_real_escape_string($connection1, $_POST['a_prios']);	
				
					$result_query = mysqli_query($connection1, "SELECT * FROM admin_log WHERE priority IN ($prios) ORDER BY id DESC") 
					or die("[ERROR_20] Failed to query admin_log table in database!");			
					while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
					{
						if($row["priority"]==0)$priority_string = "Info";
						else if ($row["priority"]==1)$priority_string = "Suspicious Action";
						else $priority_string = "System Event";
						$log_data[] = array(
											'user' => $row["user"],
											'action' => $row["action"],
											'reason' => $row["reason"],
											'priority' => $priority_string,
											'time' => $row["time"]
										   );							 		   
					}	
					// return user data as json		
					array_unshift($log_data, '__SUCCESS;'); // operation successful	
					echo json_encode($log_data);						
				}	
				else echo json_encode('[ADMIN_ERROR_AUTH] User not authenticated!');			
				mysqli_free_result($result_query);	
				break;								
			}			
			case 13: // Get registered users
			{			
				$user_data = array();
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
													
				if(is_user_request_valid($connection1, $user, $pass, true)) // authenticated, trusted user
				{											
					$result_query = mysqli_query($connection1, "SELECT user, admin, email, lastLogin FROM users ORDER BY admin DESC") 
					or die("[ERROR_21] Failed to query users table in database!");
					while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
					{					
						$user_data[] = array(
											'user' => $row["user"],
											'admin' => $row["admin"],
											'email' => $row["email"],
											'lastLogin' => $row["lastLogin"]
										   );							
					}	
					// return user data as json		
					array_unshift($user_data, '__SUCCESS;'); // operation successful	
					echo json_encode($user_data);							
				}	
				else echo json_encode('[ADMIN_ERROR_AUTH] User not authenticated!');		
				mysqli_free_result($result_query);	
				break;								
			}		
			case 14: // Check for submitted admin commands
			{											
				$result_query = mysqli_query($connection1, "SELECT action FROM admin_log WHERE priority='99' LIMIT 1") 
				or die("[ERROR_22] Failed to query users table in database!");
				if(!mysqli_num_rows($result_query)) // no admin commands waiting for execution
				{
					echo json_encode('_NO_COMMANDS;');	
				}
				else // admin commands waiting for execution
				{			
					$row = mysqli_fetch_array($result_query, MYSQLI_ASSOC);
					mysqli_query($connection1, "UPDATE admin_log SET priority='2' WHERE priority='99'");
					$return_array[] = array('cmd' => $row['action']);			
					array_unshift($return_array, '__SUCCESS;');
					echo json_encode($return_array);	
				}
				mysqli_free_result($result_query);	
				break;								
			}		
			case 15: // Data Export
			{				
				$user=mysqli_real_escape_string($connection1, $_POST['p_user']);
				$pass=mysqli_real_escape_string($connection1, $_POST['p_pass']);	
													
				if(is_user_request_valid($connection1, $user, $pass, false)) // authenticated, trusted user
				{	
					$export_data = array();		
					$export_mode=mysqli_real_escape_string($connection1, $_POST['d_export_mode']);
				
					if($export_mode == 0) // export from primary database
					{
						$sensors=mysqli_real_escape_string($connection1, $_POST['d_sensors']);
						$date_start=mysqli_real_escape_string($connection1, $_POST['d_start']);
						$date_stop=mysqli_real_escape_string($connection1, $_POST['d_stop']);
						$step=mysqli_real_escape_string($connection1, $_POST['d_step']);
						$sensor_array = explode(", ",$sensors);	// split sensor_string into array						

						// get all datasets within the specified time range
						$query_export = "SELECT $sensors, t_unix FROM sensor_datasets WHERE t_unix >= UNIX_TIMESTAMP('$date_start') 
						AND t_unix < UNIX_TIMESTAMP('$date_stop') ORDER BY t_unix";						
						$result_query = mysqli_query($connection1, $query_export) or die("[ERROR_23] Failed to query sensor table in database!");
						
						if(!mysqli_num_rows($result_query)) // no data matching request - database did not return any rows for executed query
						{
							// return date/time of first dataset in database for information purposes
							$result_query = mysqli_query($connection1, "SELECT t_unix FROM sensor_datasets ORDER BY id LIMIT 1") 
							or die("[ERROR_24] Failed to query sensor table in database!");		
							$row = mysqli_fetch_array($result_query, MYSQLI_ASSOC);	
							echo json_encode('__SUCCESS;__db1;_NO_RESULT;'.$row['t_unix']);				
						}
						else // data available - output the selected data
						{	
							if($step == 5) // 5 seconds step - this is the default data acquisition time step -> no further processing required
							{								
								while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
								{
									$current_row = array();
									$current_row[] = $row["t_unix"]; // add timestamp
									foreach($sensor_array as $val)$current_row[] = $row["$val"]; // get all requested values (sensors) from current row		
									$export_data[] = $current_row; // save dataset into export array	
								}			
							}
							else // other time step specified for export -> processing needed in order to return only datasets that fit the speficied time step
							{											
								$first_taken = false;
								while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
								{
									// first dataset in specified time range already has been taken: proceed with choosing sets in regard to the specified time step
									if($first_taken)
									{
										// chose only datasets that fit into the specified time step and dismiss all in between
										if((intval($timestamp_lastSet) + $step) <= intval($row["t_unix"]))
										{										
											$current_row = array();
											$timestamp_lastSet = $row["t_unix"]; // update timestamp of the latest chosen dataset
											$current_row[] = $timestamp_lastSet; // add timestamp
											foreach($sensor_array as $val)$current_row[] = $row["$val"]; // get all requested values (sensors) from current row		
											$export_data[] = $current_row; // save dataset into export array													
										}	
									}
									else // no dataset has been taken yet: take the first set and save the initial starting timestamp
									{
										$current_row = array();
										$timestamp_lastSet = $row["t_unix"]; // update timestamp of the latest chosen dataset
										$current_row[] = $timestamp_lastSet; // add timestamp
										foreach($sensor_array as $val)$current_row[] = $row["$val"]; // get all requested values (sensors) from current row		
										$export_data[] = $current_row; // save dataset into export array	
										$first_taken = true;								
									}
								}							
							}																		
							// return export data as json		
							array_unshift($export_data, '__SUCCESS;__db1;'); // operation successful	
							echo json_encode($export_data);								
															 		   
							// log database activity with priority '0' -> (Info)
							mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
							VALUES ('$user', 'Data export (primary database)', '--', '0')");
						}			
					}
					else if($export_mode == 1) // export from secondary database
					{
						// connect to secondary database (WeeWx)
						$connection2=mysqli_connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DB2) 
						or die("[ERROR_01_2] Could not connect to secondary database!");	

						// get provided arguments
						$sensors=mysqli_real_escape_string($connection2, $_POST['d_sensors']);
						$date_start=mysqli_real_escape_string($connection2, $_POST['d_start']);
						$date_stop=mysqli_real_escape_string($connection2, $_POST['d_stop']);
						$step=mysqli_real_escape_string($connection2, $_POST['d_step']);
						$hilo=mysqli_real_escape_string($connection2, $_POST['d_hilo']);
						$sensor_array = explode(", ",$sensors);	// split sensor_string into array	
						$export_data_ex = array();						

						// get all datasets within the specified time range from the archive table
						$query_export = "SELECT $sensors, dateTime FROM archive WHERE dateTime >= UNIX_TIMESTAMP('$date_start') 
						AND dateTime < UNIX_TIMESTAMP('$date_stop') ORDER BY dateTime";						
						$result_query = mysqli_query($connection2, $query_export) or die("[ERROR_24] Failed to query archive table in database!");
						
						if(!mysqli_num_rows($result_query)) // no data matching request - database did not return any rows for executed query
						{
							// return date/time of first dataset in database for information purposes
							$result_query = mysqli_query($connection2, "SELECT dateTime FROM archive ORDER BY dateTime LIMIT 1") 
							or die("[ERROR_25] Failed to query archive table in database!");		
							$row = mysqli_fetch_array($result_query, MYSQLI_ASSOC);		
							echo json_encode('__SUCCESS;__db2;_NO_RESULT;'.$row['dateTime']);			
						}
						else // data available - output the selected data
						{	
							if($step == 300) // 5 minute step - this is the default data acquisition time step -> no further processing required
							{
								while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
								{									
									$current_row = array();
									$current_row[] = $row["dateTime"]; // add timestamp
									foreach($sensor_array as $val)$current_row[] = $row["$val"]; // get all requested values (sensors) from current row		
									$export_data_ex[] = $current_row; // save dataset into export array											
								}
							}
							else // other time step specified for export -> processing needed in order to return only datasets that fit the speficied time step
							{											
								$first_taken = false;
								while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
								{
									// first dataset in specified time range already has been taken: proceed with choosing sets in regard to the specified time step
									if($first_taken)
									{
										// chose only datasets that fit into the specified time step and dismiss all in between
										if((intval($timestamp_lastSet) + $step) <= intval($row["dateTime"]))
										{											
											$current_row = array();
											$timestamp_lastSet = $row["dateTime"]; // update timestamp of the latest chosen dataset
											$current_row[] = $timestamp_lastSet; // add timestamp
											foreach($sensor_array as $val)$current_row[] = $row["$val"]; // get all requested values (sensors) from current row		
											$export_data_ex[] = $current_row; // save dataset into export array												
										}	
									}
									else // no dataset has been taken yet: take the first set and save the initial starting timestamp
									{										
										$current_row = array();
										$timestamp_lastSet = $row["dateTime"]; // update timestamp of the latest chosen dataset
										$current_row[] = $timestamp_lastSet; // add timestamp
										foreach($sensor_array as $val)$current_row[] = $row["$val"]; // get all requested values (sensors) from current row		
										$export_data_ex[] = $current_row; // save dataset into export array											
										$first_taken = true;								
									}
								}							
							}		
							if($hilo == 1) // If High/Low Statistics should be included in the export
							{
								$export_data_hilo = array();
								foreach($sensor_array as $val) // loop through all selected sensor tables
								{
									// get all hi/lo entries within the specified time range
									$current_sensor_table = "archive_day_".$val;
									$query_export = "SELECT min, mintime, max, maxtime, dateTime FROM $current_sensor_table WHERE dateTime >= UNIX_TIMESTAMP('$date_start') 
									AND dateTime < UNIX_TIMESTAMP('$date_stop') ORDER BY dateTime";						
									$result_query = mysqli_query($connection2, $query_export) or die("[ERROR_hilo] Failed to query archive table in database!");
									$data_hilo_table = array();						
									while($row = mysqli_fetch_array($result_query, MYSQLI_ASSOC))
									{										
										$data_hilo_table[] = array(
															'dateTime' => $row["dateTime"],
															'min' => $row["min"],
															'mintime' => $row["mintime"],
															'max' => $row["max"],
															'maxtime' => $row["maxtime"]
															);											
									}	
									$export_data_hilo[] = $data_hilo_table;							
								}								
								$export_data[] = array('data' => $export_data_ex,
													   'hilo' => $export_data_hilo
													  );											
							}	
							else $export_data = $export_data_ex;													
							
							// return export data as json		
							array_unshift($export_data, '__SUCCESS;__db2;'); // operation successful	
							echo json_encode($export_data);									
																	 		   
							// log database activity with priority '0' -> (Info)
							mysqli_query($connection1, "INSERT INTO admin_log (user, action, reason, priority) 
							VALUES ('$user', 'Data export (secondary database)', '--', '0')");
						}
						mysqli_close($connection2);		
					}	
				}	
				else echo json_encode('[USER_ERROR_AUTH] User not authenticated!');													
				mysqli_free_result($result_query);	
				break;								
			}							
		}
		mysqli_close($connection1);				
	}	
	// *** FUNCTIONS *** //	
	/*
	* This function checks if the user sending a query request to the database is authenticated.
	*/
	function is_user_request_valid($connDB, $request_user, $request_pass, $admin_required)
	{
		/*  *** Function Parameters ***
		 *  $connDB 		-> (object) object of mysql connection
		 *  $request_user 	-> (string) user/admin account that is requesting the php-job
		 *  $request_pass 	-> (string) password of the user/admin account requesting the job
		 *  $admin_required	-> (bool)   true if only admin account can request this job, false if also normal user accounts are allowed to execute this job  
		*/	
		if($admin_required) // requested job requires admin privileges
		{
			$result_query = mysqli_query($connDB, "SELECT pass, salt FROM users WHERE email='$request_user' AND admin='1' Limit 1") 
			or die("[ERROR_Fx_admin] Failed to query user table in database!");
		}		
		else // requested job can also be executed by users
		{
			$result_query = mysqli_query($connDB, "SELECT pass, salt FROM users WHERE email='$request_user' Limit 1") 
			or die("[ERROR_Fx_user] Failed to query user table in database!");		
		}			
		if(!mysqli_num_rows($result_query))return false;
		else // username and account rank available in database
		{						
			$row = mysqli_fetch_array($result_query, MYSQLI_ASSOC);
			$salt_db = $row['salt']; // get password salt from database
			$pass_db = $row['pass']; // get password from database
			$pass_auth = sha1($request_pass.$salt_db);
			if(hash_equals($pass_db, $pass_auth)) // password is correct - user request is valid and user authenticated
			{
				return true;
			}
			else return false;		
		}
	}		
	/*
	* This function generates a Secure, Random String. This is used in order to generate a random salt for user passwords
	* Credits for function to Scott Arciszewski on stackoverflow.com
	* Link: https://stackoverflow.com/questions/4356289/php-random-string-generator/31107425#31107425
	*/
	function random_str($length, $keyspace = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
	{	
		/*  *** Function Parameters ***
		 *  $length 	-> (integer) 		   lenght of random output string (chars)
		 *  $keyspace 	-> (string - optional) char pool for random string generation
		*/
		$pieces = [];
		$max = mb_strlen($keyspace, '8bit') - 1;
		for ($i = 0; $i < $length; ++$i) {
			$pieces []= $keyspace[random_int(0, $max)];
		}
		return implode('', $pieces);
	}		
?>