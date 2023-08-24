#!/usr/bin/env bash

# Prints help
usage () {
    echo -e '\nThis will be the documentation for the shell script later on...\n'
}

# Loading animation
loading () {
    local -a dots=( '.  ' '.. ' '...' )
    local i=-1

    while kill -0 "$1" 2>/dev/null; do
	i=$(( (i+1) % 3 ))
	printf "\r$2${dots[i]}"
	sleep .4
    done
    printf "\r$2...\nDone.\n\n"
}

# Checks for correct database
db_check () {
    local message1='Error: No database specified!\n'
    local message2='Error: Database name contains non-alphanumeric characters!\n'
    # Ensure database is not a command option
    if [[ "${1:0:1}" == '-' ]]; then
	echo -e "$message1"
	exit 1
    fi
    # Ensure database has only alphanumeric characters
    for (( i=0; i<"${#1}"; i++ )); do
        if ! [[ "${1:$i:1}" == [[:alnum:]] ]]; then
	    echo -e "$message2"
            exit 1
        fi
    done

    return 0
}

# Install system-wide dependencies based on OS
install_system_dependencies () {
    local -a already_installed

    # Ubuntu/Debian
    local -a debian_packages=(
	'python3-pip' 'python3-venv' 'libgirepository1.0-dev' 'gcc'
	'libcairo2-dev' 'pkg-config' 'python3-dev' 'gir1.2-gtk-4.0'
    )
    # Install missing system packages
    cat /etc/os-release | grep -Eq '^ID=([Dd]ebian|[Uu]buntu)' &&
	{ for i in "${debian_packages[@]}"; do
	      apt list --installed 2>/dev/null | grep -q "^$i " &&
		  already_installed+=( "$i" )
	  done;
	  for i in "${already_installed[@]}"; do
	      debian_packages=( "${debian_packages[@]/$i}" )
	  done; } &&
	[[ -n "$debian_packages" ]] &&
	yes | sudo apt -qqq install "${debian_packages[@]}"

    # Manjaro/Arch
    local -a arch_packages=(
	'cairo' 'pkgconf' 'gobject-introspection' 'gtk4'
    )
    # Install missing system packages
    cat /etc/os-release | grep -Eq '^ID=([Aa]rch|[Mm]anjaro)' &&
	{ for i in "${arch_packages[@]}"; do
	      pacman -Q | grep -q "^$i " && already_installed+=( "$i" )
	  done;
	  for i in "${already_installed[@]}"; do
	      arch_packages=( "${arch_packages[@]/$i}" )
	  done; } &&
	[[ -n "$arch_packages" ]] &&
	yes | sudo pacman -S --needed "${arch_packages[@]}"
}

connect_local () {
    # If no MongoDB daemon is running in background,
    # initiate one manually
    if ! ps -A | grep -q 'mongod'; then
	kill_daemon=1
	# Create directory if necessary
	if [[ "$connection_type" == 'local' ]]; then
	    if ! ls | grep -q '^mongo$'; then
		mkdir mongo
	    fi
	fi
	# Determine correct terminal emulator for async command
	term=$(ps -o comm= -p "$(($(ps -o ppid= -p "$(($(ps -o sid= -p "$$")))")))")
	case "$term" in
	    xfce4-terminal)
		xfce4-terminal -e "mongod --dbpath ./mongo --logappend --nojournal"
		;;
	    gnome-terminal|gnome-terminal-)
		gnome-terminal -- sh -c "mongod --dbpath ./mongo --logappend --nojournal; bash"
		;;
	    urxvt|urxvtd)
		urxvtc -e mongod --dbpath ./mongo --logappend --nojournal
		;;
	    *)
		echo "Running on unsupported terminal: $term"
		exit 1
		;;
	esac
    fi

    connection_string='mongodb://localhost:27017'
}

connect_server () {
    # Ask for password if only username is provided
    [[ -z "$password" && -n "$username" ]] &&
	read -s -p 'Enter password:' password && echo

    connection_string="mongodb://${username}:${password}@${address}"
}

main () {
    # Parse command arguments
    while getopts "hls:u:p:" option; do
	case $option in
	    h)
		usage
		exit 0
		;;
	    l)
		[[ -n "$connection_type" ]] && usage && exit 1 ||
			connection_type='local'
		;;
	    s)
		[[ -n "$connection_type" ]] && usage && exit 1 ||
			connection_type='server'
		address="$OPTARG"
		;;
	    u)
		username="$OPTARG"
		;;
	    p)
		password="$OPTARG"
		;;
	    \?)
		exit 1
		;;
	esac
    done

    # Set base directory
    cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
    cd ".."
    # Create databases directory if necessary
    if ! ls | grep -q '^databases$'; then
	mkdir databases
    fi

    # Set database
    db="${@: -1}"
    db_check "$db"

    # Connect to MongoDB
    if [[ -z "$connection_type" ]]; then
	echo -e 'Please specify a connection type (-l|-s)!\n'
	usage
	exit 1
    elif [[ "$connection_type" == 'local' ]]; then
	connect_local
    elif [[ "$connection_type" == 'server' ]]; then
	connect_server
    fi

    # Install system-wide dependencies
    install_system_dependencies &
    pid=$!
    loading "$pid" 'Checking/installing system-wide dependencies'

    # Set up virtual environment
    [[ -n "$VIRTUAL_ENV" ]] ||
	{ ls | grep -q 'venv' &&
	      echo -e 'Entering virtual environment...' &&
	      source venv/bin/activate &&
	      echo -e 'Done.\n'; } ||
	{ echo -e 'Entering virtual environment...' &&
	      python3 -m venv venv &&
	      source venv/bin/activate &&
	      echo -e 'Done.\n'; }

    # Install python packages
    pip3 install --no-python-version-warning -qqr requirements.txt &
    pid=$!
    loading "$pid" 'Checking/installing python packages'

    # Start Poodle
    python3 -i poodle/launch.py "$username" "$password" "$connection_string" "$db"
    # Delete info stored in variables
    unset address
    unset username
    unset password
    unset connection_string

    # Kill daemon on exit if started by Poodle
    pid=$!
    wait $pid
    [[ -n "$kill_daemon" ]] &&
	pid=$(ps a | awk '/mongod/ {print $1}' | head -n 1) &&
	kill $pid
}

main "$@"
