import numpy as np
#定数を保存するファイル
import const
from sys import exit
from scipy import interpolate
import random

def read_datfile(datfile_name):
    """
        datファイルを読み込む関数
    """
    #ファイル読み込み
    f=open(datfile_name)
    fd = f.read()
    f.close()
    #最終的な座標データ格納リスト
    #以下のように、n行2列のリストになる
    #[[x,y],.....]
    datlist = []
    #1行ごとに分割
    _datlines = fd.split('\n');
    #空白行削除
    datlines = [i for i in _datlines if i!='']
    #先頭行の翼型名を除き、座標を1行ごとに取得
    for line in datlines[1:]:
        #x座標とy座標を分割
        line = line.split()
        #x座標とy座標を文字列から数値へ
        line[0] = float(line[0])
        line[1] = float(line[1])
        datlist.append(line)
    return datlist


def write_datfile(datlist,newfile_name = 'newfoil.dat'):
    """
        datファイルを書き込む関数
    """
    #ファイル名の.dat拡張子を除いて、翼型名を先頭に書き込む
    output_dat_data = newfile_name[0:-4]+'\n'
    #x座標とy座標を間に空白をおいて1行ずつ書き込む
    for dat in datlist:
        output_dat_data += str(dat[0]) + ' ' + str(dat[1]) + '\n'
    with open(newfile_name, mode='w') as f:
        f.write(output_dat_data)
    return newfile_name


def linear(xs, ys, xn):
    #(x座標、y座標、内分点)
    """
        線形補完する関数(xs昇順)
    """
    if(xn == 0.0 or xn == 1.0):
        #print('end')
        return 0.0
    for i in range(len(xs)-1):
        if(xs[i] < xn and xn < xs[i+1]):
            #線形補完(内分している)
            return ((xs[i+1] - xn) * ys[i] + (xn - xs[i]) * ys[i+1]) / (xs[i+1] - xs[i])
        if(xs[i] == xn):
            return ys[i]
    print('none data')
    return ys[0]


def linear_reverse(xs, ys, xn):
    """
        線形補完する関数(xs降順)
    """
    if(xn == 0.0 or xn == 1.0):
        #print('end')
        return 0.0
    for i in range(len(xs)-1):
        if(xs[i] > xn and xn > xs[i+1]):
            #線形補完(内分している)
            return ((xs[i+1] - xn) * ys[i] + (xn - xs[i]) * ys[i+1]) / (xs[i+1] - xs[i])
        if(xs[i] == xn):
            return ys[i]
    print('none data reverse')
    return ys[0]


def shape_dat(datlist):
    #datlist==[[x,y],....]
    """
        上面と下面のX座標を揃える関数
    """
    datlist_shaped = []
    datlist_x = [dat[0] for dat in datlist]
    datlist_y = [dat[1] for dat in datlist]
    #print(datlist_x)
    for x in const.XDAT_D:

        datlist_shaped.append([x,linear_reverse(datlist_x, datlist_y,x)])
    for x in const.XDAT_U:
        datlist_shaped.append([x,linear(datlist_x, datlist_y,x)])
    #print(newdat)
    return datlist_shaped

def _return_abs(n):
    return abs(n);

def spline_foil(x,y,num = 300):
    """
    受け取った座標を3次b-spline補完する関数

    # argument
        - x
            controll points of x axis
        - y
            controll points of y axis
        - num
            size of return list[0] and list[1]
    # return
        - x
            controll pointsをスプライン補完したときのx座標リスト
        - y
            controll pointsをスプライン補完したときのy座標リスト
    """
    tck,u = interpolate.splprep([x,y], k=3, s=0)
    u = np.linspace(0.0, 1.0,num=num,endpoint=True)
    x, y = interpolate.splev(u,tck)
    return x, y

def beauty(x,y):
    """
    # argument
        - x
            x座標のリスト
        - y
            y座標のリスト
    # return
        下記論文で定義される曲線の歪みエネルギー
        https://ipsj.ixsq.nii.ac.jp/ej/index.php?action=pages_view_main&active_action=repository_action_common_download&item_id=13813&item_no=1&attribute_id=1&file_no=1&page_id=13&block_id=8
        小さいほどなめらか
    """
        yd = [(y[i+1] - y[i])/(x[i+1] - x[i]) for i in range(len(x)-1)]
        ydd = [(yd[i+1] - yd[i])/(x[i+1] - x[i]) for i in range(len(yd)-1)]
        beauty = sum([ydd[i]**2/((1 + yd[i]**2)**2.5)*(x[i + 1] - x[i]) for i in range(len(ydd))])
        return abs(beauty)

def get_foil_para(datlist_shaped):
    """
        翼型の各種パラメータを取得する関数
        翼厚、キャンバ、最大翼厚位置、最大キャンバ位置など

        ※shape_dat()関数で整形した座標を渡すこと※
        # argument
            - datlist_shaped
                座標リスト[[x1,x2,...],[y1,y2,...]]
        # return
            - max_thick(float)
                最大翼厚(百分率)
            - max_thick_at(float)
                最大翼厚位置(百分率)
            - max_camber(float)
                最大キャンバ(百分率)
            - max_camber_at(float)
                最大キャンバ位置(百分率)
            - shape_s(float)
                下面側について
                (y座標最大値) - (y座標最小値)
            - crossed(bool)
                座標が交差していたらTrue
                非交差False
            - beautydat(float)
                beauty([翼型のx座標],[翼型のy座標])
                翼型の滑らかさを示す
                小さいほど滑らか
            - beautythick(float)
                beauty([翼型のx座標後縁から前縁まで(1.0~0.0まで)],[翼厚分布])
                翼厚分布の滑らかさを示す
                小さいほど滑らか
            - beautycamber(float)
                beauty([翼型のx座標後縁から前縁まで(1.0~0.0まで)],[キャンバ分布])
                中心線の滑らかさを示す
                小さいほど滑らか
            - thick_list(float list)
                翼厚分布
    """
    max_thick = 0
    max_thick_at = 0
    max_camber = 0
    max_camber_at = 0
    shape_s = 0
    smooth = 0

    datlist_x = [dat[0] for dat in datlist_shaped]
    datlist_y = [dat[1] for dat in datlist_shaped]

    dat_l = datlist_x.index(0.0)
    dat_t_s = 0
    dat_t_e = len(datlist_x)-1

    datlist_x_u = datlist_x[dat_t_s:dat_l+1]
    datlist_x_d = datlist_x[dat_t_e:dat_l-1:-1]
    datlist_y_u = datlist_y[dat_t_s:dat_l+1]
    datlist_y_d = datlist_y[dat_t_e:dat_l-1:-1]

    thick_list = [abs(yu-yd) for yu,yd in zip(datlist_y_u, datlist_y_d)]
    camber_list = [(yu+yd)/2 for yu,yd in zip(datlist_y_u, datlist_y_d)]

    max_thick = max(thick_list)
    max_thick_at = datlist_x_u[thick_list.index(max_thick)]
    max_camber = max(camber_list,key =_return_abs)
    max_camber_at = datlist_x_u[camber_list.index(max_camber)]
    shape_s = max(datlist_y_d)-min(datlist_y_d)
    crossed = not (all([t < 0 for t in thick_list[1:len(thick_list)-1]]) or all([t > 0 for t in thick_list[1:len(thick_list)-1]]))

    dx = [datlist_x[i+1] - datlist_x[i] for i in range(len(datlist_x)-1)]
    yd = [(datlist_y[i+1]-datlist_y[i]) if int(len(datlist_x)/2) - 1 < i and i < int(len(datlist_x)/2) + 1 else (datlist_y[i+1]-datlist_y[i])/(datlist_x[i+1]-datlist_x[i]) for i in range(len(datlist_y)-1)]
    ydd =[(yd[i+1]-yd[i])/(datlist_x[i+1]-datlist_x[i]) for i in range(len(yd)-1)]
    temp = [ydd[i]**2/((1 + yd[i]**2)**2.5)*(datlist_x[i + 1] - datlist_x[i]) for i in range(len(ydd))]
    beautydat = sum(temp)

    beautythick = beauty(datlist_x_u,thick_list)

    beautycamber = beauty(datlist_x_u, camber_list)

    return max_thick, max_thick_at, max_camber, max_camber_at, shape_s, crossed, beautydat, beautythick, beautycamber, smooth, thick_list

def interpolate_dat(datlist_shaped_list, propotions):
    #(混ぜる翼型datリスト群、各翼型の混ぜる比率リスト)
    """
        dat座標を混合する関数
    """
    if (len(datlist_shaped_list) != len(propotions)):
        print("dat_list uneaqual propotions")
        exit()

    datlist_new_y = [0]*len(datlist_shaped_list[0])
    datlist_new_x = [dat[0] for dat in datlist_shaped_list[0]]
    for datlist_shaped, p in zip(datlist_shaped_list, propotions):
        datlist_new_y = [dat[1]*p + dat_new_y for dat, dat_new_y in zip(datlist_shaped,datlist_new_y)]
    datlist_new = [[dat_new_x,dat_new_y] for dat_new_x, dat_new_y in zip(datlist_new_x, datlist_new_y)]

    return datlist_new


if __name__=='__main__':
    phi = np.linspace(0, 2.*np.pi, 40)
    r = 0.5 + np.cos(phi)         # polar coords
    x, y = r * np.cos(phi), r * np.sin(phi)    # convert to cartesian
    tck, u = interpolate.splprep([x, y], s=0)
    new_points = interpolate.splev(u, tck)
    print(u)
