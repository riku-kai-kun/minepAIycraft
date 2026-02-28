#minepAIycraft
#ver0.3

#minepAIycraftとは、minecraftをpythonで再現しようという試みの一環です
#作成はAIと共同で行います
#なので、AIの機能テストという目的もあります

#実行方法
#ビルド後の物はターミナルから実行しないと動かない場合があります
#1.フォルダ「minepAIycraft_macos」を解凍し、中身の、「minepAIycraft」フォルダを、Finderの左側にある自分のユーザーのフォルダに移動させる（🏠マークがあるところ）
#2.アプリケーションの「ターミナル」を開く
#3.「cd minepAIycraft」と入力しEnterキーを押す
#4.「./READMEの実行方法読め.dylib」と入力しEnterキーを押す

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
#ui.pyはホーム画面（NEW/LOAD/SETTINGS/MULTIPLAYER）と各種UI描画を担当します。
#save_system.pyはセーブスロットの作成・保存・読み込み（JSON）を担当します。
#settings_system.pyはsettings.jsonの読み書きと、ゲーム内設定の反映を担当します。
#軽量化設定として、標準ではchunk_radius=4、cave_render_range=12、max_chunk_builds_per_frame=1です。
#ワールド高さは地表y=-1基準で、上方向は最大+64相当、下方向は最大-320相当の範囲に調整しています。
#ブロックは草/土/石の3種で、地表はy=-1、地下はノイズで洞窟を作ります。

#マルチプレイについて
#ver0.3では、ホーム画面のMULTIPLAYERからオンライン参加できます。
#参加方法は「Room Code（6文字）」または「Invite ID（MPC-...）」です。
#接続時にバージョンチェックを行い、不一致の場合は参加できません。
#他プレイヤーは固定スキン（簡易モデル）で表示されます。
#利用者向けサーバー起動キットはserver_kit/にあります。
#server_kit/run_world_server.pyを起動すると、専用ワールドサーバーを起動し、invite idを発行します。
#ネットワーク制限やファイアウォール設定により、マルチ接続が失敗する場合があります。

#github
#ソースコード
#https://github.com/riku-kai-kun/minepAIycraft
#リリース
#https://github.com/riku-kai-kun/minepAIycraft/releases
