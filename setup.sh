RED='\033[1;31m'
GREEN='\033[0;32m'
NC='\033[0m'
if ! python3 -c 'import sys; assert sys.version_info >= (3,6)' > /dev/null; 
then 
    echo -e "${RED}python 3.6 or higher is required!${NC}";
else
    pkgs='libboost-all-dev libc6:i386 build-essential zlib1g-dev libmpfr-dev cmake'
    install=false
    for pkg in $pkgs; do
        status="$(dpkg-query -W --showformat='${db:Status-Status}' "$pkg" 2>&1)"
        if [ ! $? = 0 ] || [ ! "$status" = installed ]; then
             install=true
             echo -e "${RED} Missing package $pkg. ${NC}" 
        break
        fi
    done
    if "$install"; then
        echo -e "${GREEN} Installing missing packages. ${NC}"
        sudo apt install $pkgs
    fi
    echo -e "${GREEN} Installing python modules. ${NC}"
    pip install -r requirements.txt > /dev/null
    echo -e "${GREEN} Downloading git submodules. ${NC}"
    git submodule update --init
    if [ ! -f aspmc/external/flow-cutter/flow_cutter_pace17 ];
    then
        echo -e "${GREEN} Compiling flow-cutter. ${NC}"
        cd aspmc/external/flow-cutter/
        g++ -Wall -std=c++11 -O3 -DNDEBUG src/*.cpp -o flow_cutter_pace17 --static
	    cd ../../../
    fi
    if [ ! -f aspmc/external/minisat-definitions/bin/defined ] || [ ! -f aspmc/external/minisat-definitions/bin/minisat ];
    then
        echo -e "${GREEN} Compiling minisat-definitions. ${NC}"
        cd aspmc/external/minisat-definitions/
        bash setup.sh static
	    cd ../../../
    fi
    if [ ! -f aspmc/external/d4/d4_static ];
    then
        echo -e "${GREEN} Compiling d4. ${NC}"
        cd aspmc/external/d4/
        make -j4 rs
	    cd ../../../
    fi
    if [ ! -f aspmc/external/sharpsat-td/bin/sharpSAT ];
    then
        echo -e "${GREEN} Compiling sharpSAT-TD. ${NC}"
        cd aspmc/external/sharpsat-td/
	mkdir bin
        bash setupdev.sh static
	    cd ../../../
    fi
    if [ ! -f aspmc/external/preprocessor/bin/sharpSAT ];
    then
        echo -e "${GREEN} Compiling sharpSAT-TD Preprocessor. ${NC}"
        cd aspmc/external/preprocessor/
        bash setupdev.sh static
	    cd ../../../
    fi
    echo -e "${GREEN} Done! ${NC}"
fi
