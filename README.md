#minepAIycraft

#minepAIycraftとは、minecraftをpythonで再現しようという試みの一環です
#作成はAIと共同で行います
#なので、AIの機能テストという目的もあります

#imagesディレクトリ
#テクスチャ、アイテム、UI用にそれぞれディレクトリがあります

#soundsディレクトリ 
#音楽、効果音用にそれぞれディレクトリがあります

#programsディレクトリ
#index.py以外のプログラムはここに入れます

#コードについて
#実行入口はindex.pyです。pygameでウィンドウと入力を管理し、PyOpenGLで3D描画します。
#programs/ は役割分割されたロジックで、state.pyが定数と共有状態、
#rendering.pyがテクスチャ読み込みと描画、
#world.pyがワールド生成・チャンク管理・衝突判定・レイキャスト、
#controls.pyが操作入力を担当します。
#ブロックは草/土/石の3種で、地表はy=-1、地下はノイズで洞窟を作ります。


#github
#ソースコード
#https://github.com/riku-kai-kun/minepAIycraft
#リリース
#https://github.com/riku-kai-kun/minepAIycraft/releases
