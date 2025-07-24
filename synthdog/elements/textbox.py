"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np
from synthtiger import layers

class TextBox:
    def __init__(self, config):
        self.fill = config.get("fill", [1, 1])

    def generate(self, size, text, font):
        width, height = size
        fill = np.random.uniform(self.fill[0], self.fill[1])
        width = np.clip(width * fill, height, width)
        
        font_config = {**font, "size": int(height)}

        # Detect if text contains complex script characters (Devanagari, Arabic, etc.)
        def is_complex_script(text_str):
            for char in text_str:
                code = ord(char)
                # Devanagari: U+0900–U+097F, Arabic: U+0600–U+06FF
                if (0x0900 <= code <= 0x097F) or (0x0600 <= code <= 0x06FF):
                    return True
            return False

        # Collect text first, respecting width constraints
        collected_text = ""
        for char in text:
            if char in "\r\n":
                break
            
            test_text = collected_text + char
            try:
                # Test if adding this character would exceed width
                test_layer = layers.TextLayer(test_text, **font_config)
                char_scale = height / test_layer.height if test_layer.height > 0 else 1
                scaled_width = test_layer.width * char_scale
                
                if scaled_width > width:
                    break
                    
                collected_text = test_text
            except Exception as e:
                # If TextLayer fails (common with complex scripts), try simpler approach
                print(f"TextLayer error with '{test_text}': {e}")
                # For complex scripts, be more conservative about width
                if len(collected_text) > 0:
                    break
                # Try to include at least one character
                collected_text = char
                break

        if not collected_text.strip():
            return None, None

        # For complex scripts, render as a single unit to preserve ligatures
        if is_complex_script(collected_text):
            try:
                text_layer = layers.TextLayer(collected_text, **font_config)
                char_scale = height / text_layer.height if text_layer.height > 0 else 1
                text_layer.bbox = [0, 0, *(text_layer.size * char_scale)]
                return text_layer, collected_text.strip()
            except Exception as e:
                print(f"Complex script rendering failed for '{collected_text}': {e}")
                # Fallback to character-by-character for problematic text
                pass
        
        # For simple scripts or fallback, use character-by-character approach
        char_layers, chars = [], []
        left, top = 0, 0
        
        for char in collected_text:
            if char in "\r\n":
                continue
                
            try:
                char_layer = layers.TextLayer(char, **font_config)
                char_scale = height / char_layer.height if char_layer.height > 0 else 1
                char_layer.bbox = [left, top, *(char_layer.size * char_scale)]
                
                char_layers.append(char_layer)
                chars.append(char)
                left = char_layer.right
            except Exception as e:
                print(f"Character rendering failed for '{char}': {e}")
                # Skip problematic characters
                continue

        if not chars:
            return None, None
            
        text_result = "".join(chars).strip()
        text_layer = layers.Group(char_layers).merge()
        
        return text_layer, text_result