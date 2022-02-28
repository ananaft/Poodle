#!/usr/bin/env bash

name_check () {
    for (( i=0; i<"${#1}"; i++ )); do
        if ! [[ "${1:$i:1}" == [[:alnum:]] ]]; then
            return 1
        fi
    done
    
    return 0
}

package_check () {
	local -i pcount="$(pip3 list --no-python-version-warning | tail -n +3 | \
	awk '{if ($1 ~ /^numpy$|^pandas$|^Pillow$|^pymongo$|^pyperclip$/) print $1}' | wc -l)"
	if (( "$pcount" < 5 )); then
		return 1
	else
		return 0
	fi
}

main () {
    cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
    cd ".."

    # Choose database
    if ! name_check "$1"; then
        echo 'Error: Please use only alphanumeric characters for a database name!'
        exit
    elif ! [[ "$1" ]]; then
        echo 'Error: No database specified!'
        exit
    fi
    local db="$1"

    # Start MongoDB
    term=$(ps -o comm= -p "$(($(ps -o ppid= -p "$(($(ps -o sid= -p "$$")))")))")
    if [[ "$term" == 'xfce4-terminal' ]]; then
        xfce4-terminal -e "mongod --dbpath ./db --logappend --nojournal"
    elif [[ "$term" == 'gnome-terminal-' ]]; then
        gnome-terminal -- sh -c "mongod --dbpath ./db --logappend --nojournal; bash"
    else
        echo "Running on unsupported terminal: $term"
        exit
    fi

    # Start Poodle
    if ! package_check; then
	echo 'Installing missing packages...'
    	pip3 install --no-python-version-warning -qqqr requirements.txt || \
    	pip3 install -qqqr requirements.txt
    fi
    python3 -i poodle/launch.py "$1"

    # Kill daemon on exit
    pid=$!
    wait $pid
    pid=$(ps a | awk '/sh -c mongod|mongod --dbpath/ {print $1}' | head -n 1)
    kill $pid
}
main "$@"
