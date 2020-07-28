from nsga3_base import nsga3_base
import numpy as np
import random

#ディープ
from deap import algorithms
from deap import base
#from deap.benchmarks.tools import igd
from deap import creator
from deap import tools
from functools import partial
#プロット
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D # ３Dグラフ作成のため

#id取得
import os
import sys
import traceback

#翼型解析ライブラリ
from xfoil import XFoil
from xfoil.model import Airfoil
import XfoilAnalize as xa

#自作モジュール
import foilConductor as fc
from change_output import SetIO
import timeout_decorator

class nsga3_spline(nsga3_base):
    #遺伝子
    #[x1, x2, x3,...,x6, y1, y2, ...., y6]
    def __init__(self):
        super().__init__()
        self.NDIM = 12
        self.BOUND_LOW = [0.66, 0.33,  0.15,  0.15,  0.33, 0.66,\
                         -0.05, -0.05, -0.05,  -0.2, -0.2, -0.2]
        self.BOUND_UP = [0.85, 0.66, 0.33, 0.33, 0.66, 0.85,\
                          0.4,  0.4,  0.4,  0.2, 0.2, 0.2]
        self.re = 5000
        self.NOBJ = 2
        self.MU = 100
        self.NGEN = 300#世代数
        self.CXPB = 1.0#交叉の確立(1を100%とする)
        self.MUTPB = 1.0#突然変異の確立(1を100%とする)
        self.cx_eta = 20
        self.mut_eta = 20

    def readPop(self,file,gen):
        f=open(file)
        fd = f.read()
        f.close()
        pop = fd.split('#')

        pop = [a for a in pop if a != '#' and a != '' and a!='\n']
        pop = pop[gen].split('\n')
        pop = [a.split(',') for a in pop if a != '']
        pop = [[float(c) for c in ind if c != ''] for ind in pop]
        return pop

    def writePop(self,pop,file):
        output = ''
        for ind in pop:
            for c in ind:
                output += str(c) + ','
            output += '\n'
        output += '#\n'
        with open(file, mode='a') as f:
            f.write(output)
        return file

    def evaluate(self,individual):
        DELTA = 1e10
        print("====================")
        #----------------------------------
        #遺伝子に基づいて新翼型を生成
        #----------------------------------
        #遺伝子に基づきスプライン翼型を作成
        x = individual[:int(len(individual)/2)]
        x.insert(0,1.0)
        x.insert(int(len(x)/2)+1,0.0)
        x.append(1.0)
        y = individual[int(len(individual)/2):]
        if not (all([u - d > 0 for u, d in zip(y[:int(len(y)/2)], y[int(len(y)/2):])]) or all([u - d < 0 for u, d in zip(y[:int(len(y)/2)], y[int(len(y)/2):])])):
            print("crossed")
            return [DELTA*10]*self.NOBJ
        y.insert(0,0.0)
        y.insert(int(len(y)/2)+1,0.0)
        y.append(0.0)
        newdat = fc.spline_foil(x, y, 200)
        shape_dat = fc.shape_dat([[a, b] for a, b in zip(newdat[0][::-1], newdat[1][::-1])])

        #翼型の形に関する情報を取得する
        #foilpara == [最大翼厚、最大翼厚位置、最大キャンバ、最大キャンバ位置、S字の強さ]
        foil_para = fc.get_foil_para(shape_dat)
        mt, mta, mc, mca, s, crossed, bd, bt, bc, smooth, td = foil_para

        if crossed:
            print("crossed_a")
            return [DELTA*10]*self.NOBJ
        else:
            print("hi_a")

        #新しい翼型をAerofoilオブジェクトに適用
        datx = np.array(newdat[0][::-1])
        daty = np.array(newdat[1][::-1])
        newfoil = Airfoil(x = datx, y = daty)

        #翼型の形に関する拘束条件
        penalty = 0
        if not all([t >= 0.0035 for t in td[10:80]]):
            penalty += 100 * (sum([abs(t - 0.0035)*10 for t in td[15:85] if t - 0.0035 < 0]))
        if not all([t <= 0.015 for t in td[:15]]):
            penalty += 100 * (sum([abs(t - 0.015)*10 for t in td[:15] if t > 0.015]))
        if mta > 0.4:
            penalty += 100 * (mta - 0.4)
        if mc < 0.0:
            penalty += 100 * (-mc)
        if datx[0] > 1.002 or datx[0] < 0.998:
            print("invalid foil")
            return [DELTA*10]*self.NOBJ
        #----------------------------------
        #新翼型の解析
        #----------------------------------
        try:
            xf = XFoil()
            #レイノルズ数の設定
            xf.airfoil = newfoil
            xf.Re = self.re
            xf.print = False
            xf.max_iter = 40

            #xf.polar = "polar" + id
            #境界要素法計算時1ステップにおける計算回数
            #xf.repanel(n_nodes = 180)
            #計算結果格納
            #result = xf.OneAlpha()
            cl, cd, cm, cp  = xf.a(5.0)
        #----------------------------------
        #目的値
        #----------------------------------
            if cl >= 0:
                obj1 = 1/cl
            else:
                obj1 = self.delta
            #揚抗比のピークを滑らかに(安定性の最大化)
            obj2 = cd


        except Exception as e:
            obj1,obj2=[DELTA]*self.NOBJ
            traceback.print_exc()

        if (np.isnan(obj1)):
            obj1 = DELTA
        if (np.isnan(obj2)):
            obj2 = DELTA

        return [obj1 + penalty, obj2 + penalty]

    def main(self):
        self.setup()

        # Initialize statistics object
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "std", "min", "avg", "max"

        #初期化(個体生成のこと)
        pop = self.toolbox.population(n=self.MU)#[creator.Individual(a) for a in self.readPop('pop1.log',-1)]##
        start = 0
        #進化の始まり
        # Begin the generational process
        for gen in range(start,self.NGEN):

            if(gen == start):
                #with open('pop1.log', mode='w') as f:
                #    f.write('')
                #0世代目の評価
                # Evaluate the individuals with an invalid fitness
                invalid_ind = [ind for ind in pop if not ind.fitness.valid]
                fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit

                #0世代目の統計
                # Compile statistics about the population
                record = stats.compile(pop)
                logbook.record(gen=gen, evals=len(invalid_ind), **record)

            else:
                offspring = algorithms.varAnd(pop, self.toolbox, self.CXPB, self.MUTPB)
                #評価
                # Evaluate the individuals with an invalid fitness
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit

                #淘汰
                # Select the next generation population from parents and offspring
                pop = self.toolbox.select(pop + offspring, self.MU)


            #評価
            pop_fit = np.array([ind.fitness.values for ind in pop])

            #----------------------------------
            #途中経過プロット
            #----------------------------------
            #1世代ごとに翼型をファイルに書き出す
            k = 0
            for ind in pop:
                try:
                    k += 1
                    x = ind[:int(len(ind)/2)]
                    x.insert(0,1.0)
                    x.insert(int(len(x)/2)+1,0.0)
                    x.append(1.0)
                    y = ind[int(len(ind)/2):]
                    y.insert(0,0.0)
                    y.insert(int(len(y)/2)+1,0.0)
                    y.append(0.0)

                    d = fc.spline_foil(x, y)
                    newdat = [[a, b] for a, b in zip(d[0], d[1])]
                    if k == 1:
                        X = x
                        Y = y
                        fc.write_datfile(datlist=newdat,newfile_name = "newfoil_g"+str(gen)+str("_best.dat"))
                    fc.write_datfile(datlist=newdat,newfile_name = "newfoil"+str(k)+str(".dat"))
                except Exception as e:
                    print("message:{0}".format(e))

            #新翼型の描画
            if (gen == start):
                fig = plt.figure(figsize=(7, 7))
                fig2 = plt.figure(figsize=(7, 7))
                ax1 = fig.add_subplot(111)
                ax2 = fig2.add_subplot(111)
                ax1.set_xlim([-0.1,1.1])
                ax1.set_ylim([-0.5,0.5])

            ##評価値のプロット
            p = [ind.fitness.values for ind in pop]
            p1 = [i[0] for i in p if i[0]]
            p2 = [j[1] for j in p if j[1]]
            #p3 = [k[2] for k in p if k[2]]
            ax2.cla()
            plt.figure(fig2.number)
            plt.title('generation:'+str(gen))
            ax2.set_xlabel("obj1")
            ax2.set_ylabel("obj2")
            #ax2.set_zlabel("smoothness")
            #ax2.view_init(elev=11, azim=-25)
            ax2.scatter(p1, p2, marker="o", label="Population")
            ax2.autoscale(tight = True)
            #plt.savefig("./nsga3_gen/nsga3_gen_scaled"+str(gen)+".png")
            #ax2.set_xlim(0, self.obj1_max)
            #ax2.set_ylim(0, self.obj2_max)
            #ax2.set_zlim(0, self.obj2_max)
            #plt.savefig("./nsga3_gen/nsga3_gen"+str(gen)+".png")
            plt.pause(0.1)
            d = fc.spline_foil(X, Y)
            newdat = [[a, b] for a, b in zip(d[0], d[1])]
            fc.write_datfile(datlist=newdat,newfile_name = "./newfoil_gen"+str(gen)+str(".dat"))
            ax1.cla()
            plt.figure(fig.number)
            ax1.set_xlim([-0.1,1.1])
            ax1.set_ylim([-0.5,0.5])
            ax1.plot(d[0],d[1])
            plt.title('generation:'+str(gen))
            plt.savefig("./newfoil_gen"+str(gen)+".png")
            plt.pause(0.1)


            #======================================================


            # Compile statistics about the new population
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)
            with SetIO('stats.log'):
                #stas.logに統計データを出力
                print(logbook.stream)

        return pop, logbook

if __name__ == '__main__':
    ng = nsga3_spline()
    #翼型最適化開始
    try:
        pop, stats = ng.main()
    except KeyboardInterrupt:
        print("Ctrl + Cで停止しました")
        pass

    #最終世代の評価値取得
    pop_fit = np.array([ind.fitness.values for ind in pop])

    #10個の最適翼型候補をファイルに書き出す
    k = 0
    for ind, fit in zip(pop[:10], pop_fit[:10]):
        try:
            k += 1
            x = ind[:int(len(ind)/2)]
            x.insert(0,1.0)
            x.insert(int(len(x)/2)+1,0.0)
            x.append(1.0)
            y = ind[int(len(ind)/2):]
            y.insert(0,0.0)
            y.insert(int(len(y)/2)+1,0.0)
            y.append(0.0)

            d = fc.spline_foil(x, y)
            newdat = [[a, b] for a, b in zip(d[0], d[1])]

            fc.write_datfile(datlist=newdat,newfile_name = "newfoil"+str(k)+str(".dat"))
        except Exception as e:
            print("message:{0}".format(e))

    #10個の最適翼型候補の評価値を出力
    k = 0
    for ind, fit in zip(pop, pop_fit):
        try:
            k += 1
            print(k)
            print("individual:" + str(ind) + "\nfit:" + str(fit))
        except Exception as e:
            print("message:{0}".format(e))

    #pf = problem.pareto_front(ref_points)
    #print(igd(pop_fit, pf))

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111)

    p = np.array([ind.fitness.values for ind in pop])
    ax.scatter(p[:, 0], p[:, 1], marker="o", label="Final Population")

    #ax.scatter(pf[:, 0], pf[:, 1], pf[:, 2], marker="x", c="k", s=32, label="Ideal Pareto Front")

    ref_points = tools.uniform_reference_points(ng.NOBJ, ng.P)

    ax.scatter(ref_points[:, 0], ref_points[:, 1], marker="o", label="Reference Points")

    ax.autoscale(tight=True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("nsga3.png")
