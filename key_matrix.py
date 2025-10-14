"""
キーマトリックススキャンモジュール

【概要】
4行×5列のキーマトリックスをスキャンして、17個のキースイッチ + 
エンコーダスイッチの状態を検出します。チャタリング対策として
デバウンス処理を実装しています。

【仕様】
- マトリックス構成: 4行 × 5列
- 対応キー: key0～key16 + encoder_sw
- デバウンス時間: 20ms（調整可能）
- 同時押し検出: 最大17キー

【使用例】
    from key_matrix import KeyMatrix
    
    matrix = KeyMatrix()
    
    while True:
        matrix.scan()
        
        # キー状態の取得
        if matrix.is_pressed(0):
            print("key0 pressed!")
        
        # 押されたキーのリスト取得
        pressed_keys = matrix.get_pressed_keys()
        print(f"Pressed: {pressed_keys}")
        
        time.sleep(0.01)

【マトリックス配置】
           COL0(GP5)  COL1(GP7)  COL2(GP9)  COL3(GP11)  COL4(GP15)
           ---------------------------------------------------------
ROW0(GP8)  | key0    | key1    | key2    | key3     | encoder_sw |
ROW1(GP10) | key4    | key5    | key6    | key7     | -          |
ROW2(GP14) | key8    | key9    | key10   | key11    | -          |
ROW3(GP26) | key12   | key13   | key14   | key15    | key16      |
"""

import board
import digitalio
import time


class KeyMatrix:
    """
    キーマトリックススキャンクラス
    
    Attributes:
        DEBOUNCE_TIME (float): デバウンス時間（秒）
        rows (list): ROWピンのリスト
        cols (list): COLピンのリスト
        key_states (list): 各キーの現在の状態（True=押下中）
        last_change_time (list): 各キーの最終状態変化時刻
        key_map (list): マトリックス座標からキー番号へのマッピング
    """
    
    # デバウンス時間（秒）
    DEBOUNCE_TIME = 0.02  # 20ms
    
    # ROWピン: 出力モード（スキャン時に1つずつLOWにする）
    ROW_PINS = [board.GP8, board.GP10, board.GP14, board.GP26]
    
    # COLピン: 入力モード（プルアップ）
    COL_PINS = [board.GP5, board.GP7, board.GP9, board.GP11, board.GP15]
    
    # マトリックス座標からキー番号へのマッピング
    # KEY_MAP[row][col] = key_number (None = 未接続)
    KEY_MAP = [
        [0,  1,  2,  3,  17],  # ROW0: key0, 1, 2, 3, encoder_sw(17)
        [4,  5,  6,  7,  None],  # ROW1: key4, 5, 6, 7
        [8,  9,  10, 11, None],  # ROW2: key8, 9, 10, 11
        [12, 13, 14, 15, 16]     # ROW3: key12, 13, 14, 15, 16
    ]
    
    # キー総数（key0-16 + encoder_sw = 18）
    NUM_KEYS = 18
    
    def __init__(self):
        """
        キーマトリックスの初期化
        
        ROWピンを出力（初期状態HIGH）、COLピンを入力（プルアップ）に設定します。
        """
        # ROWピンの初期化（出力、初期状態HIGH）
        self.rows = []
        for pin in self.ROW_PINS:
            row = digitalio.DigitalInOut(pin)
            row.direction = digitalio.Direction.OUTPUT
            row.value = True  # スキャン時以外はHIGH
            self.rows.append(row)
        
        # COLピンの初期化（入力、プルアップ）
        self.cols = []
        for pin in self.COL_PINS:
            col = digitalio.DigitalInOut(pin)
            col.direction = digitalio.Direction.INPUT
            col.pull = digitalio.Pull.UP  # プルアップ抵抗有効
            self.cols.append(col)
        
        # キー状態の初期化
        self.key_states = [False] * self.NUM_KEYS  # 全キー未押下
        self.last_change_time = [0.0] * self.NUM_KEYS  # 最終変化時刻
        
        print("[KeyMatrix] 初期化完了")
        print(f"  - ROWピン: {len(self.rows)}本")
        print(f"  - COLピン: {len(self.cols)}本")
        print(f"  - キー数: {self.NUM_KEYS}個")
    
    def scan(self):
        """
        キーマトリックスをスキャンして状態を更新
        
        各ROWを順番にLOWにし、COLの状態を読み取ることでキー押下を検出します。
        デバウンス処理により、チャタリングを防ぎます。
        """
        current_time = time.monotonic()
        
        # 各ROWをスキャン
        for row_index, row in enumerate(self.rows):
            # 現在のROWをLOWに設定（他はHIGH）
            row.value = False
            
            # わずかに待機（信号安定化のため）
            time.sleep(0.0001)  # 100μs
            
            # 各COLの状態を読み取り
            for col_index, col in enumerate(self.cols):
                # キー番号を取得
                key_num = self.KEY_MAP[row_index][col_index]
                
                # 未接続の場合はスキップ
                if key_num is None:
                    continue
                
                # COLがLOW → キーが押されている
                is_pressed = not col.value
                
                # デバウンス処理
                time_since_change = current_time - self.last_change_time[key_num]
                
                # 状態が変化し、デバウンス時間が経過している場合のみ更新
                if is_pressed != self.key_states[key_num] and time_since_change > self.DEBOUNCE_TIME:
                    self.key_states[key_num] = is_pressed
                    self.last_change_time[key_num] = current_time
            
            # ROWをHIGHに戻す
            row.value = True
    
    def is_pressed(self, key_num):
        """
        指定したキーが押されているか確認
        
        Args:
            key_num (int): キー番号（0-16: key0-16, 17: encoder_sw）
        
        Returns:
            bool: 押されている場合True、それ以外False
        """
        if 0 <= key_num < self.NUM_KEYS:
            return self.key_states[key_num]
        return False
    
    def get_pressed_keys(self):
        """
        現在押されているキーのリストを取得
        
        Returns:
            list: 押されているキー番号のリスト（例: [0, 5, 12]）
        """
        return [i for i in range(self.NUM_KEYS) if self.key_states[i]]
    
    def get_key_count(self):
        """
        現在押されているキーの数を取得
        
        Returns:
            int: 押されているキーの数
        """
        return sum(self.key_states)
    
    def is_encoder_sw_pressed(self):
        """
        エンコーダスイッチが押されているか確認
        
        Returns:
            bool: 押されている場合True、それ以外False
        """
        return self.is_pressed(17)
    
    def get_key_name(self, key_num):
        """
        キー番号から名前を取得（デバッグ用）
        
        Args:
            key_num (int): キー番号（0-17）
        
        Returns:
            str: キー名（例: "key0", "key16", "encoder_sw"）
        """
        if key_num == 17:
            return "encoder_sw"
        elif 0 <= key_num <= 16:
            return f"key{key_num}"
        else:
            return "unknown"
    
    def deinit(self):
        """
        キーマトリックスの終了処理
        
        すべてのピンを解放します。
        """
        for row in self.rows:
            row.deinit()
        for col in self.cols:
            col.deinit()
        print("[KeyMatrix] 終了処理完了")


