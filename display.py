"""
OLEDディスプレイ制御モジュール（フォントファイル不要版）

【概要】
128×64のOLEDディスプレイ（0.96インチ）を90度回転して縦長表示します。
レイヤー情報、パラメータ名、CC値などを表示します。
フォントファイル不要でCircuitPython標準機能のみで動作します。

【仕様】
- 物理解像度: 128×64
- 表示方向: 90度回転（縦長配置）
- 表示領域: 64(幅) × 128(高さ) ピクセル
- 通信: I2C（SDA=GP12, SCL=GP13）
- アドレス: 0x3C または 0x3D（自動検出）
- フォント: CircuitPython組み込みフォント（font5x8.bin不要）

【使用例】
    from display import Display
    
    display = Display()
    
    # レイヤー情報表示
    display.show_layer(1, "Filter")
    
    # パラメータ表示
    display.show_parameter("Cutoff", 80, cc_num=1, channel=1)
    
    # メッセージ表示
    display.show_message("Ready!")
"""

import board
import busio
import adafruit_ssd1306
import time


class Display:
    """
    OLEDディスプレイ制御クラス
    
    Attributes:
        i2c (busio.I2C): I2Cオブジェクト
        oled (adafruit_ssd1306.SSD1306_I2C): OLEDディスプレイオブジェクト
        width (int): 表示幅（回転後）
        height (int): 表示高さ（回転後）
        rotation (int): 回転角度（0, 90, 180, 270）
    """
    
    # I2Cピン
    SDA_PIN = board.GP12
    SCL_PIN = board.GP13
    
    # 物理解像度
    PHYSICAL_WIDTH = 128
    PHYSICAL_HEIGHT = 64
    
    # 表示解像度（90度回転後）
    DISPLAY_WIDTH = 64
    DISPLAY_HEIGHT = 128
    
    def __init__(self, rotation=90):
        """
        ディスプレイの初期化
        
        Args:
            rotation (int): 回転角度（0, 90, 180, 270、デフォルト=90）
        """
        # I2Cの初期化
        self.i2c = busio.I2C(scl=self.SCL_PIN, sda=self.SDA_PIN)
        
        # OLEDの初期化（アドレス自動検出）
        try:
            self.oled = adafruit_ssd1306.SSD1306_I2C(
                self.PHYSICAL_WIDTH,
                self.PHYSICAL_HEIGHT,
                self.i2c,
                addr=0x3C
            )
            print("[Display] OLED初期化成功 (0x3C)")
        except:
            self.oled = adafruit_ssd1306.SSD1306_I2C(
                self.PHYSICAL_WIDTH,
                self.PHYSICAL_HEIGHT,
                self.i2c,
                addr=0x3D
            )
            print("[Display] OLED初期化成功 (0x3D)")
        
        # 回転設定
        self.rotation = rotation
        if rotation == 90 or rotation == 270:
            self.width = self.DISPLAY_WIDTH
            self.height = self.DISPLAY_HEIGHT
        else:
            self.width = self.PHYSICAL_WIDTH
            self.height = self.PHYSICAL_HEIGHT
        
        # コントラスト設定
        self.oled.contrast(200)
        
        # 画面クリア
        self.clear()
        
        print(f"[Display] 初期化完了")
        print(f"  - 物理解像度: {self.PHYSICAL_WIDTH}×{self.PHYSICAL_HEIGHT}")
        print(f"  - 回転: {rotation}度")
        print(f"  - 表示解像度: {self.width}×{self.height}")
    
    def clear(self):
        """
        画面をクリア
        """
        self.oled.fill(0)
        self.oled.show()
    
    def show(self):
        """
        バッファを画面に反映
        """
        self.oled.show()
    
    def pixel(self, x, y, color=1):
        """
        ピクセルを描画（回転考慮）
        
        Args:
            x (int): X座標
            y (int): Y座標
            color (int): 色（0=黒、1=白）
        """
        if self.rotation == 90:
            # 90度回転: (x,y) → (y, width-1-x)
            physical_x = y
            physical_y = self.PHYSICAL_WIDTH - 1 - x
            self.oled.pixel(physical_x, physical_y, color)
        else:
            self.oled.pixel(x, y, color)
    
    def text(self, text, x, y, scale=1):
        """
        テキストを表示（簡易ビットマップフォント、回転非対応）
        
        90度回転時は物理座標系で描画します。
        
        Args:
            text (str): 表示するテキスト
            x (int): X座標（物理座標）
            y (int): Y座標（物理座標）
            scale (int): スケール（1=通常、2=2倍など）
        """
        # adafruit_ssd1306のtextメソッドは物理座標系で動作
        # 90度回転表示の場合も物理座標で指定
        self.oled.text(text, x, y, 1)
    
    def rect(self, x, y, width, height, color=1):
        """
        矩形を描画（回転考慮）
        
        Args:
            x (int): X座標
            y (int): Y座標
            width (int): 幅
            height (int): 高さ
            color (int): 色（0=黒、1=白）
        """
        if self.rotation == 90:
            physical_x = y
            physical_y = self.PHYSICAL_WIDTH - x - width
            self.oled.rect(physical_x, physical_y, height, width, color)
        else:
            self.oled.rect(x, y, width, height, color)
    
    def fill_rect(self, x, y, width, height, color=1):
        """
        塗りつぶし矩形を描画（回転考慮）
        
        Args:
            x (int): X座標
            y (int): Y座標
            width (int): 幅
            height (int): 高さ
            color (int): 色（0=黒、1=白）
        """
        if self.rotation == 90:
            physical_x = y
            physical_y = self.PHYSICAL_WIDTH - x - width
            self.oled.fill_rect(physical_x, physical_y, height, width, color)
        else:
            self.oled.fill_rect(x, y, width, height, color)
    
    def show_layer(self, layer_num, layer_name=""):
        """
        レイヤー情報を表示（90度回転用の簡易レイアウト）
        
        Args:
            layer_num (int): レイヤー番号（1-16）
            layer_name (str): レイヤー名（オプション）
        """
        self.clear()
        
        # 物理座標系で描画（横向き）
        # 実際のデバイスは90度回転して見る
        self.text(f"Layer {layer_num}", 5, 5)
        
        if layer_name:
            self.text(layer_name[:10], 5, 20)
        
        # 区切り線
        self.oled.hline(0, 35, self.PHYSICAL_WIDTH, 1)
        
        self.show()
    
    def show_parameter(self, param_name, value, cc_num=None, channel=1):
        """
        パラメータ情報を表示
        
        Args:
            param_name (str): パラメータ名
            value (int): 値（0-127）
            cc_num (int): CCナンバー（オプション）
            channel (int): MIDIチャンネル（デフォルト=1）
        """
        # CCナンバーとチャンネル
        if cc_num is not None:
            self.text(f"CC#{cc_num} Ch{channel}", 5, 40)
        
        # パラメータ名
        self.text(param_name[:10], 5, 52)
        
        # 区切り線
        self.oled.hline(0, 48, self.PHYSICAL_WIDTH, 1)
        
        self.show()
    
    def show_full_status(self, layer_num, layer_name, param_name, value, cc_num, channel):
        """
        フル情報を表示（レイヤー + パラメータ）
        
        Args:
            layer_num (int): レイヤー番号（1-16）
            layer_name (str): レイヤー名
            param_name (str): パラメータ名
            value (int): 値（0-127）
            cc_num (int): CCナンバー
            channel (int): MIDIチャンネル
        """
        self.clear()
        
        # 物理座標系で描画（横向き）
        # レイヤー情報
        self.text(f"L{layer_num}", 2, 2)
        
        # 区切り線
        self.oled.vline(20, 0, self.PHYSICAL_HEIGHT, 1)
        
        # CCとチャンネル
        self.text(f"CC#{cc_num}", 25, 2)
        self.text(f"Ch{channel}", 25, 12)
        
        # パラメータ名
        self.text(param_name[:8], 25, 25)
        
        # 値の表示
        self.text(f"{value:3d}", 25, 38)
        
        # 値のバー表示
        bar_width = int(90 * (value / 127.0))
        self.oled.rect(25, 50, 90, 10, 1)  # 枠
        if bar_width > 0:
            self.oled.fill_rect(26, 51, bar_width, 8, 1)  # バー
        
        self.show()
    
    def show_message(self, message, duration=None):
        """
        メッセージを表示
        
        Args:
            message (str): メッセージ（改行で複数行可能）
            duration (float): 表示時間（秒、Noneの場合は自動消去しない）
        """
        self.clear()
        
        # メッセージを表示（複数行対応）
        lines = message.split('\n')
        y_start = 10
        
        for i, line in enumerate(lines):
            self.text(line[:16], 5, y_start + i * 12)
        
        self.show()
        
        if duration:
            time.sleep(duration)
    
    def show_startup(self):
        """
        起動画面を表示
        """
        self.clear()
        
        # タイトル（中央寄せ）
        self.text("Lots of", 35, 15)
        self.text("Knobs", 40, 30)
        
        # バージョン
        self.text("v1.0", 48, 50)
        
        self.show()
        time.sleep(1.5)
    
    def test_display(self):
        """
        ディスプレイテスト
        """
        print("[Display] テスト開始")
        
        # 全画面点灯
        self.oled.fill(1)
        self.show()
        print("  - 全画面点灯")
        time.sleep(1)
        
        # 全画面消灯
        self.clear()
        print("  - 全画面消灯")
        time.sleep(0.5)
        
        # テキスト表示
        self.text("Test OK!", 20, 25)
        self.show()
        print("  - テキスト表示")
        time.sleep(1)
        
        # 矩形表示
        self.clear()
        for i in range(4):
            self.oled.rect(i * 10, i * 8, 
                          self.PHYSICAL_WIDTH - i * 20, 
                          self.PHYSICAL_HEIGHT - i * 16, 1)
        self.show()
        print("  - 矩形表示")
        time.sleep(1)
        
        self.clear()
        print("[Display] テスト完了")
    
    def deinit(self):
        """
        ディスプレイの終了処理
        """
        self.clear()
        self.i2c.deinit()
        print("[Display] 終了処理完了")
