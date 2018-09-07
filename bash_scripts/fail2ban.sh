#!/bin/bash

# Requires one argument, one of the following:
#  start
#  stop
#  ban
#  unban
#
# Optional second argument: IP for ban/unban

# Include file with the following content:
#   SERVER=Host del servidor FIR
#   HOST=Host donde se recoge el incidente


SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  TARGET="$(readlink "$SOURCE")"
  if [[ $TARGET == /* ]]; then
    echo "SOURCE '$SOURCE' is an absolute symlink to '$TARGET'"
    SOURCE="$TARGET"
  else
    DIR="$( dirname "$SOURCE" )"
    echo "SOURCE '$SOURCE' is a relative symlink to '$TARGET' (relative to '$DIR')"
    SOURCE="$DIR/$TARGET" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
  fi
done
RDIR="$( dirname "$SOURCE" )"
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

cd /var/apps/FIR/bash_scripts

source "$DIR/secret.conf"

# Display usage information
function show_usage {
  echo "Usage: $0 action <ip>"
  echo "Where action is start, stop, ban, unban"
  echo "and ip is optional passed to ban, unban"
  exit
}


function send_sms {
#  /usr/bin/curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$sid/SMS/Messages.json" -d "From=$from" -d "To=$to" -d "Body=$1" -u "$sid:$token" >> '/home/all/log/fail2ban-sms.log'

  echo "$1 $2" >> /var/apps/FIR/bash_scripts/script_fail2ban.log
  echo "0=$0 1=$1 2=$2"
  LINE=1 
  CATEGORY=25
  if [ $1 == "sshd" ];   then 
     LINE=2; 
     CATEGORY=26
  fi
  if [ $1 == "MAIL" ];  then 
     LINE=3; 
     CATEGORY=27
  fi
  if [ $1 == "FTP" ];   then 
     LINE=4;  
     CATEGORY=28
  fi
  if [ $1 == "DB" ];    then 
     LINE=5; 
     CATEGORY=29
  fi
  if [ $1 == "VESTA" ]; then 
     LINE=6; 
     CATEGORY=30
  fi

  curl -X POST http://127.0.0.1:4444/api/incidents  -H "Content-Type: application/json; charset=UTF-8" \
        -H "Authorization: Token $TOKEN" \
        --data '{"detection":2,"actor":'$ID_HOST',"plan":5,"date":"2017-02-17T09:55:56","is_starred":false,"subject":"'"$HOST"' > '"$2"' banned","description":"'"$HOST"'\n'"$2"' banned","severity":1,"is_incident":true,"is_major":false,"status":"O","confidentiality":1,"category":'$CATEGORY',"opened_by":1,"concerned_business_lines":['"$LINE"']}'>>fail2ban_bash.log 
      
  exit
}



# Check for script arguments
if [ $# -lt 1 ]
then
  show_usage
fi



# Take action depending on argument
if [ "$1" = 'start' ]
then
  message='Fail2ban+just+started.'
  send_sms $message
elif [ "$1" = 'stop' ]
then
  message='Fail2ban+just+stopped.'
  send_sms $message 
elif [ "$1" = 'ban' ]
then
  message=$([ "$2" != '' ] && echo "$3 $2 banned" || echo 'Fail2ban just banned an IP' )
  send_sms $message $1 $2 $3
elif [ "$1" = 'unban' ]
then
  message=$([ "$2" != '' ] && echo "Fail2ban+just+unbanned+$2" || echo "Fail2ban just unbanned an IP" )
  send_sms $message $1 $2 $3
else
  show_usage
fi
exit 


