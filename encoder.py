"""
ロータリエンコーダ読み取りモジュール

【概要】
ロータリエンコーダの回転方向と回転量を検出します。
CLK（A相）とDT（B相）の位相差を利用して回転方向を判定します。

【仕様】
- CLK (A相): GP4
- DT (B相): GP1
- 検出方式: クロックエッジ検出
- プッシュボタン: KeyMatrixモジュールで検出（key_num=17）

【使用例】
    from encoder import RotaryEncoder
    
    encoder = RotaryEncoder()
    
    while True:
        delta = encoder.get_delta()
        
        if delta > 0:
            print(f"時計回り: {delta}")
        elif delta < 0:
            print(f"反時計回り: {delta}")
        
        time.sleep(0.01)

【回転検出原理】
CLKがHigh→Lowに変化した時にDTの状態を確認：
  - DTがHigh → 時計回り（+1）
  - DTがLow  → 反時計回り（-1）

【加速度対応】
高速回転時は、値の変化量を大きくすることで、
パラメータ調整を効率的に行えます（オプション）。
"""

import board
import digitalio
import time


class RotaryEncoder:
    """
    ロータリエンコーダクラス
    
    Attributes:
        clk (DigitalInOut): CLK（A相）ピン
        dt (DigitalInOut): DT（B相）ピン
        position (int): エンコーダの累積位置
        last_clk_state (bool): CLKの前回の状態
        acceleration_enabled (bool): 加速度機能の有効/無効
        last_rotation_time (float): 最後に回転を検出した時刻
    """
    
    # ピン定義
    CLK_PIN = board.GP4  # A相
    DT_PIN = board.GP1   # B相
    
    # 加速度設定
    ACCELERATION_THRESHOLD = 0.05  # 50ms以内の回転で加速開始
    ACCELERATION_MULTIPLIER = 2     # 加速時の倍率
    
    def __init__(self, acceleration_enabled=False):
        """
        ロータリエンコーダの初期化
        
        Args:
            acceleration_enabled (bool): 加速度機能を有効にする場合True
        """
        # CLKピンの初期化（入力、プルアップ）
        self.clk = digitalio.DigitalInOut(self.CLK_PIN)
        self.clk.direction = digitalio.Direction.INPUT
        self.clk.pull = digitalio.Pull.UP
        
        # DTピンの初期化（入力、プルアップ）
        self.dt = digitalio.DigitalInOut(self.DT_PIN)
        self.dt.direction = digitalio.Direction.INPUT
        self.dt.pull = digitalio.Pull.UP
        
        # 状態の初期化
        self.position = 0
        self.last_clk_state = self.clk.value
        self.acceleration_enabled = acceleration_enabled
        self.last_rotation_time = 0.0
        
        print("[RotaryEncoder] 初期化完了")
        print(f"  - CLKピン: GP4")
        print(f"  - DTピン: GP1")
        print(f"  - 加速度: {'有効' if acceleration_enabled else '無効'}")
    
    def update(self):
        """
        エンコーダの状態を更新
        
        CLKピンの状態変化を検出し、回転方向を判定します。
        このメソッドは定期的に呼び出す必要があります。
        
        Returns:
            int: 回転量（時計回り=正、反時計回り=負、変化なし=0）
        """
        current_clk = self.clk.value
        delta = 0
        
        # CLKがHigh→Lowに変化した場合
        if self.last_clk_state and not current_clk:
            current_time = time.monotonic()
            
            # DTの状態で回転方向を判定
            if self.dt.value:
                # DTがHigh → 時計回り
                delta = 1
                self.position += 1
            else:
                # DTがLow → 反時計回り
                delta = -1
                self.position -= 1
            
            # 加速度処理
            if self.acceleration_enabled:
                time_since_last = current_time - self.last_rotation_time
                
                # 高速回転の場合、変化量を増やす
                if time_since_last < self.ACCELERATION_THRESHOLD:
                    delta *= self.ACCELERATION_MULTIPLIER
            
            self.last_rotation_time = current_time
        
        # CLKの状態を更新
        self.last_clk_state = current_clk
        
        return delta
    
    def get_delta(self):
        """
        前回の呼び出しからの回転量を取得
        
        update()を呼び出して、回転量を返します。
        
        Returns:
            int: 回転量（時計回り=正、反時計回り=負、変化なし=0）
        """
        return self.update()
    
    def get_position(self):
        """
        エンコーダの累積位置を取得
        
        Returns:
            int: 累積位置（初期位置を0として、回転に応じて増減）
        """
        return self.position
    
    def reset_position(self):
        """
        エンコーダの累積位置をリセット
        
        位置を0に戻します。
        """
        self.position = 0
    
    def set_position(self, position):
        """
        エンコーダの累積位置を設定
        
        Args:
            position (int): 設定する位置
        """
        self.position = position
    
    def enable_acceleration(self, enabled=True):
        """
        加速度機能の有効/無効を設定
        
        Args:
            enabled (bool): 有効にする場合True
        """
        self.acceleration_enabled = enabled
        print(f"[RotaryEncoder] 加速度: {'有効' if enabled else '無効'}")
    
    def deinit(self):
        """
        ロータリエンコーダの終了処理
        
        すべてのピンを解放します。
        """
        self.clk.deinit()
        self.dt.deinit()
        print("[RotaryEncoder] 終了処理完了")


class EncoderWithValue:
    """
    値を持つエンコーダクラス（MIDI CC用）
    
    ロータリエンコーダの回転を、0-127の範囲の値に変換します。
    MIDI CCの制御に最適です。
    
    Attributes:
        encoder (RotaryEncoder): ロータリエンコーダインスタンス
        value (int): 現在の値（0-127）
        min_value (int): 最小値
        max_value (int): 最大値
    """
    
    def __init__(self, initial_value=64, min_value=0, max_value=127, acceleration_enabled=False):
        """
        値付きエンコーダの初期化
        
        Args:
            initial_value (int): 初期値（デフォルト=64）
            min_value (int): 最小値（デフォルト=0）
            max_value (int): 最大値（デフォルト=127）
            acceleration_enabled (bool): 加速度機能を有効にする場合True
        """
        self.encoder = RotaryEncoder(acceleration_enabled)
        self.value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        
        print(f"[EncoderWithValue] 初期化完了 (値: {initial_value}, 範囲: {min_value}-{max_value})")
    
    def update(self):
        """
        エンコーダを更新して値を変更
        
        Returns:
            int: 前回からの値の変化量（変化なし=0）
        """
        delta = self.encoder.get_delta()
        
        if delta != 0:
            # 値を更新（範囲制限あり）
            old_value = self.value
            self.value = max(self.min_value, min(self.max_value, self.value + delta))
            
            # 実際の変化量を返す
            return self.value - old_value
        
        return 0
    
    def get_value(self):
        """
        現在の値を取得
        
        Returns:
            int: 現在の値（min_value～max_value）
        """
        return self.value
    
    def set_value(self, value):
        """
        値を設定
        
        Args:
            value (int): 設定する値（範囲外の場合はクリッピング）
        """
        self.value = max(self.min_value, min(self.max_value, value))
    
    def set_range(self, min_value, max_value):
        """
        値の範囲を設定
        
        Args:
            min_value (int): 最小値
            max_value (int): 最大値
        """
        self.min_value = min_value
        self.max_value = max_value
        # 現在の値が範囲外の場合はクリッピング
        self.value = max(self.min_value, min(self.max_value, self.value))
    
    def enable_acceleration(self, enabled=True):
        """
        加速度機能の有効/無効を設定
        
        Args:
            enabled (bool): 有効にする場合True
        """
        self.encoder.enable_acceleration(enabled)
    
    def deinit(self):
        """
        終了処理
        """
        self.encoder.deinit()
        print("[EncoderWithValue] 終了処理完了")


