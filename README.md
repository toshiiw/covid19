What is this?
=============

These are scripts to analyze covid-19 case numbers in Japan.

prefplot.py
-----------

You'll need csv files which contain per prefecture infection counts.

tokyoparse2.py
--------------

example:

```
#!/bin/sh

d=`date +%m%d`
wget -O tokyo-cards-$d.js https://stopcovid19.metro.tokyo.lg.jp/_nuxt/commons/cards.card~index.c4d9462.js
python3 tokyoparse2.py -o -1  ../Downloads/covid19/tokyo-positive-diagnosed-$d.html ../Downloads/covid19/tokyo-confirmed-$d.html
```
