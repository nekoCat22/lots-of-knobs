"""
Lots of Knobs - 完全統合テストプログラム

【概要】
すべてのハードウェアモジュールを統合した最終動作確認プログラム。
実際のMIDIコントローラとして動作します。

【統合モジュール】
1. キーマトリックス（17キー + エンコーダSW）
2. ロータリエンコーダ
3. LED制御（WS2812C × 16個）
4. MIDI出力（TRS MIDI OUT）
5. OLEDディスプレイ（128×64、90度回転）

【機能】
- キーを押す → MIDI Note On + LED点灯 + ディスプレイ更新
- キーを押しながらエンコーダ → MIDI CC送信 + LED色変化 + ディスプレイ更新
- 複数キー同時押し対応
- OLED画面でリアルタイム情報表示

【設定】
- MIDIチャンネル: 1
- Note範囲: C4(60) - D#5(75)
- CC範囲: CC#1 - CC#16
"""

import time
from key_matrix import KeyMatrix
from encoder import EncoderWithValue
from led_control import LEDController
from midi_output import MIDIOutput, MIDINote
from display import Display

print("=" * 70)
print("Lots of Knobs - 完全統合テスト")
print("=" * 70)
print()

# ===== 初期化 =====

print("【初期化開始】")
print()

# ディスプレイの初期化（最初に初期化して起動画面を表示）
print("1/5: ディスプレイ初期化中...")
display = Display(rotation=90)
display.show_startup()
print("✓ 完了")
print()

# キーマトリックスの初期化
print("2/5: キーマトリックス初期化中...")
matrix = KeyMatrix()
print("✓ 完了")
print()

# エンコーダの初期化
print("3/5: ロータリエンコーダ初期化中...")
encoder = EncoderWithValue(initial_value=64, acceleration_enabled=False)
print("✓ 完了")
print()

# LED制御の初期化
print("4/5: LED制御初期化中...")
leds = LEDController(brightness=0.3)
print("✓ 完了")
print()

# MIDI出力の初期化
print("5/5: MIDI出力初期化中...")
midi = MIDIOutput(default_channel=1)
midi_note = MIDINote(midi)
print("✓ 完了")
print()

# 起動アニメーション
print("起動アニメーション実行中...")
display.show_message("Initializing\nLEDs...", duration=0.5)
leds.rainbow_cycle(duration=1.5)
leds.clear()
print("✓ 完了")
print()

# ===== 設定 =====

# レイヤー設定（Phase 2で実装予定、今回は固定）
current_layer = 1
layer_name = "Default"

# 各キーに対応するMIDI Note番号
KEY_TO_NOTE = list(range(60, 76))  # C4-D#5

# 各キーに対応するMIDI CC番号
KEY_TO_CC = list(range(1, 17))  # CC#1-16

# 各キーに対応するパラメータ名（例）
KEY_PARAM_NAMES = [
    "Cutoff", "Reso", "Attack", "Decay",
    "Release", "LFO Rt", "LFO Amt", "Drive",
    "Reverb", "Delay", "Chorus", "Pan",
    "Volume", "Filter", "Pitch", "Mod"
]

# 各キーのCC値
key_cc_values = [64] * 16

# MIDIチャンネル
midi_channel = 1

# 初期LEDの設定
for i in range(16):
    leds.set_key_value(i, key_cc_values[i])
leds.show()

# 初期ディスプレイ表示
display.show_message("Ready!", duration=1)
display.show_layer(current_layer, layer_name)

print("=" * 70)
print("テスト開始！")
print("=" * 70)
print()
print("【操作方法】")
print("・キーを押す → MIDI Note On + LED点灯")
print("・キー押下中にエンコーダ → MIDI CC送信 + LED色変化")
print("・複数キー同時押し対応")
print("・OLED画面でリアルタイム表示")
print()
print("Ctrl+C で終了")
print()

# ===== メインループ =====

prev_pressed_keys = []
last_display_update = 0
DISPLAY_UPDATE_INTERVAL = 0.1  # ディスプレイ更新間隔（秒）

try:
    while True:
        current_time = time.monotonic()
        
        # キーマトリックスをスキャン
        matrix.scan()
        
        # エンコーダを更新
        encoder_delta = encoder.update()
        
        # 現在押されているキーを取得
        all_pressed = matrix.get_pressed_keys()
        pressed_keys = [k for k in all_pressed if k < 16]
        
        # キーの押下状態変化を検出
        newly_pressed = [k for k in pressed_keys if k not in prev_pressed_keys]
        newly_released = [k for k in prev_pressed_keys if k not in pressed_keys]
        
        # 新しく押されたキー → Note On
        for key_num in newly_pressed:
            note = KEY_TO_NOTE[key_num]
            midi_note.play(note, velocity=100, channel=midi_channel)
            
            # LED白フラッシュ
            leds.set_key_color(key_num, (255, 255, 255))
            leds.show()
            time.sleep(0.03)
            leds.set_key_value(key_num, key_cc_values[key_num])
            leds.show()
            
            # ディスプレイ更新
            display.show_full_status(
                current_layer,
                layer_name,
                KEY_PARAM_NAMES[key_num],
                key_cc_values[key_num],
                KEY_TO_CC[key_num],
                midi_channel
            )
            
            print(f"[{current_time:.2f}] key{key_num} → Note On: {note}")
        
        # 離されたキー → Note Off
        for key_num in newly_released:
            note = KEY_TO_NOTE[key_num]
            midi_note.stop(note, channel=midi_channel)
            
            print(f"[{current_time:.2f}] key{key_num} → Note Off: {note}")
        
        # キーが離されて何も押されていない → レイヤー画面に戻る
        if not pressed_keys and prev_pressed_keys:
            if current_time - last_display_update > DISPLAY_UPDATE_INTERVAL:
                display.show_layer(current_layer, layer_name)
                last_display_update = current_time
        
        # エンコーダ回転
        if encoder_delta != 0 and pressed_keys:
            direction = "↻" if encoder_delta > 0 else "↺"
            
            print(f"\n[{current_time:.2f}] エンコーダ {direction} (Δ{encoder_delta:+d})")
            
            for key_num in pressed_keys:
                # CC値更新
                old_val = key_cc_values[key_num]
                key_cc_values[key_num] = max(0, min(127, key_cc_values[key_num] + encoder_delta))
                new_val = key_cc_values[key_num]
                
                # 値が変化した場合
                if new_val != old_val:
                    # MIDI CC送信
                    cc_num = KEY_TO_CC[key_num]
                    midi.control_change(cc_num, new_val, channel=midi_channel)
                    
                    # LED更新
                    leds.set_key_value(key_num, new_val)
                    
                    # ディスプレイ更新（最初のキーのみ）
                    if key_num == pressed_keys[0]:
                        display.show_full_status(
                            current_layer,
                            layer_name,
                            KEY_PARAM_NAMES[key_num],
                            new_val,
                            cc_num,
                            midi_channel
                        )
                    
                    print(f"  key{key_num}: CC#{cc_num} = {old_val} → {new_val} ({KEY_PARAM_NAMES[key_num]})")
            
            # LED反映
            leds.show()
            print()
        
        # 状態保存
        prev_pressed_keys = pressed_keys.copy()
        
        # ウェイト
        time.sleep(0.01)

except KeyboardInterrupt:
    print()
    print("=" * 70)
    print("テスト終了")
    print("=" * 70)
    print()
    
    # 終了画面
    display.show_message("Shutting\ndown...")
    
    # すべてのNote Off
    midi_note.stop_all(channel=midi_channel)
    
    # LED終了アニメーション
    for i in range(3):
        leds.set_brightness(0.05)
        time.sleep(0.15)
        leds.set_brightness(0.3)
        time.sleep(0.15)
    
    # クリーンアップ
    print("\n終了処理中...")
    leds.clear()
    matrix.deinit()
    encoder.deinit()
    leds.deinit()
    midi.deinit()
    display.deinit()
    
    print()
    print("=" * 70)
    print("Phase 1 完了！")
    print("=" * 70)
    print()
    print("【完成した機能】")
    print("✓ キーマトリックススキャン")
    print("✓ ロータリエンコーダ読み取り")
    print("✓ LED制御（蛇行配線対応）")
    print("✓ MIDI OUT送信（Note/CC）")
    print("✓ OLEDディスプレイ表示")
    print()
    print("次はPhase 2: コア機能実装にゃ！")
    print("・レイヤー機能")
    print("・モード切替（CC/Note）")
    print("・設定メニュー")
    print()
