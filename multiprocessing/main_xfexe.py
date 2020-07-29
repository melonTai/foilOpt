import random
from math import factorial
import math

import numpy
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

#並列処理
from multiprocessing import Pool,Value

#自作モジュール
import foilConductor as fc
import XfoilAnalize as xa

def decoder(individual,code_division):
    #遺伝子を混合比にデコード
    ratios = []
    for i in range(0,len(individual),code_division):
        ratio = 0
        for j in range(code_division):
            ratio += individual[i+j]
        ratios.append(ratio)
    return ratios

#=====================================================
#親翼型の選択
#=====================================================
obj1_max = 1
obj2_max = 1
obj3_max = 1
foil_path = 'foils/'
datfiles = ['AG24.dat','AG14.dat','AG16','AG38.dat','SD8040 (10%).dat','SD7084 (9.6%).dat','SD7037.dat']
#---------------------------------------
#フィルにパスをつなぐ
for i in range(len(datfiles)):
    datfiles[i] = foil_path + datfiles[i]
#---------------------------------------

#=====================================================
#最適化の定義
#=====================================================
NOBJ = 3#評価関数の数
#K = 10
code_division = 6#混合比率をコードにする際の分解数
NDIM = len(datfiles)*code_division#遺伝子数=親翼型の数×比率の分解能
P = 12
H = factorial(NOBJ + P - 1) / (factorial(P) * factorial(NOBJ - 1))
BOUND_LOW, BOUND_UP = -5.0/code_division, 5.0/code_division#遺伝子定義域
#problem = pymop.factory.get_problem(PROBLEM, n_var=NDIM, n_obj=NOBJ)#ベンチマーク

MU = 400#人口の数#int(H + (4 - H % 4))
#print(MU)
NGEN = 200#世代数
CXPB = 1.0#交叉の確立(1を100%とする)
MUTPB = 1.0#突然変異の確立(1を100%とする)

# Create uniform reference point
ref_points = tools.uniform_reference_points(NOBJ, P)

# Create classes
creator.create("FitnessMin", base.Fitness, weights=(-1.0,) * NOBJ)
creator.create("Individual", list, fitness=creator.FitnessMin)
##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#評価関数の定義
#(いじるのは基本この中)
def evaluate(individual):
    global code_division
    ratios = decoder(individual, code_division)
    #===========================================
    #翼型を混合し、新翼型のdatファイルを書き出す
    #==========================================
    datlist_list = [fc.read_datfile(file) for file in datfiles]
    datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
    newdat = fc.interpolate_dat(datlist_shaped_list,ratios)
    #foilpara == [最大翼厚、最大翼厚位置、最大キャンバ、最大キャンバ位置、S字の強さ]
    foil_para = fc.get_foil_para(newdat)

    mt, mta, mc, mca, s = foil_para
    #print(obj1_max,obj2_max,obj3_max)
    #--------------------
    #翼の形に関する拘束条件
    penalty = 0
    print('===================')
    if(mc<0):
        print("out of the border")
        print("reverse_cmaber")
        penalty -= mc
    if(mt<0.08):
        print("out of the border")
        print("too_thin")
        penalty += 0.08-mt
    if(mt>0.11):
        print("out of the border")
        print("too_fat")
        penalty += mt-0.11
    #if(foil_para[4]>0.03):
    #    print("out of the border")
    #    print("peacock")
    #    print('===================')
    #    return (1.0+(foil_para[4]-0.03),)*NOBJ
    if(mta<0.23):
        print("out of the border")
        print("Atama Dekkachi!")
        penalty += 0.23 - mta
    if(mta>0.3):
        print("out of the border")
        print("Oshiri Dekkachi!")
        penalty += mta - 0.3

    if penalty > 0:
        return [1.0 + penalty]*NOBJ
    #--------------------
    id = str(os.getpid())
    dir_path = 'dump'
    try:
        os.makedirs(dir_path)
    except FileExistsError:
        pass
    newfile_name = 'newfoil' + id + '.dat'
    foilfile = fc.write_datfile(datlist=newdat,newfile_name = dir_path + '/' +  newfile_name)

    #==========================================
    #新翼型の解析
    #==========================================
    set1 = xa.XfoilAnalize(cseq=[0.4,1.1,0.1],foilfile=foilfile,polar="polar1" + id)
    #set2 = xa.XfoilAnalize(foilfile=newfile_name,polar="polar2" + id,Re=150000,cl=0.5)
    #set3 = xa.XfoilAnalize(foilfile=newfile_name,polar="polar3" + id,Re=100000,cl=0.5)

    try:
        Lrlist = set1.Cseq(timeout=9)["Lrlist"]
        maxLr = max(Lrlist)
        maxindex = Lrlist.index(maxLr)

    #==========================================
    #目的値
    #==========================================
        obj1 = 1/Lrlist[0]#揚抗比の最大化
        obj2 = abs(Lrlist[maxindex] - Lrlist[maxindex+1])#揚抗比のピークを滑らかに(安定性の最大化)
        obj3 = foil_para[4]#下面の反りを最小化(製作再現性の最大化)#abs(set2.OneCL()["Alpha"]-set3.OneCL()["Alpha"])

        #正規化
        obj1 = obj1 if obj1<=1 else 1.0#値域<1.0
        obj2 = obj2 if obj2<=1 else 1.0#値域<1.0
        obj3 = obj3 if obj3<=1 else 1.0#値域<1.0

        print("individual",individual)
        print("evaluate",obj1,obj2,obj3)
        print("max_thickness",foil_para[0])
        print("at",foil_para[1])
        print("max_camber",foil_para[2])
        print("at",foil_para[3])
        print("S",foil_para[4])
        print('===================')
    except Exception as e:
        obj1,obj2,obj3=[1.0]*NOBJ
        traceback.print_exc()
        print("individual",individual)
        print("evaluate",obj1,obj2,obj3)
        print("max_thickness",foil_para[0])
        print("at",foil_para[1])
        print("max_camber",foil_para[2])
        print("at",foil_para[3])
        print("S",foil_para[4])
        print('===================')

    return [obj1,obj2,obj3]
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Toolbox initialization
def uniform(low, up, size=None):
    try:
        return [random.uniform(a, b) for a, b in zip(low, up)]
    except TypeError:
        return [random.uniform(a, b) for a, b in zip([low] * size, [up] * size)]
##
toolbox = base.Toolbox()
toolbox.register("attr_float", uniform, BOUND_LOW, BOUND_UP, NDIM)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.attr_float)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("evaluate",evaluate)
toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=30.0)
toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)
toolbox.register("select", tools.selNSGA3, ref_points=ref_points)

def main(seed=None):
    global obj1_max,obj2_max,obj3_max, CXPB, MUTPB
    pool = Pool(4)#同時並列数(空白にすると最大数になる)
    toolbox.register("map", pool.map)

    random.seed(seed)

    # Initialize statistics object
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    pop = toolbox.population(n=MU)

    #0世代目の評価
    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    #0世代目の統計
    # Compile statistics about the population
    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(invalid_ind), **record)
    print(logbook.stream)

    #描画準備
    plt.ion()

    #進化の始まり
    # Begin the generational process
    for gen in range(1, NGEN):
        offspring = algorithms.varAnd(pop, toolbox, CXPB, MUTPB)
        #評価
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        #淘汰
        # Select the next generation population from parents and offspring
        pop = toolbox.select(pop + offspring, MU)


        print("------objs_before-------")
        print(obj1_max,obj2_max,obj3_max)
        #最大値取得
        pop_fit = numpy.array([ind.fitness.values for ind in pop])
        fits1 = [obj[0] for obj in pop_fit]
        _obj1_max = max(fits1)
        fits2 = [obj[1] for obj in pop_fit]
        _obj2_max = max(fits2)
        fits3 = [obj[2] for obj in pop_fit]
        _obj3_max = max(fits3)

        #最大値に応じて正規化
        if _obj1_max <= 1.0:
            obj1_max = _obj1_max
        if _obj2_max <= 1.0:
            obj2_max = _obj2_max
        if _obj3_max <= 1.0:
            obj3_max = _obj3_max

        print("------objs_after-------")
        print(obj1_max,obj2_max,obj3_max)

        #======================================================
        #---------途中経過プロット----------

        ##1世代ごとに翼型を書き出す
        k = 0
        for ind in pop[:10]:
            global code_division
            ratios = decoder(ind,code_division)
            try:
                k += 1
                datlist_list = [fc.read_datfile(file) for file in datfiles]
                datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
                newdat = fc.interpolate_dat(datlist_shaped_list,ratios)
                fc.write_datfile(datlist=newdat,newfile_name = "newfoil"+str(k)+str(".dat"))
            except Exception as e:
                print("message:{0}".format(e))
        #

        ##翼型それぞれの評価値を出力する
        k = 0
        for ind, fit in zip(pop, pop_fit):
            try:
                k += 1
                print(k)
                print("individual:" + str(ind) + "\nfit:" + str(fit))
            except Exception as e:
                print("message:{0}".format(e))
        #

        plt.cla()#消去
        ##新翼型の描画
        datlist_list = [fc.read_datfile(file) for file in datfiles]
        datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
        newdat = fc.interpolate_dat(datlist_shaped_list,decoder(pop[0],code_division))
        fc.write_datfile(datlist=newdat,newfile_name = "./foil_dat_gen/newfoil_gen"+str(gen)+str(".dat"))
        plt.title('generation:'+str(gen))
        newdat_x = [dat[0] for dat in newdat]
        newdat_y = [dat[1] for dat in newdat]
        plt.xlim([0,1])
        plt.ylim([-0.5,0.5])
        plt.plot(newdat_x,newdat_y)
        plt.savefig("./newfoil_gen/newfoil_gen"+str(gen)+".png")
        plt.draw()#描画
        plt.pause(0.1)#描画待機

        ##評価値のプロット
        fig = plt.figure(figsize=(7, 7))
        ax = fig.add_subplot(111, projection="3d")
        p = [ind.fitness.values for ind in pop]
        p1 = [i[0] for i in p]
        p2 = [j[1] for j in p]
        p3 = [k[2] for k in p]
        ax.set_xlim(0,obj1_max)
        ax.set_ylim(0,obj2_max)
        ax.set_zlim(0,obj3_max)
        ax.scatter(p1, p2, p3, marker="o", s=24, label="Final Population")
        ref = tools.uniform_reference_points(NOBJ, P)
        ax.scatter(ref[:, 0], ref[:, 1], ref[:, 2], marker="o", s=24, label="Reference Points")
        ax.view_init(elev=11, azim=-25)
        #ax.autoscale(tight=True)
        plt.legend()
        plt.title("nsga3_gen:"+str(gen))
        plt.tight_layout()
        plt.savefig("./nsga3_gen/nsga3_gen"+str(gen)+".png")
        plt.close()
        #======================================================


        # Compile statistics about the new population
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=len(invalid_ind), **record)
        print(logbook.stream)

    return pop, logbook


if __name__ == "__main__":
    try:
        pop, stats = main()
    except KeyboardInterrupt:
        print("Ctrl + Cで停止しました")
        pass

    pop_fit = numpy.array([ind.fitness.values for ind in pop])

    k = 0
    for ind, fit in zip(pop[:10], pop_fit[:10]):
        try:
            k += 1
            datlist_list = [fc.read_datfile(file) for file in datfiles]
            datlist_shaped_list = [fc.shape_dat(datlist) for datlist in datlist_list]
            newdat = fc.interpolate_dat(datlist_shaped_list,decoder(ind,code_division))
            fc.write_datfile(datlist=newdat,newfile_name = "newfoil"+str(k)+str(".dat"))
        except Exception as e:
            print("message:{0}".format(e))
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
    ax = fig.add_subplot(111, projection="3d")

    p = numpy.array([ind.fitness.values for ind in pop])
    ax.scatter(p[:, 0], p[:, 1], p[:, 2], marker="o", s=24, label="Final Population")

    #ax.scatter(pf[:, 0], pf[:, 1], pf[:, 2], marker="x", c="k", s=32, label="Ideal Pareto Front")

    ref_points = tools.uniform_reference_points(NOBJ, P)

    ax.scatter(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], marker="o", s=24, label="Reference Points")

    ax.view_init(elev=11, azim=-25)
    ax.autoscale(tight=True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("nsga3.png")
