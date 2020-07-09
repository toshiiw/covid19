import csv
import datetime
import getopt
import os
import re
import sys

import numpy as np

import matplotlib
from matplotlib import pyplot as plt
from matplotlib import dates
from bs4 import BeautifulSoup

def fontsetup():
    matplotlib.font_manager._rebuild()
    matplotlib.rcParams['font.sans-serif'] = ['IPAGothic'] + matplotlib.rcParams['font.sans-serif']

class Data:
    def __init__(self):
        self.data = []
        self.this_year = datetime.datetime.now().date().year
        
    def parse(self, f, offset=0):
        soup = BeautifulSoup(f.read(), 'html.parser')
        tables = soup.find_all('table')
        assert len(tables) == 1
        do = datetime.timedelta(days=offset)
        d = []
        for e in tables[0].contents:
            if e.name == 'thead':
                # XXX assume a specific layout
                datalabel = e.contents[0].contents[1].string
                continue
            elif e.name != 'tbody':
                continue
            for ee in e.contents:
                v = int(''.join(ee.contents[2].string.split(',')))
                try:
                    md = map(int, ee.contents[0].string.split('/'))
                    d1 = datetime.datetime(self.this_year, *md)
                except ValueError:
                    try:
                        d1 = datetime.datetime.strptime(
                            ("%d " % self.this_year) + ee.contents[0].string, "%Y %B %d")
                    except Exception as e:
                        print(ee.contents[0].string)
                        print(e)
                        raise e
                d1 += do
                d.append((d1, v))
        d.reverse()
        self.data.append((datalabel, np.array(d), offset))

    def plot(self):
        fig, ax1 = plt.subplots()
        for k, v, o in self.data:
            if o:
                ks = k + " (offset %d)" % o
            else:
                ks = k
            ax1.plot_date(v[:,0], v[:,1], fmt='-', label=ks)
        ax1.legend()
        if len(self.data) == 2:
            ax2 = ax1.twinx()
            ax2.set_ylabel("%s / %s" % (self.data[0][0], self.data[1][0]))
            dd = []
            dr = []
            d0 = self.data[0][1]
            d1 = self.data[1][1]
            i1 = 0
            for i0 in range(d0.shape[0]):
                try:
                    while d0[i0,0] > d1[i1,0]:
                        print((d0[i0,0], d1[i1,0]))
                        i1 += 1
                except IndexError:
                    break
                if d0[i0,0] == d1[i1,0]:
                    try:
                        dr.append(d0[i0,1] / d1[i1,1])
                        dd.append(d0[i0,0])
                    except ZeroDivisionError:
                        pass
                    i1 += 1
                    continue
                elif d0[i0,0] < d1[i1,0]:
                    continue
            print(dd)
            ax2.plot_date(dd, dr, fmt='-', color='yellow')
        ax1.grid()
        plt.show()

if __name__ == '__main__':
    d = Data()
    offset = 0
    opts, args = getopt.getopt(sys.argv[1:], 'o:')
    for o, a in opts:
        if o == '-o':
            offset = int(a)
    for i, fn in enumerate(args):
        with open(fn) as fp:
            d.parse(fp, offset if i > 0 else 0)
    fontsetup()
    d.plot()
