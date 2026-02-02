from __future__ import annotations

from abc import ABC
from typing import Self, Any, Callable

from libs.ak_memkit import Address


class CData:
    """
    C語言基本數據類型定義類 (C language basic data type definitions)

    功能: 提供對內存地址的類型化讀取 (Provides typed memory address reading)

    屬性:
        bool: 布爾類型（1字節）(Boolean type, 1 byte)
        i8:   有符號8位整數 (Signed 8-bit integer)
        u8:   無符號8位整數 (Unsigned 8-bit integer)
        i16:  有符號16位整數 (Signed 16-bit integer)
        u16:  無符號16位整數 (Unsigned 16-bit integer)
        i32:  有符號32位整數 (Signed 32-bit integer)
        u32:  無符號32位整數 (Unsigned 32-bit integer)
        i64:  有符號64位整數 (Signed 64-bit integer)
        u64:  無符號64位整數 (Unsigned 64-bit integer)
        f32:  單精度浮點數（32位）(Single-precision floating point, 32-bit)

    嵌套類:
        CPointer: 指針類型讀取器 (Pointer type reader)
        CString: 字符串類型讀取器 (String type reader)
    """
    bool = Address.bool
    i8   = Address.i8
    u8   = Address.u8
    i16  = Address.i16
    u16  = Address.u16
    i32  = Address.i32
    u32  = Address.u32
    i64  = Address.i64
    u64  = Address.u64
    f32  = Address.float

    class CPointer:
        """
        C語言指針類型讀取器 (C language pointer type reader)

        功能:
            - 讀取內存地址中的指針值 (Reads pointer values from memory addresses)
            - 可選使用讀取器函數解析指針指向的數據 (Optionally uses a reader function to parse pointed-to data)

        參數:
            reader: 可選的讀取器函數，用於解析指針指向的數據 (Optional reader function for parsing pointed-to data)

        用法:
            CPointer()  # 僅讀取指針地址 (Reads only the pointer address)
            CPointer(SchemaClassData)  # 讀取指針並解析為CStruct (Reads pointer and parses as CStruct)
            CPointer(CData.CString(128))  # 讀取指針並解析為字符串 (Reads pointer and parses as string)
        """

        def __init__(self, reader: __READER_TYPE | None = None) -> None:
            self.reader = reader

        def __call__(self, address: Address) -> CStruct | Address | None:
            # return self.reader(address.pointer()) if self.reader is not None else address.pointer()
            if self.reader is None:
                return address.pointer()

            address = address.pointer()
            if not address: return address

            return self.reader(address)

    class CString:
        """
        C語言字符串類型讀取器（固定長度）(C language string type reader, fixed length)

        參數:
            size: 字符串的最大長度（包含結尾空字符）(Maximum string length, including null terminator)

        功能:
            - 從內存地址讀取指定長度的字符串 (Reads fixed-length strings from memory addresses)
            - 自動處理C風格字符串的空終止符 (Automatically handles C-style string null terminators)
        """

        def __init__(self, size: int) -> None:
            self.size = size

        def __call__(self, address: Address) -> CStruct | Address:
            return address.str(self.size)


class CField(Address):
    """
    C結構體字段定義類 (C struct field definition class)

    功能: 描述C結構體中的單個字段 (Describes a single field in a C structure)

    特性:
        - 定義字段在結構體中的偏移量 (Defines field offset within structure)
        - 指定字段的數據類型（通過[]運算符）(Specifies field data type via [] operator)
        - 提供類型安全的內存讀取 (Provides type-safe memory reading)
        - 支持類型註冊: CField[數據類型] (Supports type registration: CField[data type])
        - 支持偏移量設置: CField[類型](偏移量) (Supports offset setting: CField[type](offset))
        - 自動轉換為屬性讀取器 (Automatically converts to property reader)

    示例:
        # 定義一個整數字段 (Define an integer field)
        field1 = CField[CData.i32](0x10)

        # 定義一個指針字段 (Define a pointer field)
        field2 = CField[CData.CPointer(SomeStruct)](0x20)

        # 定義一個字符串指針字段 (Define a string pointer field)
        field3 = CField[CData.CPointer(CData.CString(128))](0x30)
    """


    class CFieldReader:
        """
        C字段讀取器工廠類 (C field reader factory class)

        功能:
            - 實現讀取器緩存 (Implements reader caching)
            - 通過__call__方法創建CField實例 (Creates CField instances via __call__ method)

        參數:
            reader: 內存讀取函數或CStruct類型 (Memory reading function or CStruct type)
        """
        _instances = {}

        def __new__(cls, reader: __READER_TYPE) -> Self:
            instance = cls._instances.get(reader, None)
            if instance is None:
                instance = super().__new__(cls)
                instance.__reader = reader
                cls._instances.setdefault(reader, instance)

            return instance

        def __call__(self, offset: int) -> CField:
            instance = CField(offset)
            instance._reader = self.__reader
            return instance

    def __init__(self, offset: int) -> None:
        """
        初始化C字段 (Initializes C field)

        參數:
            offset: 字段在結構體中的偏移量（字節）(Field offset within structure in bytes)
        """
        # super().__init__(address)  # no need :D
        self.offset = offset

    @classmethod
    def __class_getitem__(cls, reader: __READER_TYPE) -> CFieldReader:
        """
        類方法：註冊字段讀取器 (Class method: registers field reader)

        功能:
            - 通過[]運算符註冊字段的數據類型 (Registers field data type via [] operator)
            - 返回CFieldReader實例用於後續設置偏移量 (Returns CFieldReader instance for subsequent offset setting)

        參數:
            reader: 內存讀取函數或CStruct類型 (Memory reading function or CStruct type)

        返回:
            CFieldReader: 字段讀取器工廠實例 (Field reader factory instance)
        """
        return CField.CFieldReader(reader)

    @staticmethod
    def _reader(address: Address):
        """
        默認內存讀取函數 (Default memory reading function)

        注意:
            - 這是用於被子類覆蓋的基礎讀取函數 (This is a base reading function meant to be overridden by subclasses)
            - 默認實現僅返回偏移後的地址 (Default implementation returns offset address only)
            - 實際使用中會被CFieldReader中設置的讀取器覆蓋 (In practice, overridden by reader set in CFieldReader)
        """
        return address

    def read(self, address: Address) -> Address:
        """
        讀取字段數據 (Reads field data)

        功能:
            - 根據字段偏移量和註冊的讀取器讀取數據 (Reads data based on field offset and registered reader)
            - 在CStruct中被轉換為屬性時自動調用 (Automatically called when converted to property in CStruct)

        參數:
            address: 結構體的基地址 (Base address of the structure)

        返回:
            Address: 讀取到的數據（已根據類型解析）(Read data, parsed according to type)
        """
        return self._reader(address.new().offset(self.offset))


class CStruct(ABC):
    """
    C結構體抽象基類 (C struct abstract base class)

    功能: 定義和操作C語言結構體的Python映射 (Python mapping for defining and manipulating C language structures)

    特性:
        - 提供C結構體的Python映射 (Provides Python mapping for C structures)
        - 自動將CField轉換為屬性訪問 (Automatically converts CField to property access)
        - 支持類型安全的內存操作 (Supports type-safe memory operations)
        - 抽象基類，必須被子類化使用 (Abstract base class, must be subclassed)
        - 支持靜態結構體定義（static=True）(Supports static struct definition, static=True)
        - 自動處理字段屬性轉換 (Automatically handles field property conversion)

    用法:
        class MyStruct(CStruct):
            field1 = CField[CData.i32](0x0)
            field2 = CField[CData.CPointer()](0x8)

        # 使用 (Usage)
        instance = MyStruct(0x12345678)
        value = instance.field1  # 自動讀取內存 (Automatically reads memory)
    """

    def __init__(self, address: int | Address) -> None:
        """
        初始化C結構體實例 (Initializes C struct instance)

        參數:
            address: 結構體在內存中的地址 (Memory address of the structure)

        異常:
            ValueError: 當address參數無效時拋出 (Raised when address parameter is invalid)
        """
        self.address = None
        if isinstance(address, int):
            self.address = Address(address)
        elif isinstance(address, Address):
            self.address = address

        if self.address is None:
            raise ValueError()

    def __repr__(self) -> str:
        """返回結構體的字符串表示 (Returns string representation of the structure)"""
        return f"CStruct->{self.__class__.__name__}({self.address})"

    def __init_subclass__(cls, static: bool = False, **kwargs) -> None:
        """
        子類初始化時調用 (Called when subclass is initialized)

        功能:
            - 掃描子類中的所有CField實例 (Scans all CField instances in subclass)
            - 將CField轉換為屬性描述符 (Converts CField to property descriptors)
            - 支持靜態結構體定義 (Supports static struct definition)

        參數:
            static: 是否為靜態結構體（僅定義，不綁定實例）(Whether it's a static struct, definition only, no instance binding)
            **kwargs: 其他關鍵字參數傳遞給父類 (Other keyword arguments passed to parent class)
        """
        super().__init_subclass__(**kwargs)

        for name, value in cls.__dict__.items():
            if not isinstance(value, CField): continue
            setattr(cls, name, CStruct.__field_builder(value))

    @staticmethod
    def __field_builder(field: CField) -> property:
        """
        構建字段屬性描述符 (Builds field property descriptor)

        功能:
            - 將CField包裝為property (Wraps CField as property)
            - 在訪問屬性時自動調用CField.read() (Automatically calls CField.read() when accessing property)

        參數:
            field: CField實例 (CField instance)

        返回:
            property: 屬性描述符，用於訪問字段數據 (Property descriptor for accessing field data)
        """

        def wrapper(self) -> Any:
            return field.read(self.address)

        return property(wrapper)


__READER_TYPE = CData.CPointer | type[CStruct] | Callable