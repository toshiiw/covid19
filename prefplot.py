#!/usr/bin/python3

import csv
import getopt
import sys
import matplotlib
import matplotlib.font_manager
from matplotlib import pyplot as plt
import numpy as np

def fontsetup():
    matplotlib.font_manager._rebuild()
    matplotlib.rcParams['font.sans-serif'] = ['IPAGothic'] + matplotlib.rcParams['font.sans-serif']

def load_prefpop():
    pp = {}
    with open("../Documents/prefpop2.csv") as f:
        cr = csv.reader(f)
        skip = True
        for r in cr:
            if r[0] == '全国':
                skip = False
                continue
            try:
                pp[r[0]] = int(''.join(r[1].split(',')))
            except ValueError:
                pass
    print(pp)
    return pp

class Plotter:
    def __init__(self, files):
        self.labels = []
        cases = []
        for fn in files:
            c1 = {}
            self.labels.append(fn.split('.')[0])
            with open(fn) as f:
                cr = csv.reader(f)
                for r in cr:
                    if len(r) == 0:
                       continue
                    if r[0] in c1:
                        raise ValueError("Duplicated key: " + r[0])
                    c1[r[0]] = int(r[1])
            cases.append(c1)
        k = set()
        for c1 in cases:
            k |= set(c1.keys())
        self.kl = list(k)
        self.kl.sort(key=lambda x: max([c.get(x,0) for c in cases]), reverse=True)
        print((k, cases))
        self.cases = []
        for k in self.kl:
            self.cases.append((k, [c.get(k, 0) for c in cases]))
        print(self.cases)
        self.prefpop = load_prefpop()

    def plot(self, diff=False, log=False):
        fontsetup()
        if diff:
            self.labels = self.labels[1:]
        x = np.arange(len(self.kl))

        width = .7 / len(self.labels)
        f, (ax1, ax2) = plt.subplots(2, 1)
        if diff:
            ax1.set_ylabel("new cases")
        else:
            ax1.set_ylabel("cases")
        xoff = -.5 * width * (len(self.labels) - 1)
        for i, l1 in enumerate(self.labels):
            if not diff:
                ax1.bar(x + xoff, [v[i] for k, v in self.cases], width, label=l1)
            ax2.bar(x + xoff, [1e3*v[i]/self.prefpop[k] for k, v in self.cases], width, label=l1)
            xoff += width

        if diff:
            xl = np.arange(len(self.labels)) * width - .5 * width * (len(self.labels) - 1)
            for i, kv in enumerate(self.cases):
                v = []
                for j in range(len(kv[1])-1):
                    v.append(kv[1][j+1] - kv[1][j])
                ax1.plot(xl + i, v)

        ax2.set_ylabel("ppm")
        for a in [ax1, ax2]:
            a.grid()
            a.set_xticks(x)
            a.set_xticklabels(self.kl)
            if log:
                a.set_yscale('log')
            a.legend()
        plt.show()

    def overlapplot(self, log=False, ppm=False, threshold=20):
        fontsetup()
        f, a = plt.subplots(1,1)
        for k, v in self.cases:
            try:
                i = 0
                while v[i] < threshold:
                    i += 1
            except IndexError:
                continue
            data = np.array(v[i:])
            if ppm:
                data = data * 1e3 / self.prefpop[k]
            a.plot(data, label=k)
        if log:
            a.set_yscale('log')
        a.grid()
        if ppm:
            a.set_ylabel("ppm")
        else:
            a.set_ylabel("cases")
        a.set_xlabel("days")
        a.legend()
        plt.show()
def zplot(files):
    prefpop = load_prefpop()
    fontsetup()
    assert(len(files) == 1)
    
    with open(files[0]) as f:
        cr = csv.reader(f)
        for r in cr:
            del prefpop[r[0]]
    data = list(prefpop.items())
    data.sort(key=lambda x: x[1], reverse=True)
    plt.bar([x[0] for x in data], [x[1] * 1e3 for x in data])
    plt.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
    plt.grid()
    plt.ylabel("population")
    plt.show()
    
if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'dlorz')
    plotargs = {}
    overlap = False
    zero = False
    for o, a in opts:
        if o == '-r':
            args.reverse()
        elif o == '-d':
            plotargs['diff'] = True
        elif o == '-l':
            plotargs['log'] = True
        elif o == '-o':
            overlap = True
        elif o == '-z':
            zero = True

    if zero:
        zplot(args)
    else:
        p = Plotter(args)
        if overlap:
            p.overlapplot(**plotargs)
            p.overlapplot(**plotargs, ppm=True)
        else:
            p.plot(**plotargs)
