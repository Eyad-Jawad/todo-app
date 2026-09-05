#!/bin/bash

cleanup() {
    kill "$FASTAPI_PID" 2>/dev/null
    wait "$FASTAPI_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

uvicorn todo_app.services:app --host 0.0.0.0 --port 8000 &>/dev/null &
FASTAPI_PID=$!

for i in $(seq 1 30); do
    if curl -s -o /dev/null http://127.0.0.1:8000/docs; then
        break
    fi
    sleep 1
done

#####################################################
# Check for regular sign up

sign_up_response=$(curl -s -w "\n%{http_code}" -X POST http://127.0.0.1:8000/auth/sign_up \
    -H "Content-Type: application/json" \
    -d '{"username":"EyadJawad", "password":"password123"}' \
)

sign_up_result=$(sed '$d' <<< "$sign_up_response")
sign_up_status=$(tail -n1 <<< "$sign_up_response")

if [[ $sign_up_status -ne 200 ]]; then
    detail=$(echo "$sign_up_result" | jq -r '.detail')
    echo "Sign up failed, status code: $sign_up_status, $detail"
    exit 1
fi

access_token=$(echo "$sign_up_result" | jq -r '.access_token')

#####################################################
# Log out check

log_out_response=$(curl -s -w "\n%{http_code}" -X POST http://127.0.0.1:8000/auth/log_out \
    -H "Content-Type: application/json" \
    -d '{"access_token":"'"$access_token"'"}' \
)

log_out_result=$(sed '$d' <<< "$log_out_response")
log_out_status=$(tail -n1 <<< "$log_out_response")

log_out_detail=$(echo "$log_out_result" | jq -r '.logged_out')

if [[ $log_out_status -ne 200 || $log_out_detail != "true" ]]; then
    detail=$(echo "$log_out_result" | jq -r '.detail')
    echo "Log out failed, status code: $log_out_status, $detail"
    exit 1
fi

#####################################################
# Log in check

log_in_response=$(curl -s -w "\n%{http_code}" -X POST http://127.0.0.1:8000/auth/log_in \
    -H "Content-Type: application/json" \
    -d '{"username":"EyadJawad", "password":"password123"}' \
)

log_in_result=$(sed '$d' <<< "$log_in_response")
log_in_status=$(tail -n1 <<< "$log_in_response")

access_token=$(echo "$log_in_result" | jq -r '.access_token')

if [[ $log_in_status -ne 200 ]]; then
    detail=$(echo "$log_in_result" | jq -r '.detail')
    echo "Log in failed, status code: $log_in_status, $detail"
    exit 1
fi

#####################################################
# Check add todo

add_todo_response=$(curl -s -w "\n%{http_code}" -X POST http://127.0.0.1:8000/todos/add \
    -H "Content-Type: application/json" \
    -d '{"text":"Str", "access_token":"'"$access_token"'"}' \
)

add_todo_result=$(sed '$d' <<< "$add_todo_response")
add_todo_status=$(tail -n1 <<< "$add_todo_response")

if [[ $add_todo_status -ne 200 ]]; then
    detail=$(echo "$add_todo_result" | jq -r '.detail')
    echo "Add todo failed, status code: $add_todo_status, $detail"
    exit 1
fi

#####################################################
# Validate todos

get_all_todos_response=$(curl -q -s -w "\n%{http_code}\n" -G http://127.0.0.1:8000/todos/all \
    --data-urlencode "access_token=$access_token"
)

get_all_todos_result=$(sed '$d' <<< "$get_all_todos_response")
get_all_todos_status=$(tail -n1 <<< "$get_all_todos_response")

todo_id=$(echo "$get_all_todos_result" | jq -r '.[0].id' <<< "$get_all_todos_result")
todo_text=$(echo "$get_all_todos_result" | jq -r '.[0].todo' <<< "$get_all_todos_result")
todo_is_done=$(echo "$get_all_todos_result" | jq -r '.[0].is_done' <<< "$get_all_todos_result")

if [[ $get_all_todos_status -ne 200 ]]; then
    detail=$(echo "$get_all_todos_result" | jq -r '.detail' <<< "$get_all_todos_result")
    echo "Get all todos failed, status code: $get_all_todos_status, $detail"
    exit 1
fi

if [[ $todo_id -ne 1 || $todo_text != "Str" || $todo_is_done != "false" ]]; then
    echo "Unexpected todo was recived: $get_all_todos_result"
    exit 1
fi

#####################################################
# Toggle a todo

toggle_todo_response=$(curl -s -w "\n%{http_code}" -X PATCH http://127.0.0.1:8000/todos/toggle/ \
    -H "Content-Type: application/json" \
    -d '{"todo_id":1, "access_token":"'"$access_token"'"}' \
)

toggle_todo_result=$(sed '$d' <<< "$toggle_todo_response")
toggle_todo_status=$(tail -n1 <<< "$toggle_todo_response")

if [[ $toggle_todo_status -ne 200 ]]; then
    detail=$(echo "$toggle_todo_result" | jq -r '.detail')
    echo "Toggle todo failed, status code: $toggle_todo_status, $detail"
    exit 1
fi


#####################################################
# Validate todos

get_all_todos_response=$(curl -q -s -w "\n%{http_code}\n" -G http://127.0.0.1:8000/todos/all \
    --data-urlencode "access_token=$access_token"
)

get_all_todos_result=$(sed '$d' <<< "$get_all_todos_response")
get_all_todos_status=$(tail -n1 <<< "$get_all_todos_response")

todo_id=$(echo "$get_all_todos_result" | jq -r '.[0].id' <<< "$get_all_todos_result")
todo_text=$(echo "$get_all_todos_result" | jq -r '.[0].todo' <<< "$get_all_todos_result")
todo_is_done=$(echo "$get_all_todos_result" | jq -r '.[0].is_done' <<< "$get_all_todos_result")

if [[ $get_all_todos_status -ne 200 ]]; then
    detail=$(echo "$get_all_todos_result" | jq -r '.detail' <<< "$get_all_todos_result")
    echo "Get all todos failed, status code: $get_all_todos_status, $detail"
    exit 1
fi

if [[ $todo_id -ne 1 || $todo_text != "Str" || $todo_is_done != "true" ]]; then
    echo "Unexpected todo was recived: $get_all_todos_result"
    exit 1
fi

#####################################################
# Delete todo

delete_todo_response=$(curl -s -w "\n%{http_code}" -X DELETE http://127.0.0.1:8000/todos/delete/ \
    -H "Content-Type: application/json" \
    -d '{"todo_id":1, "access_token":"'"$access_token"'"}' \
)

delete_todo_result=$(sed '$d' <<< "$delete_todo_response")
delete_todo_status=$(tail -n1 <<< "$delete_todo_response")

if [[ $delete_todo_status -ne 200 ]]; then
    detail=$(echo "$delete_todo_result" | jq -r '.detail')
    echo "Delete todo failed, status code: $delete_todo_status, $detail"
    exit 1
fi

#####################################################
# Validate todos

get_all_todos_response=$(curl -q -s -w "\n%{http_code}\n" -G http://127.0.0.1:8000/todos/all \
    --data-urlencode "access_token=$access_token"
)

get_all_todos_result=$(sed '$d' <<< "$get_all_todos_response")
get_all_todos_status=$(tail -n1 <<< "$get_all_todos_response")

detail=$(echo "$get_all_todos_result" | jq -r '.detail' <<< "$get_all_todos_result")

if [[ $get_all_todos_status -ne 404 || $detail != "You don't have any todos." ]]; then
    echo "Get all todos failed, status code: $get_all_todos_status, $detail"
    exit 1
fi

#####################################################
# Check delete account

delete_account_response=$(curl -s -w "\n%{http_code}" -X DELETE http://127.0.0.1:8000/auth/delete_account \
    -H "Content-Type: application/json" \
    -d '{"username":"EyadJawad", "password":"password123"}' \
)

delete_account_result=$(sed '$d' <<< "$delete_account_response")
delete_account_status=$(tail -n1 <<< "$delete_account_response")

account_deleted=$(echo "$delete_account_result" | jq -r '.account_deleted' <<< "$delete_account_result")

if [[ $delete_account_status -ne 200 || $account_deleted != "true" ]]; then
    detail=$(echo "$delete_account_result" | jq -r '.detail' <<< "$delete_account_result")
    echo "Delete failed, status code: $delete_account_status, $detail"
    exit 1
fi

#####################################################

echo "Done! All tests passed!"
