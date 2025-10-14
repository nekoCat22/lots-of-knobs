"""
LED制御モジュール（WS2812C-2020）

【概要】
16個のWS2812C-2020 LEDを制御します。
蛇行配線に対応したマッピングにより、キー番号から適切なLEDを
制御できます。MIDI CC値（0-127）を色と明るさで視覚的に表現します。

【仕様】
- LED数: 16個（key0-15に対応）
- データピン: GP6（BSS138経由で5Vに変換）
- LED配線: 蛇行カスケード接続
- 表現方法: 色相（Hue）+ 明るさ（Value）でCC値を表現

【蛇行配線マッピング】
キースイッチ物理配置:
  key0   key1   key2   key3    (ROW0)
  key4   key5   key6   key7    (ROW1)
  key8   key9   key10  key11   (ROW2)
  key12  key13  key14  key15   (ROW3)

LEDデータライン順序（GP6から）:
  LED3   LED2   LED1   LED0    ← (右から左)
  LED4   LED5   LED6   LED7    → (左から右)
  LED11  LED10  LED9   LED8    ← (右から左)
  LED12  LED13  LED14  LED15   → (左から右)

【使用例】
    from led_control import LEDController
    
    leds = LEDController()
    
    # key0のLEDを赤色に設定
    leds.set_key_color(0, (255, 0, 0))
    
    # key5のLEDをCC値に応じた色に設定
    leds.set_key_value(5, 100)  # CC値100
    
    # 全LEDを消灯
    leds.clear()
"""

import board
import neopixel
import time


class LEDController:
    """
    LED制御クラス
    
    Attributes:
        pixels (neopixel.NeoPixel): NeoPixelオブジェクト
        num_leds (int): LED数
        key_to_led_map (list): キー番号からLED番号へのマッピング
        brightness (float): 全体の明るさ（0.0-1.0）
    """
    
    # ピン定義
    LED_PIN = board.GP6
    
    # LED数
    NUM_LEDS = 16
    
    # キー番号からLED番号へのマッピング
    # KEY_TO_LED[key_num] = led_index
    KEY_TO_LED = [
        3,   # key0  → LED3
        2,   # key1  → LED2
        1,   # key2  → LED1
        0,   # key3  → LED0
        4,   # key4  → LED4
        5,   # key5  → LED5
        6,   # key6  → LED6
        7,   # key7  → LED7
        11,  # key8  → LED11
        10,  # key9  → LED10
        9,   # key10 → LED9
        8,   # key11 → LED8
        12,  # key12 → LED12
        13,  # key13 → LED13
        14,  # key14 → LED14
        15   # key15 → LED15
    ]
    
    # 色相マッピング（CC値 0-127 → Hue 0-360）
    # 青(240) → シアン(180) → 緑(120) → 黄(60) → 赤(0)
    HUE_MIN = 240  # 低い値: 青
    HUE_MAX = 0    # 高い値: 赤
    
    def __init__(self, brightness=0.3):
        """
        LED制御の初期化
        
        Args:
            brightness (float): 全体の明るさ（0.0-1.0、デフォルト=0.3）
        """
        # NeoPixelの初期化
        self.pixels = neopixel.NeoPixel(
            self.LED_PIN,
            self.NUM_LEDS,
            brightness=brightness,
            auto_write=False,  # 手動で更新
            pixel_order=neopixel.GRB  # WS2812Cの色順
        )
        
        self.num_leds = self.NUM_LEDS
        self.brightness = brightness
        
        # 初期化: 全消灯
        self.clear()
        
        print("[LEDController] 初期化完了")
        print(f"  - LED数: {self.num_leds}個")
        print(f"  - データピン: GP6")
        print(f"  - 明るさ: {brightness * 100:.0f}%")
    
    def set_led_color(self, led_index, color):
        """
        指定したLEDインデックスに色を設定
        
        Args:
            led_index (int): LEDインデックス（0-15）
            color (tuple): RGB色 (R, G, B) 各0-255
        """
        if 0 <= led_index < self.num_leds:
            self.pixels[led_index] = color
    
    def set_key_color(self, key_num, color):
        """
        指定したキー番号に対応するLEDに色を設定
        
        Args:
            key_num (int): キー番号（0-15）
            color (tuple): RGB色 (R, G, B) 各0-255
        """
        if 0 <= key_num < len(self.KEY_TO_LED):
            led_index = self.KEY_TO_LED[key_num]
            self.set_led_color(led_index, color)
    
    def set_key_value(self, key_num, value):
        """
        指定したキーのLEDをMIDI CC値に応じた色に設定
        
        値が低い（0に近い）→ 青
        値が高い（127に近い）→ 赤
        
        Args:
            key_num (int): キー番号（0-15）
            value (int): MIDI CC値（0-127）
        """
        if 0 <= key_num < len(self.KEY_TO_LED):
            # CC値を0-127から0-1に正規化
            normalized = value / 127.0
            
            # 色相を計算（青→赤）
            hue = self.HUE_MIN - (self.HUE_MIN - self.HUE_MAX) * normalized
            
            # 明るさを計算（値が高いほど明るく）
            brightness = 0.3 + (0.7 * normalized)  # 30%-100%
            
            # HSVからRGBに変換
            rgb = self._hsv_to_rgb(hue, 1.0, brightness)
            
            # LEDに設定
            self.set_key_color(key_num, rgb)
    
    def set_all_value(self, value):
        """
        全LEDを同じMIDI CC値に設定
        
        Args:
            value (int): MIDI CC値（0-127）
        """
        for key_num in range(16):
            self.set_key_value(key_num, value)
    
    def clear(self):
        """
        全LEDを消灯
        """
        self.pixels.fill((0, 0, 0))
        self.show()
    
    def show(self):
        """
        LEDの状態を反映（実際に点灯）
        
        set_xxx()メソッドで設定した後、このメソッドを呼ぶことで
        実際にLEDが点灯します。
        """
        self.pixels.show()
    
    def set_brightness(self, brightness):
        """
        全体の明るさを設定
        
        Args:
            brightness (float): 明るさ（0.0-1.0）
        """
        self.brightness = max(0.0, min(1.0, brightness))
        self.pixels.brightness = self.brightness
        self.show()
    
    def rainbow_cycle(self, duration=2.0):
        """
        レインボーアニメーション（起動時のテストなどに使用）
        
        Args:
            duration (float): アニメーションの継続時間（秒）
        """
        steps = 50
        step_time = duration / steps
        
        for i in range(steps):
            for led_index in range(self.num_leds):
                hue = (360 / self.num_leds * led_index + i * 7) % 360
                rgb = self._hsv_to_rgb(hue, 1.0, 0.5)
                self.set_led_color(led_index, rgb)
            self.show()
            time.sleep(step_time)
    
    def test_mapping(self):
        """
        マッピングテスト: 各キーを順番に点灯
        
        蛇行配線のマッピングが正しいか確認するためのテスト。
        key0から順番に赤く点灯します。
        """
        print("[LEDController] マッピングテスト開始")
        
        for key_num in range(16):
            self.clear()
            self.set_key_color(key_num, (255, 0, 0))  # 赤
            self.show()
            print(f"  key{key_num} → LED{self.KEY_TO_LED[key_num]} 点灯")
            time.sleep(0.5)
        
        self.clear()
        print("[LEDController] マッピングテスト完了")
    
    def _hsv_to_rgb(self, h, s, v):
        """
        HSVからRGBに変換
        
        Args:
            h (float): 色相 Hue（0-360）
            s (float): 彩度 Saturation（0.0-1.0）
            v (float): 明度 Value（0.0-1.0）
        
        Returns:
            tuple: RGB色 (R, G, B) 各0-255
        """
        # 色相を0-1に正規化
        h = h / 360.0
        
        if s == 0.0:
            # 彩度が0 → グレースケール
            val = int(v * 255)
            return (val, val, val)
        
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def deinit(self):
        """
        LED制御の終了処理
        
        全LEDを消灯してリソースを解放します。
        """
        self.clear()
        self.pixels.deinit()
        print("[LEDController] 終了処理完了")


