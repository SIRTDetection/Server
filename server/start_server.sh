#!/bin/bash

## Based on model: https://github.com/mattbryson/bash-arg-parse/blob/master/arg_parse_example
## for arguments parser

# Abort on error
#set -e

function usage {
    echo "Usage: start_server.sh [OPTIONS] [SERVER OPTIONS]";
    echo "   ";
    echo "  --bhelp               : shows this dialog";
    echo "  --no_update           : does not attempt to update the server application during the startup"
    echo "  --no_pip              : does not attempt to update the PIP packages during the startup"
    echo "  --no_protoc           : does not attempt to compile the protoc sources"
    echo "  --no_pypath           : does not attempt to add the \"slim\" folder to the PYTHONPATH"
    echo "  --nice [VALUE]        : defines the nice value that will be used - by default: 10"
    echo "  --help                : shows the TensorflowServer help and settings"
}

function parseArgs {
    # positional arguments
    args=()

    # named arguments
    while [[ "$1" != "" ]]; do
        case "$1" in
        --bhelp )               usage;              exit;;
        --no_update )           no_update=true;;
        --no_pip )              no_pip=true;;
        --no_protoc )           no_protoc=true;;
        --no_pypath )           no_pypath=true;;
        --nice )                nice_value="$2";    shift;;
        * )                     args+=("$1")
        esac
        shift
    done

    # restore positional args
    set -- "${args[@]}"

    # set defaults
    if [[ -z "$no_update" ]]; then
        no_update=false
    fi
    if [[ -z "$no_pip" ]]; then
        no_pip=false
    fi
    if [[ -z "$no_protoc" ]]; then
        no_protoc=false
    fi
    if [[ -z "$no_pypath" ]]; then
        no_pypath=false
    fi
    if [[ -z "$nice_value" ]]; then
        nice_value=10
    fi
}

function checkNecessaryPackages {
    echo "Checking for necessary packages to be installed..."
    PROTOBUF_OK=$(dpkg-query -W --showformat='${Status}\n' protobuf-compiler|grep "install ok installed")

    if [[ "" == "$PROTOBUF_OK" ]]; then
        echo "Protoc is not installed - installing..."
        apt install protobuf-compiler -y
        echo "Protoc installed!"
    fi

    PYTHON3_OK=$(dpkg-query -W --showformat='${Status}\n' python3|grep "install ok installed")

    if [[ "" == "$PYTHON3_OK" ]]; then
        echo "Python3 is not installed - installing..."
        apt install --install-suggests python3 -y
        echo "Python3 installed!"
    fi

    PYTHON3_PIP_OK=$(dpkg-query -W --showformat='${Status}\n' python3-pip|grep "install ok installed")

    if [[ "" == "$PYTHON3_PIP_OK" ]]; then
        echo "PIP3 is not installed - installing..."
        apt install --install-suggests python3-pip -y
        echo "PIP3 installed!"
    fi

    PYTHON3_PIL_OK=$(dpkg-query -W --showformat='${Status}\n' python3-pil|grep "install ok installed")

    if [[ "" == "$PYTHON3_PIL_OK" ]]; then
        echo "Python 3 PIL is not installed - installing..."
        apt install python3-pil -y
        echo "Python3 PIL installed!"
    fi

    PYTHON3_LXML_OK=$(dpkg-query -W --showformat='${Status}\n' python3-lxml|grep "install ok installed")

    if [[ "" == "$PYTHON3_LXML_OK" ]]; then
        echo "Python 3 LXML is not installed - installing..."
        apt install python3-lxml -y
        echo "Python 3 LXML installed!"
    fi

    PYTHON3_TK_OK=$(dpkg-query -W --showformat='${Status}\n' python3-tk|grep "install ok installed")

    if [[ "" == "$PYTHON3_TK_OK" ]]; then
        echo "Python 3 TK is not installed - installing..."
        apt install python3-tk -y
        echo "Python 3 TK installed!"
    fi

    GIT_OK=$(dpkg-query -W --showformat='${Status}\n' git|grep "install ok installed")

    if [[ "" == "$PYTHON3_TK_OK" ]]; then
        echo "Git is not installed - installing..."
        apt install git -y
        echo "Git installed!"
    fi

    echo "All necessary packages are installed"
}

function run {
    parseArgs "$@"
    if ! [[ $(id -u) = 0 ]]; then
        echo "The script needs to be executed as root - this will only affect packages installation.
        The other scripts will be executed as regular user">&2
        exit 1
    fi

    if [[ $SUDO_USER ]]; then
        real_user=$SUDO_USER;
    else
        real_user=$(whoami);
    fi
    checkNecessaryPackages

    echo "Packages checked!"
    echo "$no_pip"

    if [[ "$no_pip" == false ]]; then
        echo "Looking for installations/upgrades on PIP necessary packages"
        if [[ $EUID -ne 0 ]]; then
            echo "Running as root - installing PIP packages globally"
            pip3 install -r requirements.txt --upgrade --quiet
#        else
#            echo "Running in user-mode - installing PIP packages locally"
#            pip3 install -r requirements.txt --upgrade --user --quiet
        fi
    else
        echo "Aborting PIP packages installation"
    fi
    echo "$no_update"

    if [[ "$no_update" == false ]]; then
        if [[ -d "../.git" ]]; then
            echo "Looking for new server updates..."
            sudo -u ${real_user} git pull --quiet
            echo "Obtained the latest updates"
        else
            echo "Downloading the server..."
            sudo -u ${real_user} git clone --recurse-submodules https://github.com/SIRTDetection/Server.git ../Server
            sudo -u ${real_user} git config submodule.recurse true
            echo "Downloaded the server"
            cd $(dirname $(readlink -f ../Server/server || realpath ../Server/server))
        fi
    fi

    echo "$no_protoc"

    if [[ "$no_protoc" == false ]]; then
        echo "Compiling protoc files"
        sudo -u ${real_user} protoc TensorflowServer/object_detection/protos/*.proto --proto_path=TensorflowServer --python_out=.
        echo "Compiled protoc files"
    else
        echo "Aborting protoc compilation"
    fi

    echo "$no_pypath"

    if [[ "$no_pypath" == false ]]; then
        echo "Exporting PYTHONPATH"
        RESEARCH=dirname $(readlink -f ../models/research || realpath ../models/research)
        export PYTHONPATH=${PYTHONPATH}:${RESEARCH}:${RESEARCH}/slim
        echo "Exported PYTHONPATH"
    else
        echo "Aborting PYTHONPATH definition"
    fi

    sudo -u ${real_user} nice -n${nice_value} python3 TensorflowServer/__init__.py "$@"
}

run "$@";
