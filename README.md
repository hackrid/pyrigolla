# pyrigolla?
... is a python based SCPI simulation of a Rigol VS5022D meant to interact with sigrok-cli/pulseview....

## Why?
In the near future I plan to use an esp32 as a standalone logic analyzer to feed (digital) data into sigrok-cli / pulseview for the use of protocol decoders and further analysis.
To approach this goal I start by building a python simulation of the basic communication between a SCPI client and sigrok using a local socket between the pyrigolla and sigrok-cli/pulseview.


## How to run
in terminal 1: 
python scpi-server.py --port 5555 --loglevel DEBUG

in another terminal:
sigrok-cli --driver=rigol-ds:conn=tcp-raw/127.0.0.1/5555 --frames 1 -l 5


Most of what you find here is lend frome here: https://gist.github.com/pklaus/b741eedc66b5dc01f49a
