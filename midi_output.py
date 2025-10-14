"""
MIDI出力モジュール（USB MIDI版 - ライブラリ不要）

【概要】
USB MIDI経由でMIDIメッセージを送信します。
PCやDAWに直接接続して使用できます。
追加ライブラリ不要で、CircuitPython標準機能のみで動作します。

【仕様】
- 出力: USB MIDI（RP2040内蔵USB）
- プロトコル: MIDI 1.0
- 対応メッセージ: Note On/Off, Control Change, Program Change
- ドライバ: 不要（クラスコンプライアント）
- 必要なもの: CircuitPython標準の usb_midi のみ

【使用例】
    from midi_output import MIDIOutput
    
    midi = MIDIOutput()
    
    # Note On (Ch1, C4=60, velocity=100)
    midi.note_on(60, 100, channel=1)
    
    # Note Off
    midi.note_off(60, channel=1)
    
    # Control Change (Ch1, CC#1, value=64)
    midi.control_change(1, 64, channel=1)

【MIDIメッセージフォーマット】
Note On:        0x9n nn vv  (n=channel-1, nn=note, vv=velocity)
Note Off:       0x8n nn vv
Control Change: 0xBn cc vv  (cc=controller#, vv=value)
Program Change: 0xCn pp     (pp=program#)
"""

import usb_midi


class MIDIOutput:
    """
    MIDI出力クラス（USB MIDI版、追加ライブラリ不要）
    
    Attributes:
        midi_out (usb_midi.PortOut): USB MIDI出力ポート
        default_channel (int): デフォルトMIDIチャンネル（1-16）
    """
    
    # MIDIメッセージタイプ
    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    
    def __init__(self, default_channel=1):
        """
        MIDI出力の初期化
        
        Args:
            default_channel (int): デフォルトMIDIチャンネル（1-16、デフォルト=1）
        """
        # USB MIDI出力ポートの取得
        self.midi_out = usb_midi.ports[1]  # ポート1が出力
        
        self.default_channel = self._validate_channel(default_channel)
        
        print("[MIDIOutput] 初期化完了（USB MIDI）")
        print(f"  - 出力: USB MIDI")
        print(f"  - デフォルトチャンネル: {self.default_channel}")
    
    def note_on(self, note, velocity=100, channel=None):
        """
        Note Onメッセージを送信
        
        Args:
            note (int): ノート番号（0-127、C4=60）
            velocity (int): ベロシティ（0-127、デフォルト=100）
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        ch = self._get_channel(channel)
        note = self._validate_value(note, 0, 127)
        velocity = self._validate_value(velocity, 0, 127)
        
        status = self.NOTE_ON | (ch - 1)
        self._send_message([status, note, velocity])
    
    def note_off(self, note, velocity=0, channel=None):
        """
        Note Offメッセージを送信
        
        Args:
            note (int): ノート番号（0-127）
            velocity (int): リリースベロシティ（0-127、デフォルト=0）
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        ch = self._get_channel(channel)
        note = self._validate_value(note, 0, 127)
        velocity = self._validate_value(velocity, 0, 127)
        
        status = self.NOTE_OFF | (ch - 1)
        self._send_message([status, note, velocity])
    
    def control_change(self, cc_number, value, channel=None):
        """
        Control Changeメッセージを送信
        
        Args:
            cc_number (int): CCナンバー（0-127）
            value (int): CC値（0-127）
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        ch = self._get_channel(channel)
        cc_number = self._validate_value(cc_number, 0, 127)
        value = self._validate_value(value, 0, 127)
        
        status = self.CONTROL_CHANGE | (ch - 1)
        self._send_message([status, cc_number, value])
    
    def program_change(self, program, channel=None):
        """
        Program Changeメッセージを送信
        
        Args:
            program (int): プログラム番号（0-127）
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        ch = self._get_channel(channel)
        program = self._validate_value(program, 0, 127)
        
        status = self.PROGRAM_CHANGE | (ch - 1)
        self._send_message([status, program])
    
    def all_notes_off(self, channel=None):
        """
        All Notes Off（CC#123）を送信
        
        Args:
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        self.control_change(123, 0, channel)
    
    def set_default_channel(self, channel):
        """
        デフォルトMIDIチャンネルを設定
        
        Args:
            channel (int): MIDIチャンネル（1-16）
        """
        self.default_channel = self._validate_channel(channel)
        print(f"[MIDIOutput] デフォルトチャンネル: {self.default_channel}")
    
    def _send_message(self, message):
        """
        MIDIメッセージを送信（内部用）
        
        Args:
            message (list): 送信するMIDIメッセージ（バイトのリスト）
        """
        self.midi_out.write(bytes(message))
    
    def _get_channel(self, channel):
        """
        チャンネルを取得（内部用）
        
        Args:
            channel (int or None): チャンネル番号（Noneの場合はデフォルト）
        
        Returns:
            int: 有効なチャンネル番号（1-16）
        """
        if channel is None:
            return self.default_channel
        return self._validate_channel(channel)
    
    def _validate_channel(self, channel):
        """
        チャンネル番号を検証（内部用）
        
        Args:
            channel (int): チャンネル番号
        
        Returns:
            int: 有効なチャンネル番号（1-16）
        """
        return max(1, min(16, channel))
    
    def _validate_value(self, value, min_val, max_val):
        """
        値を検証・クリッピング（内部用）
        
        Args:
            value (int): 値
            min_val (int): 最小値
            max_val (int): 最大値
        
        Returns:
            int: クリッピングされた値
        """
        return max(min_val, min(max_val, value))
    
    def deinit(self):
        """
        MIDI出力の終了処理
        
        All Notes Offを送信します。
        """
        # 全チャンネルのAll Notes Offを送信
        for ch in range(1, 17):
            self.all_notes_off(ch)
        
        print("[MIDIOutput] 終了処理完了")


class MIDINote:
    """
    MIDI Note管理クラス
    
    Note On/Offの状態を管理し、重複送信を防ぎます。
    
    Attributes:
        midi (MIDIOutput): MIDIOutputオブジェクト
        active_notes (set): 現在アクティブなノート番号のセット
    """
    
    def __init__(self, midi_output):
        """
        MIDI Note管理の初期化
        
        Args:
            midi_output (MIDIOutput): MIDIOutputオブジェクト
        """
        self.midi = midi_output
        self.active_notes = set()
    
    def play(self, note, velocity=100, channel=None):
        """
        ノートを再生（既に再生中の場合は何もしない）
        
        Args:
            note (int): ノート番号（0-127）
            velocity (int): ベロシティ（0-127、デフォルト=100）
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        if note not in self.active_notes:
            self.midi.note_on(note, velocity, channel)
            self.active_notes.add(note)
    
    def stop(self, note, channel=None):
        """
        ノートを停止（既に停止中の場合は何もしない）
        
        Args:
            note (int): ノート番号（0-127）
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        if note in self.active_notes:
            self.midi.note_off(note, 0, channel)
            self.active_notes.discard(note)
    
    def stop_all(self, channel=None):
        """
        すべてのアクティブなノートを停止
        
        Args:
            channel (int): MIDIチャンネル（1-16、Noneの場合はデフォルト）
        """
        for note in list(self.active_notes):
            self.midi.note_off(note, 0, channel)
        self.active_notes.clear()
    
    def is_playing(self, note):
        """
        ノートが再生中か確認
        
        Args:
            note (int): ノート番号（0-127）
        
        Returns:
            bool: 再生中の場合True
        """
        return note in self.active_notes
