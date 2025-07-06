"""
SQLAdmin 管理界面配置
兼容SQLAdmin 0.21.0版本
"""

from typing import Any
from wtforms import (
    SelectField,
    TextAreaField,
    StringField,
    ValidationError,
)
from wtforms.widgets import PasswordInput
import json

from models.auth_model import InfoStatusTypeEnum


"""
SQLAdmin 管理界面配置
参考官方文档：https://aminalaee.github.io/sqladmin/model_convertors/
"""

from typing import Any
from wtforms import (
    SelectField,
    TextAreaField,
    StringField,
    ValidationError,
)
from wtforms.widgets import PasswordInput
import json

from models.auth_model import InfoStatusTypeEnum


# JSON字段格式化函数
def format_json_column(data: Any, max_length: int = 100) -> str:
    """格式化JSON数据用于列表显示"""
    if data is None:
        return "无"

    try:
        if isinstance(data, dict):
            # 如果是字典，显示键的数量
            keys = list(data.keys())
            if len(keys) <= 3:
                key_str = ", ".join(f'"{k}"' for k in keys)
                return f"{{{key_str}}}"
            else:
                key_str = ", ".join(f'"{k}"' for k in keys[:2])
                return f"{{{key_str}, ...}} ({len(keys)}个字段)"
        elif isinstance(data, list):
            return f"[数组] ({len(data)}个元素)"
        else:
            # 转换为JSON字符串并截断
            json_str = json.dumps(data, ensure_ascii=False)
            if len(json_str) > max_length:
                return json_str[:max_length] + "..."
            return json_str
    except Exception:
        return (
            str(data)[:max_length] + "..." if len(str(data)) > max_length else str(data)
        )


def format_json_detail(data: Any) -> str:
    """格式化JSON数据用于详情显示"""
    if data is None:
        return "无"

    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        return str(data)


# 自定义JSON字段（参考官方Model Convertors文档）
class CustomJSONField(TextAreaField):
    """自定义JSON字段，支持友好显示和验证"""

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            try:
                # 尝试解析JSON
                if valuelist[0].strip():
                    parsed_data = json.loads(valuelist[0])
                    self.data = parsed_data
                else:
                    self.data = None
            except (json.JSONDecodeError, ValueError) as e:
                # 如果不是有效的JSON，保存原始数据并添加验证错误
                self.data = valuelist[0]
                raise ValidationError(f"无效的JSON格式: {str(e)}")
        else:
            self.data = None

    def _value(self):
        if self.data is not None:
            if isinstance(self.data, str):
                # 如果是字符串，直接返回（可能是验证失败的情况）
                return self.data
            return json.dumps(self.data, ensure_ascii=False, indent=2)
        return ""

    def __call__(self, **kwargs):
        kwargs.setdefault("rows", 8)
        kwargs.setdefault("class_", "form-control json-field")
        kwargs.setdefault(
            "placeholder",
            '请输入有效的JSON格式数据，例如：\n{\n  "key": "value",\n  "number": 123\n}',
        )
        return super().__call__(**kwargs)


# 自定义密码字段
class CustomPasswordField(StringField):
    """自定义密码字段，支持空值不修改现有密码"""

    widget = PasswordInput(hide_value=True)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = valuelist[0]
        else:
            self.data = None

    def __call__(self, **kwargs):
        kwargs.setdefault("class_", "form-control")
        kwargs.setdefault("placeholder", "输入新密码（留空保持现有密码不变）")
        return super().__call__(**kwargs)


# 信息状态选择字段
class InfoStatusSelectField(SelectField):
    """信息状态选择字段"""

    def __init__(self, *args, **kwargs):
        choices = [
            (InfoStatusTypeEnum.PUBLIC.value, "公开"),
            (InfoStatusTypeEnum.PRIVATE.value, "私有"),
        ]
        kwargs["choices"] = choices
        kwargs["coerce"] = int
        super().__init__(*args, **kwargs)
