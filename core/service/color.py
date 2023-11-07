import enum
import math


class Color:
    GREEN = "#6aa84f"
    RED = "#ef6f6f"
    YELLOW = "#fdff82"

    @staticmethod
    def to_hex(value: int) -> str:
        assert value >= 0
        assert value <= 255
        return hex(value)[2:].rjust(2, '0')


class XLSXColor(Color):
    class GradientType(enum.Enum):
        LINEAR = 0
        LOG2 = 1

    @classmethod
    def count_gradient(
            cls,
            bottom: int,
            top: int,
            gradient_bottom: int,
            gradient_top: int,
            gradient_type: "XLSXColor.GradientType",
            value: int
    ) -> int:
        if value < bottom:
            value = bottom
        if value > top:
            value = top
        k = (gradient_top - gradient_bottom) / (top - bottom)

        if gradient_type == cls.GradientType.LINEAR:
            gradient = int(k * (value - bottom) + gradient_bottom)
        elif gradient_type == cls.GradientType.LOG2:
            gradient = int(math.log2((value - bottom) * k) * 32 + gradient_bottom)
        else:
            raise ValueError(f"Unknown gradient type: {gradient_type}.")

        if gradient < gradient_bottom:
            gradient = gradient_bottom
        if gradient > gradient_top:
            gradient = gradient_top
        return gradient

    @classmethod
    def gradient_green(
            cls,
            bottom: int,
            top: int,
            gradient_bottom: int,
            gradient_top: int,
            gradient_type: "XLSXColor.GradientType",
            value: int
    ) -> str:
        gradient = cls.count_gradient(bottom, top, gradient_bottom, gradient_top, gradient_type, value)
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
    def gradient_red(
            cls,
            bottom: int,
            top: int,
            gradient_bottom: int,
            gradient_top: int,
            gradient_type: "XLSXColor.GradientType",
            value: int
    ) -> str:
        gradient = cls.count_gradient(bottom, top, gradient_bottom, gradient_top, gradient_type, value)
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
