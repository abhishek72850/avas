pkg install termux-api

termux-setup-storage

cd ~/storage/shared

pip install wheel
pkg install libjpeg-turbo
LDFLAGS="-L/system/lib/" CFLAGS="-I/data/data/com.termux/files/usr/include/" pip install Pillow

pkg install clang
pkg install libxml2 libxslt
pip install cython

pip install -r requirements.txt