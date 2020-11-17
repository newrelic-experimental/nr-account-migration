#!/bin/bash
#set -o nounset # exit script if trying to use an uninitialized variable
<<comment
set -o errexit # exit the script if any statement returns a non-true return value
comment
#Setting up the default value if not set.
: "${FILE:="jqdata.json"}"
: "${FILE_PAGINATION:="frompage"}"
: "${offset:=0}"
: "${UPDATE_FILE:="updatedjqdata.json"}"
: "${CONDITION_LIST_FOR_TO_POLICY:="topolicy.json"}"
: "${CONDITION_LIST_FOR_TO_POLICY_PAGINATION:="topage"}"
: "${no_of_record_per_page:=50}"
: "${loop_number:=0}"
: "${UPDATE_FILE_PAGINATION:="updatepage"}"
: "${offsetto:=0}"
: "${offsetfrom:=0}"
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
    create_dataset_if_more_page
    echo "cleaning up.."
    cleanup
}
create_dataset_if_more_page() {
        echo "Checking if pagination can fetch some more records.."
        $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ANOTHER_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$toanotheracpolicyid" > $CONDITION_LIST_FOR_TO_POLICY)
        total_to=`cat $CONDITION_LIST_FOR_TO_POLICY | python -m json.tool | jq '.meta.total'`
        ceiling_result_to=`echo "($total_to + $no_of_record_per_page - 1) / $no_of_record_per_page" | bc`
        echo "ceiling_result_to = $ceiling_result_to"
        if [ "$ceiling_result_to" != "0" ]
        then
                for (( i=1; i<=$ceiling_result_to; i++ )) 
                do 
                    $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ANOTHER_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$toanotheracpolicyid&offset=$offsetto&list=50" > $CONDITION_LIST_FOR_TO_POLICY_PAGINATION-$i.json)
                    offsetto=`echo "$offset + 50" | bc`
                    loop_to=`cat $CONDITION_LIST_FOR_TO_POLICY_PAGINATION-$i.json | python -m json.tool | grep -w type | wc -l`
                    for (( j=0; j<$loop_to; j++ ))
                    do
                        newname_spaced=`cat $CONDITION_LIST_FOR_TO_POLICY_PAGINATION-$i.json | jq ".data[$j].name"`
                        newconid_spaced=`cat $CONDITION_LIST_FOR_TO_POLICY_PAGINATION-$i.json | jq ".data[$j].id"`
                        newname=`echo ${newname_spaced//[[:blank:]]/}`
                        newconid=`echo ${newconid_spaced//[[:blank:]]/}`
                        echo "$newname:$newconid" >> newpolicyconditionlist-$i
                    done
                done
                $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ONE_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$fromoneacpolicyid" > $FILE)
                #loop_number=`cat $FILE | python -m json.tool | grep -w type | wc -l`
                loop_number=`cat $FILE | python -m json.tool | jq '.meta.total'`
                ceiling_result=`echo "($loop_number + $no_of_record_per_page - 1) / $no_of_record_per_page" | bc`
                for (( i=1; i<=$ceiling_result; i++ )) 
                do
                        $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ONE_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$fromoneacpolicyid&offset=$offsetfrom&list=50" > $FILE_PAGINATION-$i.json)
                        offsetfrom=`echo "$offset + 50" | bc`
                        h3=`cat $FILE_PAGINATION-$i.json | sed "s/$fromoneacpolicyid/$toanotheracpolicyid/g" > $UPDATE_FILE_PAGINATION-$i.json`
                        loop=`cat $UPDATE_FILE_PAGINATION-$i.json | python -m json.tool | grep -w type | wc -l`
                        for (( j=0; j<$loop; j++ ))
                        do
                            oldname_spaced=`cat $FILE_PAGINATION-$i.json | jq ".data[$j].name"`
                            oldconid_spaced=`cat $FILE_PAGINATION-$i.json | jq ".data[$j].id"`
                            oldname=`echo ${oldname_spaced//[[:blank:]]/}`
                            oldconid=`echo ${oldconid_spaced//[[:blank:]]/}`
                            echo "$oldname:$oldconid" >> oldpolicyconditionlist
                        done
                done
                for (( i=1; i<=$ceiling_result; i++ )) 
                do
                            testdata=`cat $UPDATE_FILE_PAGINATION-$i.json | jq ".data[$j]"`
                            echo "$testdata"
                            : "${put_count:=0}"
                            : "${post_count:=0}"
                            while read line
                            do
                                result_key=`echo $line | cut -d ':' -f 1`
                                result_value=`echo $line | cut -d ':' -f 2`
                                h2=`cat oldpolicyconditionlist | grep -w $result_key`
                                if [ "$?" == "0" ]
                                then
                                    #TODO: Later we can simply skip the PUT if name is common in from and to POLICies.. 
                                    if [ "$result_value" != "null" ]
                                    then
                                        echo "Ietration for page "[ $i ]" for PUT..."
                                        echo "+++++++++++++++++=PUT++++++++++++++++++"
                                        local result=`curl -X PUT "https://infra-api.newrelic.com/v2/alerts/conditions/$result_value" -H "X-Api-Key:$NEW_RELIC_ANOTHER_AC" -i -H 'Content-Type: application/json' -d "{\"data\": $testdata}"`
                                        #`expr "$put_count + 1"`
                                        put_count=`echo "$put_count + 1" | bc`
                                    fi
                                else
                                    echo "Ietration for page "[ $i ]" for POST..."
                                    echo $line >> post-should-not-happen.log 
                                    echo "======================POST==================="
                                    local result=$(curl -X POST 'https://infra-api.newrelic.com/v2/alerts/conditions' -H "X-Api-Key:$NEW_RELIC_ANOTHER_AC" -i -H 'Content-Type: application/json' -d "{\"data\": $testdata}")
                                    #`expr "$post_count + 1"`
                                    post_count=`echo "$post_count + 1" | bc`
                                fi
                            done < newpolicyconditionlist-$i
                        echo "Total PUT call for Page "[ $i ]": $put_count"
                        echo "Total POST call for Page "[ $i ]": $post_count"
                done
        else
                $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ONE_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$fromoneacpolicyid" > $FILE)
                #loop_number=`cat $FILE | python -m json.tool | grep -w type | wc -l`
                loop_number=`cat $FILE | python -m json.tool | jq '.meta.total'`
                echo "loop_number: $loop_number"
                ceiling_result=`echo "($loop_number + $no_of_record_per_page - 1) / $no_of_record_per_page" | bc`
                echo "ceiling_result: $ceiling_result"
                for (( i=1; i<=$ceiling_result; i++ ))
                do
                        $(curl -v -X GET --header "X-Api-Key: $NEW_RELIC_ONE_AC" "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=$fromoneacpolicyid&offset=$offsetfrom&list=50" > $FILE_PAGINATION-$i.json)
                        offsetfrom=`echo "$offset + 50" | bc`
                        echo "offsetfrom: $offsetfrom"
                        h3=`cat $FILE_PAGINATION-$i.json | sed "s/$fromoneacpolicyid/$toanotheracpolicyid/g " > $UPDATE_FILE_PAGINATION-$i.json`
                        loop=`cat $UPDATE_FILE_PAGINATION-$i.json | python -m json.tool | grep -w type | wc -l`
                        for (( j=0; j<$loop; j++ ))
                        do
                                testdata=`cat $UPDATE_FILE_PAGINATION-$i.json | jq ".data[$j]"`
                                echo "======================POST==================="
                                result=$(curl -v -X POST 'https://infra-api.newrelic.com/v2/alerts/conditions' -H "X-Api-Key:$NEW_RELIC_ANOTHER_AC" -i -H 'Content-Type: application/json' -d "{\"data\": $testdata}")
                                echo "No of condiftion created for policy id: $toanotheracpolicyid is" `expr $j + 1` 
                        done
                done 
        fi
}
cleanup() {
    echo "cleaning up started.."
    #`rm -f $CONDITION_LIST_FOR_TO_POLICY $FILE $UPDATE_FILE oldpolicyconditionlist newpolicyconditionlist`
    `rm -f *.json oldpolicyconditionlist newpolicyconditionlist-*`
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
