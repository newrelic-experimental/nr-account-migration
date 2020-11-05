#!/bin/bash
#set -o nounset # exit script if trying to use an uninitialized variable
<<comment
set -o errexit # exit the script if any statement returns a non-true return value
comment
#Setting up the default value if not set.
: "${FILE:="jqdata.json"}"
: "${UPDATE_FILE:="updatedjqdata.json"}"
: "${CONDITION_LIST_FOR_TO_POLICY:="topolicy.json"}"
#set -x
main() {
    echo "Starting the infra specific conditiopns show..Copy from one AC to another AC."
    echo "Checking jq tool dependency.."
    echo "$@"
    check_jq_tool_dependency
    process_request "$@"
}
process_request() {
    echo "processing the request.."
    check_args "$@"
    create_dataset
    loop_number=`cat $FILE | python -m json.tool | grep -w type | wc -l`
    echo $loop_number
    local h3=`cat $FILE | sed "s/$fromoneacpolicyid/$toanotheracpolicyid/g" > $UPDATE_FILE`
    echo "restoring infra conditions to a policy id in different NR account.."
    for (( i=0; i<$loop_number; i++ ))
    do
        local testdata=`cat $UPDATE_FILE | jq ".data[$i]"`
        echo "$testdata"
        oldname=`cat $FILE | jq ".data[$i].name"`
        oldconid=`cat $FILE | jq ".data[$i].id"`
        echo "$oldname:$oldconid" > oldpolicyconditionlist
        condition_list_data=`cat $CONDITION_LIST_FOR_TO_POLICY | jq '.data[]'`
        if [ "$condition_list_data" != "" ]
        then
            newname=`cat $CONDITION_LIST_FOR_TO_POLICY | jq ".data[$i].name"`
            newconid=`cat $CONDITION_LIST_FOR_TO_POLICY | jq ".data[$i].id"`
            echo "$newname:$newconid" > newpolicyconditionlist
            local h1=`cat newpolicyconditionlist`
            echo "$h1"
            while read line
            do
                result_key_spaced=`echo $line | cut -d ':' -f 1`
                result_key=`echo ${result_key_spaced//[[:blank:]]/}`
                result_value_spaced=`echo $line | cut -d ':' -f 2`
                result_value=`echo ${result_value_spaced//[[:blank:]]/}`
            done < newpolicyconditionlist 
                local h2=`cat oldpolicyconditionlist | grep -w $result_key`
                if [ "$?" = 0 ]
                then
                    if [ "$result_value" != "null" ]
                    then
                        local result=`curl -X PUT "https://infra-api.newrelic.com/v2/alerts/conditions/$result_value" -H "X-Api-Key:$NEW_RELIC_ANOTHER_AC" -i -H 'Content-Type: application/json' -d "{\"data\": $testdata}"`
                    fi
                else
                    local result=$(curl -X POST 'https://infra-api.newrelic.com/v2/alerts/conditions' -H "X-Api-Key:$NEW_RELIC_ANOTHER_AC" -i -H 'Content-Type: application/json' -d "{\"data\": $testdata}")
                fi
            echo "No of condiftion created for policy id: $toanotheracpolicyid is" `expr $i + 1`
        else
            local result=$(curl -X POST 'https://infra-api.newrelic.com/v2/alerts/conditions' -H "X-Api-Key:$NEW_RELIC_ANOTHER_AC" -i -H 'Content-Type: application/json' -d "{\"data\": $testdata}")
        fi
    done
    echo "cleaning up.."
    cleanup
}
create_dataset() {
    echo "Downloading reference data from https://infra-api.newrelic.com/v2/alerts/conditions"
    $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ONE_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$fromoneacpolicyid" > $FILE)
    $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ONE_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$toanotheracpolicyid" > $CONDITION_LIST_FOR_TO_POLICY)
	echo "Download dataset completed"
}
cleanup() {
    echo "cleaning up started.."
    `rm -f $CONDITION_LIST_FOR_TO_POLICY $FILE $UPDATE_FILE oldpolicyconditionlist newpolicyconditionlist`
    echo "cleanup done"
}
check_args() {
    echo "Checking arguments.."
    if [[ "$NEW_RELIC_ONE_AC" != "" && "$NEW_RELIC_ANOTHER_AC" != "" ]]; then
        if [ "$#" -eq 0 -a "$#" -ge 3 ]
        then
            show_help
            exit 1002
        else
            echo "$1" > placeholder_set_1
            echo "$2" > placeholder_set_2 
            local key1=$(cat placeholder_set_1 | cut -d '=' -f1)
            local key2=$(cat placeholder_set_2 | cut -d '=' -f1)
            fromoneacpolicyid=$(cat placeholder_set_1 | cut -d '=' -f2)
            toanotheracpolicyid=$(cat placeholder_set_2 | cut -d '=' -f2)
            `rm -f placeholder_set_1`
            `rm -f placeholder_set_2`
            if [[ "$key1" == "--fromoneacpolicyid" && "$key2" == "--toanotheracpolicyid" && "$fromoneacpolicyid" != "" && "$toanotheracpolicyid" != "" ]]
            then
                    : ' 
                            echo "---$?---"
                            echo "fromoneacpolicyid = $fromoneacpolicyid"
                    '
                    echo "envs looks good!"
            else
                    show_help
                    exit 1003
            fi
        fi
        else
        echo "ENVs are not set.."
        show_help
        exit
    fi
}
show_help() {
  cat <<EOM
  Mandatory: python 2.6 onwards and jq should be installed..
  NOTE: For debian distribution jq installation will be done automatically.
  OPTIONS:
  
  RUN CMD:
  export NEW_RELIC_ONE_AC=""
  &
  export NEW_RELIC_ANOTHER_AC=""
  
  Usage: $(basename "$0") --fromoneacpolicyid="" --toanotheracpolicyid=""
  
  THEN.
  e.g.: $(basename "$0") --fromoneacpolicyid="" --toanotheracpolicyid=""
  
EOM
}
check_jq_tool_dependency() {
     local distribution=`uname -a | grep -i ubuntu`
                if [ "$distribution" != "" ]
                then
                    local qresult=$(dpkg-query -l 'jq')
                    if [ "$?" -eq 0 ]
                    then
                        echo "needed tool jq is installed, good to go.. "
                    else
                        echo "Installing jq.."
            			local update=`apt-get update -y`
                        local jq=`apt-get install jq -y`
                        echo "jq installed"
                    fi
                else
                    echo "platform is not supported..please install jq manually.."
                    #exit 1001
                fi
}
main "$@"