from __future__ import annotations

from abc import ABC
from typing import Self, Any, Callable

from libs.ak_memkit import Address



class CData:
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
        def __init__(self, size: int) -> None:
            self.size = size

        def __call__(self, address: Address) -> CStruct | Address:
            return address.str(self.size)



class CField(Address):
    """
    A[x]    -> __class_getitem__ -> CFieldReader
    A[x](y) -> __class_getitem__ -> CFieldReader -> CFieldReader.__call__ -> CField
    """

    class CFieldReader:
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
        # super().__init__(address)  # no need :D
        self.offset = offset

    @classmethod
    def __class_getitem__(cls, reader: __READER_TYPE) -> CFieldReader:
        """
        []方法註冊，
        用於返回特定內存讀取的類
        """
        return CField.CFieldReader(reader)

    @staticmethod
    def _reader(address: Address):
        """
        內存讀取函數，未覆蓋前為返回偏移後地址
        這是用於被覆蓋的調用用內存讀取函數，別刪！！
        """
        return address

    def read(self, address: Address) -> Address:
        """
        返回該內存的數據，
        在CStruct的CField被調用時調用
        """
        return self._reader(address.new().offset(self.offset))


class CStruct(ABC):
    def __init__(self, address: int | Address) -> None:
        self.address = None
        if isinstance(address, int):
            self.address = Address(address)
        elif isinstance(address, Address):
            self.address = address

        if self.address is None:
            raise ValueError()

    def __repr__(self) -> str:
        return f"CStruct->{self.__class__.__name__}({self.address})"


    def __init_subclass__(cls, static: bool = False, **kwargs) -> None:
        """
        被作為父類繼承時調用
        用於處理該子類的CField
        這將覆蓋所有類定義時類中的CField
        """
        super().__init_subclass__(**kwargs)

        for name, value in cls.__dict__.items():
            if not isinstance(value, CField): continue
            setattr(cls, name, CStruct.__field_builder(value))

    @staticmethod
    def __field_builder(field: CField) -> property:
        """
        CField處理，
        將調用重定向到CField.read()函數
        """
        def wrapper(self) -> Any:
            return field.read(self.address)
        return property(wrapper)


__READER_TYPE = CData.CPointer | type[CStruct] | Callable