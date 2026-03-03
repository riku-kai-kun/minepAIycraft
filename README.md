#minepAIycraft
#ver0.4

#minepAIycraftとは、minecraftをpythonで再現しようという試みの一環です
#作成はAIと共同で行います
#なので、AIの機能テストという目的もあります

#実行方法
#ビルド後の物はターミナルから実行しないと動かない場合があります
#まず前提として起動権限を付与してください
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
#ワールド高さは地表y=-1基準で、上方向は最大+64相当、下方向は最大-320相当の範囲に調整しています。
#ブロックは草/土/石の3種で、地下はノイズで洞窟を作ります。

#ver0.4の実装内容
#1) ワールド地形
#- ノイズベースの山地形を追加（地表高さが場所ごとに変化）
#- 海盆地を生成し、水源から水を流して埋める形で海を生成
#- 草ブロック上にランダム雑草（装飾）を自動生成
#
#2) 水システム
#- 水源から周囲へ流れる水流シミュレーションを実装
#- 水源破壊・流路変更時に、段階的に流れが変化する更新方式を採用
#- 水中時の挙動（重力/浮上/移動速度）を追加
#- 水中フォグとオーバーレイ、水テクスチャ描画に対応
#- 水テクスチャ: images/textures/water.png
#
#3) 操作
#- ダッシュを追加
#  - Wキーを素早く2回押す、またはCtrl+Wで開始
#  - Wキーを離すとダッシュ解除
#
#4) 設定画面（ホーム内）
#- 設定項目を拡張
#  - graphics: water_update_interval, water_sim_margin_chunks,
#    mountain_height_scale, tall_grass_spawn_threshold
#  - behavior: dash_speed_multiplier, dash_double_tap_window
#- 項目増加に対応するため、設定画面のスクロール操作（↑↓ / マウスホイール）を追加

#マルチプレイについて
#ver0.4では、ホーム画面のMULTIPLAYERからオンライン参加できます。
#参加方法は「Room Code（6文字）」または「Invite ID（MPC-...）」です。
#接続時にバージョンチェックを行い、不一致の場合は参加できません。
#他プレイヤーは固定スキン（簡易モデル）で表示されます。
#利用者向けサーバー起動キットはserver_kit/にあります。
#server_kit/run_world_server.pyを起動すると、専用ワールドサーバーを起動し、invite idを発行します。
#マルチのスナップショット同期は、山地形破壊(y>=-1)・水源情報(water_sources)に対応しています。
#ネットワーク制限やファイアウォール設定により、マルチ接続が失敗する場合があります。

#github
#ソースコード
#https://github.com/riku-kai-kun/minepAIycraft
#リリース
#https://github.com/riku-kai-kun/minepAIycraft/releases
