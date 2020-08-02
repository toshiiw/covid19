from collections import deque
import csv
import datetime
import getopt
import json
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
        self.start = None
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

    def parsejs1(self, data, offset=0):
        do = datetime.timedelta(days=offset)
        res = []
        for d in data:
            d1 = datetime.datetime.strptime(d['diagnosed_date'], "%Y-%m-%d")
            d1 += do
            res.append((d1, d['count']))
        return np.array(res)

    def parsejs(self, f, offsets=None):
        s = fp.read()
        i = 0
        js = []
        while True:
            try:
                i += s[i:].index("JSON.parse(")
                i += 11 # len("JSON.parse(")
                delim = s[i]
                ei = s[i+1:].index(delim)
                js.append(json.loads(s[i+1:i+1+ei]))
                i += 1 + ei
            except ValueError:
                break
        if not len(js):
            raise ValueError("file is not js")
        print(list([x.keys() for x in js]))

        if offsets is None:
            offsets = [0, 0]
        for j in js:
            try:
                d = j['data']
                if 'diagnosed_date' not in d[0]:
                    continue
                if 'count' not in d[0]:
                    continue
                if 'missing_count' in d[0]:
                    self.data.append(('positive by reported', self.parsejs1(d, offsets[0]), offsets[0]))
                elif len(d[0].keys()) == 2:
                    self.data.append(('positive by diagnosed', self.parsejs1(d, offsets[1]), offsets[1]))
            except KeyError:
                pass

    def plot(self, diff=False, logscale=False):
        fig, ax1 = plt.subplots()
        for k, v, o in self.data:
            if o:
                ks = k + " (offset %d)" % o
            else:
                ks = k
            i = 0
            if self.start is not None:
                while v[i,0] < self.start:
                    i += 1
            ax1.plot_date(v[i:,0], v[i:,1], fmt='-', label=ks)
        if logscale:
            ax1.set_yscale('log')
        ax1.legend()
        if len(self.data) == 2:
            ax2 = ax1.twinx()
            ax2.set_ylabel("%s / %s" % (self.data[0][0], self.data[1][0]))
            if diff:
                self.plot_diff(ax2, self.data[0][1], self.data[1][1])
            else:
                self.plot_ratio(ax2, self.data[0][1], self.data[1][1])
        ax1.grid()
        plt.show()

    def plot_ratio(self, ax, d0, d1):
        """Plot ratio between 2 series"""
        dd = []
        dr = []
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
        i = 0
        if self.start is not None:
            while dd[i] < self.start:
                i += 1
        ax.plot_date(dd[i:], dr[i:], fmt='-', color='yellow')

    def plot_diff(self, ax, d0, d1):
        """Plot cumulative difference between 2 series"""
        i1 = 0
        for i0 in range(d0.shape[0]):
            try:
                while d0[i0,0] > d1[i1,0]:
                    print((d0[i0,0], d1[i1,0]))
                    i1 += 1
            except IndexError:
                break
            if d0[i0,0] == d1[i1,0]:
                break
        assert d0[i0,0] == d1[i1,0]
        i0s = i0
        d0s = 0
        d1s = 0
        dt = []
        dd = []
        for i0 in range(i0s, d0.shape[0]):
            d0s += d0[i0,1]
            try:
                d1s += d1[i1,1]
                assert d0[i0,0] == d1[i1,0]
            except IndexError:
                pass
            dt.append(d0[i0,0])
            dd.append(d0s - d1s)
            i1 += 1
        while i1 < d1.shape[0]:
            d1s += d1[i1,1]
            dt.append(d0[i0,0])
            dd.append(d0s - d1s)
            i1 += 1
        dd = np.array(dd)
        dd -= dd[-1]
        i = 0
        if self.start is not None:
            while dt[i] < self.start:
                i += 1
        ax.plot_date(dt[i:], dd[i:], fmt='-', color='yellow')

    def plot_r(self):
        """Plot weekly multiplication rate"""
        for k, v, o in self.data:
            self.plot_r1(k, v, o)

    def plot_r1(self, k, v, o):
        fig, ax1 = plt.subplots()
        if o:
            ks = k + " (offset %d)" % o
        else:
            ks = k
        i = 0
        if self.start is not None:
            while v[i,0] < self.start:
                i += 1
        ax1.plot_date(v[i:,0], v[i:,1], fmt='-', label=ks)
        ax1.legend()

        ax2 = ax1.twinx()
        ax2.set_ylabel("weekly ratio")
        dr = deque()
        ws = []
        rr = []
        rd = []

        wlen = 7
        wdiff = 7
        for i in range(v.shape[0]):
            dr.append(v[i,1])
            if len(dr) < wlen:
                continue
            ws.append(sum(dr))
            if len(ws) < wdiff + 1:
                continue
            try:
                rr.append(ws[-1] / ws[-1 - wdiff])
                rd.append(v[i,0])
            except ZeroDivisionError:
                pass
            dr.popleft()
        i = 0
        if self.start is not None:
            while rd[i] < self.start:
                i += 1
        ax2.plot_date(rd[i:], rr[i:], fmt='-', color='yellow')
        ax1.grid()
        plt.show()

if __name__ == '__main__':
    d = Data()
    offset = 0
    plotargs = {}
    ratio = False
    start = None
    opts, args = getopt.getopt(sys.argv[1:], 'dlo:rS:')
    for o, a in opts:
        if o == '-d':
            plotargs['diff'] = True
        elif o == '-l':
            plotargs['logscale'] = True
        elif o == '-o':
            offset = int(a)
        elif o == '-r':
            ratio = True
        elif o == '-S':
            start = datetime.datetime.strptime(a, "%Y-%m-%d")
    if start is not None:
        print(start)
        d.start = start
    for i, fn in enumerate(args):
        try:
            with open(fn) as fp:
                d.parsejs(fp, [0, offset])
        except Exception as e:
            print(e)
            with open(fn) as fp:
                d.parse(fp, offset if i > 0 else 0)
    fontsetup()
    if ratio:
        d.plot_r()
    else:
        d.plot(**plotargs)
