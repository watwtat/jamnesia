# Jamnesia - 技術仕様書（新人引き継ぎ用）

## プロジェクト概要

Jamnesia は、ポーカーハンドの入力・保存・リプレイ機能を提供するWebアプリケーションです。Flask + HTMX で構築され、PHH（Poker Hand History）形式でのハンド記録管理を行います。

**主要機能:**
- Webフォームによるポーカーハンドの入力
- PHH形式でのハンド記録生成
- SQLiteデータベースでの正規化されたデータ保存
- ステップバイステップのハンドリプレイ機能
- 複数のサンプルハンドパターン

## システムアーキテクチャ

### 技術スタック
- **バックエンド**: Python 3.11+, Flask 2.3.3, SQLAlchemy 3.0.5
- **フロントエンド**: HTMX 1.9.10, Tailwind CSS 2.2.19
- **データベース**: SQLite（本番環境ではPostgreSQL対応可能）
- **デプロイ**: Docker + Gunicorn, Render対応
- **テスト**: Python unittest, Coverage

### アーキテクチャ図
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (HTMX/CSS)    │◄──►│   (Flask)       │◄──►│   (SQLite)      │
│                 │    │                 │    │                 │
│ - index.html    │    │ - app.py        │    │ - hands         │
│ - input.html    │    │ - models.py     │    │ - players       │
│ - hand_*.html   │    │ - poker_engine  │    │ - actions       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ファイル構成とファイル別詳細実装

### コアファイル

#### `app.py` (1,349行) - メインアプリケーション
**機能**: Flask WebアプリケーションのメインファイルでAPIエンドポイントとロジックを定義

**重要な実装詳細:**
- **Line 11-34**: `get_poker_positions()` - プレイヤー数に応じた適切なポーカーポジション（SB, BB, UTG, CO, BTN等）を返す
- **Line 37-178**: `process_hand_actions()` - ハンドアクションの処理とストリート進行の自動管理
  - プレイヤースタック追跡
  - ベッティングラウンド完了の判定
  - ストリート自動進行（preflop → flop → turn → river）
- **Line 181-203**: `should_advance_street()` - ベッティングラウンド完了判定ロジック
- **Line 246-374**: `/api/save-hand` エンドポイント - ハンド保存のメイン処理
- **Line 376-861**: `get_sample_hand_patterns()` - 5種類のサンプルハンドパターン定義
  - standard: 3プレイヤー標準ハンド
  - heads_up: ヘッズアップバトル
  - all_in: オールインショーダウン
  - bluff_fold: ブラフと フォールド
  - multi_street: 4ストリート アクション
- **Line 1009-1075**: `/api/hands/<play_id>` - 特定ハンドの詳細取得
- **Line 1120-1343**: `/api/hands/<play_id>/replay` - ハンドリプレイデータ生成
  - ステップバイステップの状態管理
  - プレイヤースタック、ポットサイズ、ボードカードの追跡
  - アクション実行時の状態更新

#### `models.py` (98行) - データベースモデル
**機能**: SQLAlchemy ORM モデル定義

**詳細実装:**
- **Line 9-29**: `Position` IntEnum - ポーカーポジションの列挙型（SB=0, BB=1, UTG=2...BTN=8）
- **Line 31-57**: `Hand` モデル - ハンドの基本情報
  - `play_id`: ユニークハンドID（UUID）
  - `phh_content`: 生成されたPHH形式コンテンツ
  - リレーション: players, actions との1対多関係
- **Line 59-73**: `Player` モデル - プレイヤー情報
  - `hole_cards`: "AsKh" 形式のホールカード
  - `position`: ポジション文字列（"SB", "BB", "UTG"等）
- **Line 75-98**: `Action` モデル - アクション詳細
  - `street`: ベッティングラウンド（preflop, flop, turn, river）
  - `action_type`: アクションタイプ（fold, call, bet, raise, check）
  - `pot_size`: アクション後のポットサイズ
  - `remaining_stack`: アクション後の残りスタック
  - `action_order`: アクション順序

#### `poker_engine.py` (188行) - ポーカーエンジン
**機能**: PHH生成とハンドビルディング

**詳細実装:**
- **Line 6-28**: `PokerHandBuilder` クラス初期化
- **Line 29-31**: `deal_hole_cards()` - ホールカード配布
- **Line 33-41**: `add_action()` - アクション追加（プレイヤー名、アクションタイプ、金額）
- **Line 43-56**: フロップ/ターン/リバー カード配布メソッド
- **Line 58-134**: `generate_phh()` - PHH（Poker Hand History）形式生成
  - プレイヤー数に応じたブラインド配列生成
  - スターティングスタック配列
  - ホールカード配布記録（`d dh p{i} {cards}`）
  - ボードカード配布記録（`d db {cards}`）
  - プレイヤーアクション記録（`p{i} f`, `p{i} cc`, `p{i} cbr {amount}`）

### フロントエンドファイル

#### `templates/base.html` (86行) - ベーステンプレート
**機能**: 全ページ共通のHTMLベース

**重要な実装:**
- **Line 7**: HTMX 1.9.10 スクリプト読み込み
- **Line 8**: Tailwind CSS 2.2.19 読み込み
- **Line 9-15**: カスタムCSSクラス定義（.card, .btn, .btn-primary等）
- **Line 33-52**: ハンド詳細表示用モーダルダイアログ
- **Line 56-84**: HTMXイベントハンドラ
  - エラーハンドリング（htmx:responseError）
  - リプレイコンテンツ読み込み後の初期化（htmx:afterSwap）

#### `templates/index.html` (143行) - メインページ
**機能**: アプリケーションのホームページ

**詳細実装:**
- **Line 11-24**: メイン機能ボタンとサンプルパターン選択UI
- **Line 29-40**: 保存済みハンド一覧表示（HTMX による動的読み込み）
- **Line 44-84**: `loadSamplePatterns()` - サンプルパターンの動的読み込み
- **Line 86-141**: `createSampleHand()` - サンプルハンド作成処理

### 設定・デプロイファイル

#### `requirements.txt` (3行) - 本番依存関係
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
gunicorn==21.2.0
```

#### `Dockerfile` (50行) - コンテナ設定
**重要な実装:**
- **Line 2**: Python 3.11-slim ベースイメージ
- **Line 8-11**: 本番環境変数設定
- **Line 32-37**: セキュリティ向上のための非rootユーザー作成
- **Line 49-50**: Gunicorn設定（1ワーカー、SQLite互換性）

#### `Makefile` (61行) - 開発コマンド
**主要コマンド:**
- `make dev-install`: 開発依存関係インストール
- `make test`: 全テスト実行
- `make coverage`: カバレッジレポート生成
- `make run`: 開発サーバー起動

## データベース設計

### ERダイアグラム
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     hands       │    │    players      │    │    actions      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │◄──┐│ id (PK)         │    │ id (PK)         │
│ play_id (UNIQUE)│   └┤ hand_id (FK)    │    │ hand_id (FK)    │◄─┐
│ game_type       │    │ name            │    │ street          │  │
│ board           │    │ stack           │    │ player_name     │  │
│ small_blind     │    │ hole_cards      │    │ action_type     │  │
│ big_blind       │    │ position        │    │ amount          │  │
│ phh_content     │    └─────────────────┘    │ pot_size        │  │
│ created_at      │                           │ remaining_stack │  │
└─────────────────┘                           │ action_order    │  │
                                              └─────────────────┘──┘
```

### テーブル詳細

#### `hands` テーブル
- **主キー**: `id` (自動増分)
- **ユニークキー**: `play_id` (UUID文字列)
- **インデックス**: `created_at` (時系列検索用)

#### `players` テーブル  
- **外部キー**: `hand_id` → `hands.id`
- **制約**: `name` NOT NULL, `stack` NOT NULL
- **形式**: `hole_cards` は "AsKh" 形式

#### `actions` テーブル
- **外部キー**: `hand_id` → `hands.id`
- **制約**: `action_order` で順序保証
- **列挙値**: `street` は preflop/flop/turn/river
- **列挙値**: `action_type` は fold/call/bet/raise/check

## API設計

### RESTful エンドポイント

#### ハンド管理
- `POST /api/save-hand` - 新しいハンド保存
- `GET /api/hands` - ハンド一覧取得（JSON/HTML）
- `GET /api/hands/{play_id}` - 特定ハンド詳細
- `GET /api/hands/{play_id}/details` - ハンド詳細HTML
- `GET /api/hands/{play_id}/replay` - リプレイデータ
- `GET /api/hands/{play_id}/replay-ui` - リプレイUI HTML

#### サンプル機能
- `GET /api/sample-patterns` - 利用可能パターン一覧
- `POST /api/create-sample` - サンプルハンド作成

#### ユーティリティ
- `GET /api/players/names` - プレイヤー名オートコンプリート

### リクエスト/レスポンス形式

#### POST /api/save-hand
```json
{
  "players": [
    {"name": "Alice", "stack": 100.0},
    {"name": "Bob", "stack": 100.0}
  ],
  "actions": [
    {
      "player_name": "Alice",
      "action_type": "bet", 
      "amount": 5.0,
      "pot_size": 7.0,
      "remaining_stack": 95.0
    }
  ],
  "small_blind": 1.0,
  "big_blind": 2.0,
  "hole_cards": {
    "Alice": "AsKh",
    "Bob": "QdQc"
  },
  "flop": "AhKd5c"
}
```

## ビジネスロジック

### ハンド処理アルゴリズム

#### 1. アクション処理フロー (`process_hand_actions`)
```python
# 疑似コード
def process_hand_actions(players, actions, blinds):
    player_stacks = initialize_stacks(players)
    current_pot = post_blinds(players, blinds)
    current_street = "preflop"
    
    for action in actions:
        process_single_action(action, player_stacks, current_pot)
        
        if should_advance_street(active_players, bets):
            advance_to_next_street()
            reset_current_bets()
    
    add_auto_folds(players_without_actions)
    return processed_actions
```

#### 2. ストリート進行判定 (`should_advance_street`)
```python
def should_advance_street(active_players, folded_players, players_acted, bets, current_bet):
    # 1プレイヤーのみ残存 → ハンド終了
    if len(active_players) <= 1:
        return True
    
    # 全アクティブプレイヤーがアクション済みかチェック
    if not active_players.issubset(players_acted):
        return False
    
    # 全プレイヤーのベット額が一致するかチェック
    return all_bets_equal(active_players, bets, current_bet)
```

### リプレイシステム

#### ステップバイステップ状態管理
リプレイシステムは以下の状態を各ステップで追跡します:

1. **プレイヤー状態**
   - `current_stack`: 現在のスタック
   - `current_bet`: 現在のベット額
   - `total_invested`: 累計投資額
   - `is_active`: アクティブ状態
   - `has_folded`: フォールド状態

2. **ゲーム状態**
   - `pot_size`: ポットサイズ
   - `board`: ボードカード配列
   - `current_bet`: 現在のベットレベル
   - `street`: 現在のストリート

3. **特殊ステップ**
   - Step 0: 初期状態
   - Step 1: ブラインド投入
   - 中間ステップ: ストリート移行時

## テスト戦略

### テストカバレッジ（90+テスト）

#### 1. ユニットテスト分類
- **`test_poker_engine.py`** (19テスト): PHH生成、ハンドビルディング
- **`test_models.py`** (14テスト): データベースモデル、リレーション
- **`test_app.py`** (25テスト): APIエンドポイント、ワークフロー
- **`test_position.py`** (15テスト): ポジション処理、バリデーション
- **`test_replay.py`** (13+テスト): リプレイAPI、状態管理

#### 2. テスト実行方法
```bash
# 全テスト実行
make test
python run_tests.py

# カバレッジレポート生成
make coverage
coverage run run_tests.py && coverage html

# 特定テストファイル実行
python -m unittest test_poker_engine.py
```

#### 3. テストデータ管理
- 各テストで独立したtemporary SQLiteデータベース使用
- テスト間でのデータ競合回避
- setUp/tearDownでクリーンな状態保証

## セキュリティ考慮事項

### 1. アプリケーションセキュリティ
- **SQLインジェクション対策**: SQLAlchemy ORM使用
- **XSS対策**: Flaskの自動エスケープ機能
- **CSRF対策**: 本番環境では適切なCSRFトークン実装が必要

### 2. コンテナセキュリティ
- 非rootユーザー（app）でアプリケーション実行
- 最小限のシステム依存関係のみインストール
- ヘルスチェック機能付き

### 3. データベースセキュリティ
- SQLite: ファイルシステムレベルでの権限管理
- PostgreSQL移行時: 接続暗号化、認証管理が必要

## パフォーマンス設計

### 1. データベース最適化
- **インデックス**: `created_at` での時系列検索最適化
- **正規化**: 重複データ削減によるストレージ効率
- **クエリ最適化**: lazy loading によるN+1問題回避

### 2. フロントエンド最適化
- **HTMX**: 部分的DOM更新によるレスポンス向上
- **CDN**: Tailwind CSS, HTMX の CDN 配信利用
- **キャッシュ**: 静的ファイルの適切なキャッシング

### 3. 本番環境設定
- **Gunicorn**: 1ワーカー（SQLite制限）
- **PostgreSQL移行**: 複数ワーカー対応可能
- **タイムアウト**: 120秒設定

## デプロイ・運用

### 1. ローカル開発環境
```bash
# 仮想環境セットアップ
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
make dev-install

# 開発サーバー起動
make run
# または
python app.py
```

### 2. Docker デプロイ
```bash
# イメージビルド
docker build -t jamnesia .

# コンテナ実行
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///data/jamnesia.db" \
  -e SECRET_KEY="your-secret-key" \
  -v $(pwd)/data:/app/data \
  jamnesia
```

### 3. Render デプロイ
- `render.yaml` 設定ファイル使用
- 環境変数: `DATABASE_URL`, `SECRET_KEY`
- 自動ビルド・デプロイパイプライン

### 4. 環境変数
- `DATABASE_URL`: データベース接続文字列
- `SECRET_KEY`: Flaskセッション暗号化キー
- `PORT`: アプリケーションポート（自動設定）

## 拡張・メンテナンス

### 1. 機能拡張ポイント
- **データベース移行**: SQLite → PostgreSQL
- **認証システム**: ユーザー管理、権限制御
- **統計機能**: VPIP, PFR 等の統計算出
- **インポート機能**: 既存PHHファイルの一括インポート
- **エクスポート機能**: 複数形式でのデータエクスポート

### 2. 技術的負債対応
- **TypeScript導入**: フロントエンドの型安全性向上
- **非同期処理**: 大量データ処理の非同期化
- **API バージョニング**: 後方互換性の保証
- **ロギング**: 適切なアプリケーションログ実装

### 3. 監視・アラート
- **アプリケーション監視**: Render内蔵監視機能
- **データベース監視**: 容量、パフォーマンス追跡
- **エラートラッキング**: Sentry等のエラー追跡サービス導入検討

## 開発ガイドライン

### 1. コード規約
- **Python**: PEP 8 準拠
- **命名規則**: スネークケース（Python）、ケバブケース（HTML/CSS）
- **関数長**: 50行以下を目安
- **複雑度**: McCabe複雑度 10以下

### 2. Git フロー
```bash
# 機能ブランチ作成
git checkout -b feature/new-feature

# 変更をコミット
git add .
git commit -m "feat: add new feature"

# テスト実行
make test

# プルリクエスト作成
```

### 3. リリースプロセス
1. 機能開発・テスト
2. コードレビュー
3. 統合テスト
4. ステージング環境デプロイ
5. 本番環境デプロイ
6. 動作確認

## トラブルシューティング

### 1. よくある問題

#### データベース関連
```bash
# データベース初期化
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# データベースリセット
rm jamnesia.db
make run
```

#### 依存関係問題
```bash
# 仮想環境再構築
rm -rf venv
python3 -m venv venv
source venv/bin/activate
make dev-install
```

### 2. ログ確認
```bash
# アプリケーションログ
tail -f app.log

# Dockerログ
docker logs container_name

# Renderログ
# Render ダッシュボード上で確認
```

### 3. パフォーマンス問題
- データベース容量確認
- メモリ使用量監視
- レスポンス時間測定

## まとめ

Jamnesia は、モダンなWebテクノロジーを使用して構築された、拡張性とメンテナンス性を重視したポーカーハンド管理システムです。明確なアーキテクチャ設計、包括的なテストカバレッジ、そして適切なデプロイメント戦略により、安定したサービス提供を実現しています。

新しい開発者がプロジェクトに参加する際は、この技術仕様書を基に、各ファイルの役割と実装詳細を理解し、既存のコード規約とアーキテクチャパターンに従って開発を進めてください。