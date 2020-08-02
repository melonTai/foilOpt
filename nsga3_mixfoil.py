#!python3.6
import random
from math import factorial

import numpy as np
#import pymop.factory

#ディープ
from deap import algorithms
from deap import base
#from deap.benchmarks.tools import igd
from deap import creator
from deap import tools

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

#自作モジュール
from my_modules import foilConductor as fc
from my_modules.change_output import SetIO
from my_modules.nsga3_base import nsga3_base

class nsga3(nsga3_base):
    def __init__(self):
        super().__init__()
        self.datfiles = ['foils/AG24.dat','foils/AG14.dat','foils/AG16.dat','foils/AG38.dat','foils/SD8040 (10%).dat']
        self.code_division = 4#混合比率をコードにする際の分解数
        self.NDIM = len(self.datfiles)*self.code_division#遺伝子数=親翼型の数×比率の分解能
        self.re = 150000

    def decoder(self,individual,code_division):
        #遺伝子を混合比にデコード
        ratios = []
        for i in range(0,len(individual),code_division):
            ratio = 0
            for j in range(code_division):
                ratio += individual[i+j]
            ratios.append(ratio)
        return ratios

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #(いじるのここから
    #=====================================================
    #評価関数の定義
    #=====================================================
    def evaluate(self,individual):
        #解析が発散した際の評価値
        DELTA = 1e10
        #----------------------------------
        #遺伝子に基づいて新翼型を生成
        #----------------------------------
        #遺伝子をデコード
        ratios = self.decoder(individual, self.code_division)

        #遺伝子に基づき翼型を混合して、新しい翼型を作る
        datlist_list = [fc.read_datfile(file) for file in self.datfiles]
        datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
        newdat = fc.interpolate_dat(datlist_shaped_list,ratios)

        #翼型の形に関する情報を取得する
        mt, mta, mc, mca, s, crossed, bd, bt, bc, smooth, td = fc.get_foil_para(newdat)

        #新しい翼型をAerofoilオブジェクトに適用
        datx = np.array([ax[0] for ax in newdat])
        daty = np.array([ax[1] for ax in newdat])
        newfoil = Airfoil(x = datx, y = daty)

        #----------------------------------
        #翼の形に関する拘束条件
        #----------------------------------
        penalty = 0
        #キャンバに関する拘束条件
        if(mc<0):
            penalty -= mc
        #最大翼厚に関する拘束条件
        if(mt<0.08):
            penalty += 0.08-mt
        if(mt>0.11):
            penalty += mt-0.11
        #最大翼厚位置に関する拘束条件
        if(mta<0.23):
            penalty += 0.23 - mta
        if(mta>0.3):
            penalty += mta - 0.3

        #----------------------------------
        #新翼型の解析
        #----------------------------------
        xf = XFoil()
        xf.airfoil = newfoil
        #レイノルズ数の設定
        xf.Re = self.re
        #境界要素法計算時1ステップにおける計算回数
        xf.max_iter = 60
        xf.print = False

        #計算結果格納
        a, cl, cd, cm, cp = xf.cseq(0.4, 1.1, 0.1)
        #----------------------------------
        #目的値
        #----------------------------------
        try:
            #揚抗比の逆数を最小化
            obj1 = 1/lr[1]

            #揚抗比のピークを滑らかに(安定性の最大化)
            maxlr = max(lr)
            maxlr_index = lr.index(maxlr)
            obj2 = abs(maxlr - lr[maxlr_index+1])

            #下面の反りを最小化(製作再現性の最大化)
            obj3 = s

        except Exception as e:
            obj1,obj2,obj3=[DELTA]*self.NOBJ
            traceback.print_exc()

        if (np.isnan(obj1) or obj1 > 1):
            obj1 = DELTA
        if (np.isnan(obj2) or obj2 > 1):
            obj2 = DELTA
        if (np.isnan(obj3) or obj3 > 1):
            obj3 = DELTA

        obj1 += penalty
        obj2 += penalty
        obj3 += penalty

        return [obj1, obj2, obj3]
    #いじるのここまで)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #=====================================================
    #最適化アルゴリズム本体
    #=====================================================
    def main(self,seed=None):
        self.setup()

        random.seed(seed)
        # Initialize statistics object
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "std", "min", "avg", "max"

        #初期化(個体生成のこと)
        pop = self.toolbox.population(n=self.MU)

        # Begin the generational process
        for gen in range(self.NGEN):

            if(gen == 0):
                #0世代目の評価
                # Evaluate the individuals with an invalid fitness
                invalid_ind = [ind for ind in pop if not ind.fitness.valid]
                fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit

                #0世代目の統計
                # Compile statistics about the population
                record = stats.compile(pop)
                logbook.record(gen=0, evals=len(invalid_ind), **record)

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
            for ind in pop[:10]:
                ratios = self.decoder(ind,self.code_division)
                try:
                    k += 1
                    datlist_list = [fc.read_datfile(file) for file in self.datfiles]
                    datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
                    newdat = fc.interpolate_dat(datlist_shaped_list,ratios)
                    fc.write_datfile(datlist=newdat,newfile_name = "newfoil"+str(k)+str(".dat"))
                except Exception as e:
                    print("message:{0}".format(e))

            #翼型それぞれの評価値を出力する
            k = 0
            for ind, fit in zip(pop, pop_fit):
                try:
                    k += 1
                    print(k)
                    print("individual:" + str(ind) + "\nfit:" + str(fit))
                except Exception as e:
                    print("message:{0}".format(e))

            #新翼型の描画
            datlist_list = [fc.read_datfile(file) for file in self.datfiles]
            datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
            newdat = fc.interpolate_dat(datlist_shaped_list,self.decoder(pop[0],self.code_division))
            fc.write_datfile(datlist=newdat,newfile_name = "./newfoil_gen"+str(gen)+str(".dat"))

            if (gen == 0):
                fig = plt.figure(figsize=(7, 7))
                fig2 = plt.figure(figsize=(7, 7))
                ax1 = fig.add_subplot(111)
                ax2 = fig2.add_subplot(111, projection = '3d')
                ax1.set_xlim([-0.1,1.1])
                ax1.set_ylim([-0.5,0.5])
                ax2.set_xlim(0, 1)
                ax2.set_ylim(0, 1)
                ax2.set_zlim(0, 1)

            #評価値のプロット
            p = [ind.fitness.values for ind in pop]
            p1 = [i[0] for i in p if i[0]]
            p2 = [i[1] for i in p if i[1]]
            p3 = [i[2] for i in p if i[2]]
            ax2.cla()
            plt.figure(fig2.number)
            plt.title('generation:'+str(gen))
            ax2.set_xlabel("obj1")
            ax2.set_ylabel("obj2")
            ax2.set_zlabel("obj3")
            ax2.view_init(elev=11, azim=-25)
            ax2.scatter(p1, p2, p3, marker="o", label="Population")
            ax2.autoscale(tight = True)
            plt.pause(0.1)
            newdat_x = [dat[0] for dat in newdat]
            newdat_y = [dat[1] for dat in newdat]
            ax1.cla()
            plt.figure(fig.number)
            ax1.set_xlim([-0.1,1.1])
            ax1.set_ylim([-0.5,0.5])
            ax1.plot(newdat_x,newdat_y)
            plt.title('generation:'+str(gen))
            plt.pause(0.1)
            #======================================================


            # Compile statistics about the new population
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)
            with SetIO('stats.log'):
                #stas.logに統計データを出力
                print(logbook.stream)

        return pop, logbook

if __name__ == "__main__":
    ng = nsga3()
    #翼型最適化開始
    try:
        pop, stats = ng.main()
        #最終世代の評価値取得
        pop_fit = np.array([ind.fitness.values for ind in pop])

        #10個の最適翼型候補の評価値を出力
        k = 0
        for ind, fit in zip(pop, pop_fit):
            try:
                k += 1
                print(k)
                print("individual:" + str(ind) + "\nfit:" + str(fit))
            except Exception as e:
                print("message:{0}".format(e))

    except KeyboardInterrupt:
        print("Ctrl + Cで停止しました")
        pass
