# 概要
翼型を最適化するプログラム。

最適化のアルゴリズムには、NSGA3という遺伝的アルゴリズムの一種を用いている。

翼型の生成を以下2種類の方法で行った。
- 既存翼型を混合する
- 3次スプライン曲線で結ぶ

# 動作環境
```
python 3.6.8
gfortran 環境変数にパス追加済み
gcc 環境変数にパス追加済み
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
このレポジトリをダウンロードする

## 手順2
gfortranやgccをインストール済みの人は手順2~4不要

http://mingw-w64.org/doku.php/download
から端末に対応するmingwインストーラーをダウンロード。

ここでは、Windows10に[MingW-W64-builds](http://mingw-w64.org/doku.php/download/mingw-builds)をダウンロードした。

## 手順3
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

![mingw-setting](https://user-images.githubusercontent.com/60560614/88699448-5017b880-d142-11ea-813d-2b837d12cb95.png)

## 手順4
ダウンロードしたディレクトリ内にあるgfortran.exeとgcc.exeが入ったディレクトリ(今回はmingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin)の絶対パスを環境変数のPATHに登録する。

以下windows10に環境変数を登録する例

![env_path](https://user-images.githubusercontent.com/60560614/88700974-6161c480-d144-11ea-8017-57a5e8f7379a.png)

windows内の検索機能で「環境変数」と検索し、「システム環境変数の編集」をクリック

![env_path2](https://user-images.githubusercontent.com/60560614/88700978-63c41e80-d144-11ea-8027-7e08511a33b5.png)

「環境変数」をクリック

![env_path3](https://user-images.githubusercontent.com/60560614/88700982-66267880-d144-11ea-99cf-92e296f60ed1.png)

ユーザ環境変数のPATHを選択し、「編集」をクリック

![env_path4](https://user-images.githubusercontent.com/60560614/88700990-67f03c00-d144-11ea-8f54-cddb45443fce.png)

右上の「新規」をクリックし、gfortran.exeとgcc.exeが入ったディレクトリの絶対パスを入力し、「OK」クリック

## 手順5
gccとgfortranが環境変数のPATHに正しく登録されたか確認する。

gccは
```
gcc -v
```
gfortranは
```
gfortran -v
```
とコマンドプロンプトに入力し、バージョン情報が出力されれば、PATHの登録に成功している。

## 手順6
必要なpythonモジュールをインストールする。

なおインストールはpythonバージョン3.6で行う。

python3.6のインストールが済んでいない場合は
https://www.python.org/downloads/
からインストールする。

モジュールのインストールは以下のコマンドで可能
```
py -3.6 -m pip install -r requirements.txt
```
なおrequirements.txtはこのレポジトリのルートディレクトリに同封

また、ダウンロード済みのライブラリとの衝突によって動作が不安定な場合、
仮想環境下でモジュールをインストールするとよい。
特に、xfoilモジュールの最新バージョンは動作が不安定なため、
最新バージョンをダウンロード済みの場合は、
仮想環境下で過去バージョンを使用することを推奨する。

例としては、
```
py -3.6 -m venv [ダウンロードしたレポジトリのパス]
cd [ダウンロードしたレポジトリのパス]
Scripts\activate
pip install -r requirements.txt
```
これによって、上に示した環境下での運用が可能。

また、以下のコマンドで仮想環境を抜けられる。
```
Scripts\deactivate
```
以降は、
```
cd [ダウンロードしたレポジトリのパス]
Scripts\activate
```
のみで同じ仮想環境を構築可能

# 使用方法
## nsga3_mixfoil.pyについて
基本的に__init__関数内パラメータを書き換え、もしくは追加して使用する
### 最も簡単な使い方
以下の変数を書き換える
- self.datfiles
  混合する翼型のdatファイルパスをリストにして代入
- self.re
  最適化を行うレイノルズ数を代入
## nsga3_spline.pyについて
準備中
