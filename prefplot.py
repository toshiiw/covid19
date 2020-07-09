#!/usr/bin/python3

import csv
import getopt
import sys
import matplotlib
import matplotlib.font_manager
from matplotlib import pyplot as plt
import numpy as np
from scipy import stats

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

    def decay(self, gamma):
        ncases = []
        for k, v in self.cases:
            x = 0
            d0 = 0
            newv = []
            for d1 in v:
                incr = d1 - d0
                x -= x * gamma
                x += incr
                newv.append(x)
                d0 = d1
            ncases.append((k, newv))
        self.cases = ncases
        
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

    def fftplot(self, threshold=100):
        fontsetup()
        for k, v in self.cases:
            d = []
            if v[-1] < threshold:
                continue
            for j in range(len(v)-1):
                d.append(v[j+1] - v[j])
            d = np.array(d)
            dlen = d.shape[-1]
            plt.plot(np.fft.rfftfreq(dlen), np.absolute(np.fft.rfft(d)),
                     label=k)
            plt.plot(np.fft.rfftfreq(dlen), np.absolute(np.fft.rfft(d*np.hamming(dlen)))/.54,
                     label=(k+'(hamming)'))
            plt.grid()
            plt.legend()
            plt.show()
            plt.scatter(d[:-1], d[1:], label=k) # XXX
            plt.grid()
            plt.legend()
            plt.show()
            f, (ax1, ax2) = plt.subplots(2, 1)
            ax1.hist(d, label=k, bins=20) # XXX
            ax2.hist(d[:-1]+d[1:], bins=20)
            ax1.legend()
            plt.show()

    def overlapplot(self, log=False, ppm=False, predict=False, threshold=20):
        fontsetup()
        f, a = plt.subplots(1,1)
        colorind = 0
        for k, v in self.cases:
            data = np.array(v)
            if ppm:
                data = data * 1e3 / self.prefpop[k]
            try:
                i = 0
                while data[i] < threshold:
                    i += 1
            except IndexError:
                continue
            data = data[i:]
            color = "C%d" % colorind
            a.plot(data, color=color, label=k)
            if predict and len(data) >= 7: # XXX
                r = stats.linregress(np.arange(len(data)-7, len(data)), np.log(data[-7:]))
                print("%s %.3g" % (k, r.slope))
                xr = np.arange(len(data)-1, len(data)+7)
                a.plot(xr, np.exp(xr * r.slope + r.intercept), color=color, linestyle=':')
            colorind += 1
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
    opts, args = getopt.getopt(sys.argv[1:], 'dfg:loprt:z')
    plotargs = {}
    fftplot = False
    overlap = False
    zero = False
    gamma = 0
    ths = []
    for o, a in opts:
        if o == '-r':
            args.reverse()
        elif o == '-d':
            plotargs['diff'] = True
        elif o == '-f':
            fftplot = True
        elif o == '-g':
            gamma = float(a)
        elif o == '-l':
            plotargs['log'] = True
        elif o == '-o':
            overlap = True
        elif o == '-p':
            plotargs['predict'] = True
        elif o == '-t':
            ths = [int(x) for x in a.split(',')]
        elif o == '-z':
            zero = True

    if zero:
        zplot(args)
    else:
        p = Plotter(args)
        if gamma > 0:
            p.decay(gamma)
        if overlap:
            try:
                plotargs['threshold'] = ths[0]
            except IndexError:
                pass
            p.overlapplot(**plotargs)
            try:
                plotargs['threshold'] = ths[1]
            except IndexError:
                pass
            p.overlapplot(**plotargs, ppm=True)
        elif fftplot:
            try:
                plotargs['threshold'] = ths[0]
            except IndexError:
                pass
            p.fftplot(**plotargs)
        else:
            p.plot(**plotargs)
