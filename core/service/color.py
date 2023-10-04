class Color:
    GREEN = "#6aa84f"
    RED = "#ef6f6f"

    @staticmethod
    def to_hex(value: int) -> str:
        assert value >= 0
        assert value <= 255
        return hex(value)[2:].rjust(2, '0')


class XLSXColor(Color):
    @classmethod
    def gradient_green(cls, bottom: int, top: int, value: int) -> str:
        gradient_top = 255
        gradient_bottom = 0
        if value < bottom:
            value = bottom
        if value > top:
            value = top
        gradient = int((gradient_top - gradient_bottom) / (top - bottom) * (value - bottom) + gradient_bottom)
        red = gradient
        green = 255
        blue = gradient
        color = (
            cls.to_hex(red),
            cls.to_hex(green),
            cls.to_hex(blue)
        )
        return f"#{''.join(color)}"

    @classmethod
    def gradient_red(cls, bottom: int, top: int, value: int) -> str:
        gradient_top = 255
        gradient_bottom = 0
        if value < bottom:
            value = bottom
        if value > top:
            value = top
        gradient = int((gradient_top - gradient_bottom) / (top - bottom) * (value - bottom) + gradient_bottom)
        red = 255
        green = gradient
        blue = gradient
        color = (
            cls.to_hex(red),
            cls.to_hex(green),
            cls.to_hex(blue)
        )
        return f"#{''.join(color)}"


class AdminPanelColor(Color):
    pass
