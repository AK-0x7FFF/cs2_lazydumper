from __future__ import annotations

from abc import ABC, abstractmethod
from xxhash import xxh3_64

from .dumper.cs2_struct import *
from .dumper.dump import *
from ak_memkit import Address


class SchemaCacheSystem(ABC):
    _SEED: int = 1337
    cache: dict[int, SchemaCacheSystem] = {}

    def __init__(self, key: int = 0) -> None:
        self.key = key

    def __repr__(self) -> str:
        return f"SchemaSystem:{self.__class__.__name__}({hex(self.key)})"

    def __getattr__(self, name: str) -> SchemaCacheSystem | None:
        return self.get(name)

    def __getitem__(self, name: str) -> SchemaCacheSystem | None:
        return self.get(name)

    @property
    @abstractmethod
    def reader(self) -> Generator[CStruct, None, None]:
        ...

    @abstractmethod
    def addr2instance(self, key: int, address: Address) -> SchemaCacheSystem | None:
        ...


    def get(self, target_name: str) -> SchemaCacheSystem | None:
        target_name = target_name.replace(".", "_").replace(":", "_").lower()
        key_hash = (self.key << 16)
        target_hash = key_hash ^ xxh3_64(target_name, seed=self._SEED).intdigest()

        # read cache
        instance = self.cache.get(target_hash, None)
        if instance is not None:
            # print(f"[{self.__class__.__name__}] HIT Cache! {target_name}: {hex(target_hash)}")
            return instance

        # read reader
        for instance in self.reader:
            name = instance.name.replace(".", "_").replace(":", "_").lower()
            name_hash = key_hash ^ xxh3_64(name, seed=self._SEED).intdigest()

            instance = self.cache.setdefault(
                name_hash,
                self.addr2instance(name_hash, instance.address)
            )
            # print(f"[{self.__class__.__name__}] Cached {name}: {hex(name_hash)}")
            if target_name == name:
                # print(f"[{self.__class__.__name__}] Found! {target_name}: {hex(target_hash)}")
                return instance

        # wrong name
        return None
        # raise ValueError(f"No schema for {target_name}")


    def cache_all_reader_remaining(self):
        for instance in self.reader:
            name = instance.name.replace(".", "_").replace(":", "_").lower()
            name_hash = (self.key << 16) ^ xxh3_64(name, seed=self._SEED).intdigest()

            instance = self.addr2instance(name_hash, instance.address)
            self.cache[name_hash] = instance

            if issubclass(instance.__class__, SchemaCacheSystem):
                instance.cache_all_reader_remaining()



class SchemaClass(SchemaCacheSystem):
    def __init__(self, key: int, class_binding: SchemaClassBinding) -> None:
        super().__init__(key)
        self._reader = read_class_binding_field(class_binding)

    @property
    def reader(self) -> Generator[SchemaClassFieldData, None, None]:
        return self._reader

    def addr2instance(self, key: int, address: Address) -> int:
        return SchemaClassFieldData(address).offset



class SchemaTypeScope(SchemaCacheSystem):
    def __init__(self, key: int, type_scope: SchemaSystemTypeScope) -> None:
        super().__init__(key)
        self._reader = read_class_binding(type_scope)

    @property
    def reader(self) -> Generator[SchemaClassBinding, None, None]:
        return self._reader

    def addr2instance(self, key: int, address: Address) -> SchemaClass:
        return SchemaClass(key, SchemaClassBinding(address))



@lambda cls: cls()
class Schema(SchemaCacheSystem):
    def __init__(self) -> None:
        super().__init__()
        self._reader = None

    def setup(self, schema_system: SchemaSystem) -> None:
        self._reader = read_type_scope(schema_system)

    @property
    def reader(self) -> Generator[CStruct, None, None]:
        return self._reader

    def addr2instance(self, key: int, address: Address) -> SchemaTypeScope:
        return SchemaTypeScope(key, SchemaSystemTypeScope(address))

    def get(self, target_name: str) -> SchemaCacheSystem | None:
        if self._reader is None:
            raise RuntimeError()

        return super().get(target_name)

    def load_all(self) -> SchemaCacheSystem:
        self.cache_all_reader_remaining()

        # cache
        for instance in self.cache.copy().values():
            if issubclass(instance.__class__, SchemaCacheSystem):
                instance.cache_all_reader_remaining()





if __name__ == '__main__':
    ...