
# 
# source /path/to/install/install.sh
# on your favorite shell's configuration file
# For example:
# vi ~/.bashrc
# source ~/Documents/duck/install/install.sh

path=$HOME/Documents/backup/duckii
mkdir -p $HOME/duck/
mkdir -p $HOME/duck/src/
cp -rf $path/main.py $HOME/duck/src/main.py
cp -rf $path/ducker.py $HOME/duck/src/ducker.py
cp -rf $path/fonts $HOME/duck/
cp -rf $path/images $HOME/duck/

duck_hatch() {
    echo "Initializing an empty project from duck. Say duck-duck!"
    mkdir -p debug 
    python3 -m venv debug/ducky/ 
    source debug/ducky/bin/activate 
    pip install --quiet pytest click colorama toml 

    mkdir -p debug/html 
    cp -rf $HOME/duck/images/logo.svg debug/html/ 
    cp -rf $HOME/duck/images/duck.jpg debug/html/ 
    cp -rf $HOME/duck/fonts debug/html/ 
}

duckk() {
	duck_hatch > /dev/null
}

alias duck-duck='source debug/ducky/bin/activate'
alias duck='python3 $path/main.py'
alias duck-hatch='duckk'

