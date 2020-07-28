# 動作環境
```
python 3.6.8
gfortran 環境変数パス追加済み
gcc 環境変数パス追加済み
```
# 使用モジュール
```
cycler==0.10.0
deap==1.3.1
kiwisolver==1.2.0
matplotlib==3.3.0
numpy==1.19.1
Pillow==7.2.0
pyparsing==2.4.7
python-dateutil==2.8.1
six==1.15.0
xfoil==0.0.16
```
# セットアップ
## 手順1
(http://mingw-w64.org/doku.php/download)から端末に対応するmingwインストーラーをダウンロード。

ここでは、Windows10に[MingW-W64-builds](http://mingw-w64.org/doku.php/download/mingw-builds)をダウンロードした。

## 手順2
インストーラーを起動し、誘導に従ってダウンロード。

ここでは、
```
Version : 8.1.0
Architecture : x86_64
Threads : posix
Exception : seh
Build : revision 0
```
とした。

## 手順3
ダウンロードしたディレクトリ内にあるgfortran.exeとgcc.exeが入ったディレクトリを環境変数のPATHに登録する。

# 概要
翼型を最適化するプログラム。最適化のアルゴリズムには、NSGA3という遺伝的アルゴリズムの一種を用いている。翼型の生成を以下2種類の方法で行った。
- 既存翼型を混合する
- 3次スプライン曲線で結ぶ

次の章でそれぞれの説明をする。
