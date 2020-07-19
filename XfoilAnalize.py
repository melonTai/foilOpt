import numpy as np
import subprocess
import os

class XfoilAnalize():
    """
    xfoilを呼び出すことで、翼型を解析するクラス。
    コンストラクタにて、解析オプションを受け取り、解析結果をメソッドの戻り値とtxtファイルで返す。


    Attributes
    ----------
    Re : float, default 150000.0
        解析するレイノルズ数領域
    alpha : float, default 2.0
        解析する迎角[deg]
    cl : float, default 0.5
        解析する揚力係数
    aseq : list of float, default [0.0, 8.0, 1.0]
        複数点で解析する場合の迎角[deg]
        aseq[0]...始端迎角
        aseq[1]...終端迎角
        aseq[2]...解析の刻み幅
        defaultの場合、0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0の9点で解析が実行される。
    cseq :  list of float, default [0.5, 1.2, 0.1]
        複数点で解析する場合の揚力係数
        aseq[0]...始端揚力係数
        aseq[1]...終端揚力係数
        aseq[2]...解析の刻み幅
        defaultの場合、0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2の8点で解析が実行される。
    foilfile : string, default "DAE-51.dat"
        解析する翼型のdatファイル
    polar : string, default "polar.txt"
        解析結果を示すテキストファイルの名前

    """
    def __init__(self,Re=150000.0,alpha=2.0,cl=0.5,aseq = [0.0,8.0,1.0],cseq = [0.5,1.2,0.1],\
                 foilfile="DAE-51.dat",polar = "polar.txt"):

        self.Re = Re
        self.alpha = alpha
        self.cl = cl
        self.aseq = aseq
        self.cseq = cseq
        self.foilfile = foilfile
        self.polar = polar


    def _CallXfoil(self,pipe,timeout=7):
        flag = True#エラー時にフラグを立てる
        #---xfoilの呼び出し---
        ps = subprocess.Popen(['xfoil.exe'],
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        try:
            res = ps.communicate(pipe, timeout=timeout)
            #print(res)
        #発散などによってxfoilが無限ループに陥った際の対応
        #タイムアウトによって実現している
        except subprocess.TimeoutExpired:
            res = None
            ps.kill()
            mt = None
            mc = None
            tat = None
            cat = None
            flag = False

        return flag


    def OneAlpha(self):
        """
        コンストラクタで指定された迎角alphaにおける翼型解析を行う

        Returns
        ----------
        Cl : float
            alphaにおける揚力係数
        Cd : float
            alphaにおける抗力係数
        Lr : float
            alphaにおける揚抗比
        """

        pipe = bytes(
        "plop\ng\n\nnorm\nload {load}\noper\nvisc {Re}\n pacc\n{filename}\n\niter 60\nalfa {alpha1}\n" \
        .format(load=self.foilfile, Re=self.Re, filename=self.polar, alpha1=self.alpha), "ascii")
        res = self._CallXfoil(pipe)
        flag = res

        if flag:
            #polarファイルから翼型の性能を読み取る
            lines = np.loadtxt(self.polar, skiprows=12)
            if len(lines) == 0:
                Cl = None
                Cd = None
                Lr = None
            else:
                if len(lines.shape) == 2:
                    lines = lines[-1]
                Cl = lines[1]
                Cd = lines[2]
                Lr = lines[1] / lines[2]
                print("success")
                print(self.polar)

        else:
            Cl = None
            Cd = None
            Lr = None
        try:
            os.remove(self.polar)
        finally:
            return {"Cl":Cl,"Cd":Cd,"Lr":Lr}

    def OneCL(self):
        """
        コンストラクタで指定された揚力係数clにおける翼型解析を行う

        Returns
        ----------
        Alpha : float
            clにおける迎角
        Cl : float
            clにおける揚力係数
        Cd : float
            clにおける抗力係数
        Lr : float
            clにおける揚抗比
        """

        pipe = bytes(
        "plop\ng\n\nnorm\nload {load}\ngdes\ncadd\n\n\n\ndero\nunit\n\noper\nvisc {Re}\n pacc\n\n\niter 60\ncl {cl1}\npwrt\n{filename}\ny\n" \
        .format(load=self.foilfile, Re=self.Re, filename= self.polar, cl1=self.cl), "ascii")
        res = self._CallXfoil(pipe)
        flag = res

        if flag:
            #polarファイルから翼型の性能を読み取る
            lines = np.loadtxt(self.polar, skiprows=12)
            if len(lines) == 0:
                Alpha = None
                Cl = None
                Cd = None
                Lr = None
            else:
                if len(lines.shape) == 2:
                    lines = lines[-1]
                Alpha = lines[0]
                Cl = lines[1]
                Cd = lines[2]
                Lr = lines[1]/lines[2]

        else:
            Alpha = None
            Cl = None
            Cd = None
            Lr = None
        try:
            os.remove(self.polar)
        finally:
            return {"Alpha":Alpha,"Cl":Cl,"Cd":Cd,"Lr":Lr}

    def Aseq(self,timeout=12):
        """
        コンストラクタで指定された複数の迎角における翼型解析を行う

        Parameters
        ----------
        timeout : int, default 12
            xfoil起動のタイムアウト秒数

        Returns : dict {<string>:<list of float>, <string>:<list of float>, <string>:<list of float>}
        ----------

        "Cllist":Cllist
            複数の迎角における揚力係数
        "Cdlist":Cdlist
            複数の迎角における抗力係数
        "Lrlist":Lrlist
            複数の迎角における揚抗比
        """
        pipe = bytes(
        "plop\ng\n\nnorm\nload {load}\ngdes\ncadd\n\n\n\ndero\nunit\n\noper\nvisc {Re}\n pacc\n{filename}\n\niter 40\naseq {start} {end} {step}\n" \
        .format(load=self.foilfile, Re=self.Re, filename=self.polar, start=self.aseq[0], end=self.aseq[1],step = self.aseq[2]), "ascii")
        res = self._CallXfoil(pipe,timeout=timeout)
        flag = res

        if flag:
            #polarファイルから翼型の性能を読み取る
            lines = np.loadtxt(self.polar, skiprows=12)

            if len(lines.shape) == 2:
                Cllist = [temp[1] for temp in lines]
                Cdlist = [temp[2] for temp in lines]
                Lrlist = [temp[1]/temp[2] for temp in lines]
            if len(lines) == 0:
                Cllist = None
                Cdlist = None
                Lrlist = None

        else:
            Cllist = None
            Cdlist = None
            Lrlist = None

        try:
            os.remove(self.polar)
        finally:
            return {"Cllist":Cllist,"Cdlist":Cdlist,"Lrlist":Lrlist}

    def Cseq(self,timeout=12):
        """
        コンストラクタで指定された複数の揚力係数における翼型解析を行う

        Parameters
        ----------
        timeout : int, default 12
            xfoil起動のタイムアウト秒数

        Returns : dict {<string>:<list of float>, <string>:<list of float>, <string>:<list of float>}
        ----------

        "Cllist":Cllist
            複数の揚力係数における揚力係数
        "Cdlist":Cdlist
            複数の揚力係数における抗力係数
        "Lrlist":Lrlist
            複数の揚力係数における揚抗比
        """
        pipe = bytes(
        "plop\ng\n\nnorm\nload {load}\ngdes\ncadd\n\n\n\ndero\nunit\n\noper\nvisc {Re}\npacc\n{filename}\n\niter 40\ncseq {start} {end} {step}\n" \
        .format(load=self.foilfile, Re=self.Re, filename=self.polar, start=self.cseq[0], end=self.cseq[1],step = self.cseq[2]), "ascii")
        res = self._CallXfoil(pipe,timeout=timeout)
        flag = res

        if flag:
            #polarファイルから翼型の性能を読み取る
            lines = np.loadtxt(self.polar, skiprows=12)
            if len(lines) == 0:
                Cllist = None
                Cdlist = None
                Lrlist = None
            else:
                # print("success")
                Cllist = [temp[1] for temp in lines]
                Cdlist = [temp[2] for temp in lines]
                Lrlist = [temp[1] / temp[2] for temp in lines]

        else:
            Cllist = None
            Cdlist = None
            Lrlist = None
        try:
            os.remove(self.polar)
        finally:
            return {"Cllist":Cllist,"Cdlist":Cdlist,"Lrlist":Lrlist}


if __name__ == '__main__':
    from main_xfapi import decoder
    import os
    import foilConductor as fc


    analize = XfoilAnalize(foilfile = 'foils/AG24.dat')
    analize.alpha = 3.0
    data = analize.OneAlpha()

    print(data["Cd"])
