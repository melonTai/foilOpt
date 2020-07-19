# 翼型最適化プログラム
## 各ファイルの説明

### foilConductor.py
主に翼型ファイルの操作する関数群
- 翼型読み取り、書き出し
- 翼型のx座標を揃える
- 翼型の混合
- spline曲線による翼型生成
- etc...

### XfoilAnalize.py
翼型解析ソフトxfoilを使用し、解析結果を取得するクラス
昨日は以下の4つ
- 揚力係数を元に計算する
- 迎角を元に計算する
- 複数の揚力係数をまとめて計算する
- 複数の迎角をまとめて計算する

### const.py
定数を保存するファイル

### main_mixfoil.py
アルゴリズムNSGA3を用いて、翼型を最適化するファイル。
翼型の既存翼型の混合によって生成し、その混合比を最適化する
このファイルから実行できる。

ライブラリ(xfoil)の仕様で以下環境が必要
https://pypi.org/project/xfoil/
- gfortran
- gcc
- python3.6


### nsga3_mixfoil.py
main_mixfoil.pyをクラス化したもの

### nsga3_spline.py
アルゴリズムNSGA3を用いて、翼型を最適化するファイル。
翼型を8つの点を結んだスプライン曲線によって生成し、その8つの点を最適化する。
このファイルから実行できる。

ライブラリ(xfoil)の仕様で以下環境が必要
https://pypi.org/project/xfoil/
- gfortran
- gcc
- python3.6

### GUI_main.py
開発中GUIのmainwindow

### Dialogs.py
開発中GUIのダイアログ

### Ui_module
GUI_main.pyやDialogs.pyで使用するUiデザインをまとめたフォルダ
