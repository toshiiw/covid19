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

def plot(files, diff=False, log=False):
    fontsetup()
    prefpop = load_prefpop()
    labels = []
    cases = []
    for fn in files:
        c1 = {}
        labels.append(fn.split('.')[0])
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
    kl = list(k)
    kl.sort(key=lambda x: max([c.get(x,0) for c in cases]), reverse=True)
    if diff:
        for i in range(len(cases)-1):
            for k in kl:
                cases[i][k] = cases[i+1].get(k, 0) - cases[i].get(k, 0)
        cases.pop()
        labels = labels[1:]
    print((k, cases))
    x = np.arange(len(kl))

    width = .7 / len(labels)
    f, (ax1, ax2) = plt.subplots(2, 1)
    if diff:
        ax1.set_ylabel("new cases")
    else:
        ax1.set_ylabel("cases")
    xoff = -.5 * width * (len(labels) - 1)
    for c1, l1 in zip(cases, labels):
        if not diff:
            ax1.bar(x + xoff, [c1.get(k, 0) for k in kl], width, label=l1)
        ax2.bar(x + xoff, [1e3*c1.get(k, 0)/prefpop[k] for k in kl], width, label=l1)
        xoff += width
    if diff:
        xl = np.arange(len(labels)) * width - .5 * width * (len(labels) - 1)
        for i, k in enumerate(kl):
            ax1.plot(xl + i, [c1.get(k, 0) for c1 in cases])

    ax2.set_ylabel("ppm")
    for a in [ax1, ax2]:
        a.grid()
        a.set_xticks(x)
        a.set_xticklabels(kl)
        if log:
            a.set_yscale('log')
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
    opts, args = getopt.getopt(sys.argv[1:], 'dlrz')
    plotargs = {}
    zero = False
    for o, a in opts:
        if o == '-r':
            args.reverse()
        elif o == '-d':
            plotargs['diff'] = True
        elif o == '-l':
            plotargs['log'] = True
        elif o == '-z':
            zero = True

    if not zero:
        plot(args, **plotargs)
    else:
        zplot(args)
