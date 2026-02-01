from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self, Any

from dumper.cs2_struct import *
from dumper.dump import *



class SchemaCacheSystem(ABC):
    cache: dict[str, Address | SchemaCacheSystem] = {}
    reader: Generator[CStruct, None, None]

    def __getattr__(self, name: str) -> SchemaCacheSystem | None:
        return self.get(name)

    def __getitem__(self, name: str) -> SchemaCacheSystem | None:
        return self.get(name)

    @abstractmethod
    def addr2instance(self, address: Address) -> SchemaCacheSystem | None:
        return SchemaTypeScope(SchemaSystemTypeScope(address))


    def get(self, target_name: str) -> SchemaCacheSystem | None:
        target_name = target_name.replace(".", "_").replace(":", "_").lower()

        # read from cache
        instance = self.cache.get(target_name, None)
        if instance is not None:
            if isinstance(instance, Address):
                instance = self.addr2instance(instance)
            return instance

        # read from generator
        for instance in self.reader:
            name = instance.name.replace(".", "_").replace(":", "_").lower()

            address: Address = self.cache.setdefault(name, instance.address)
            if target_name == name:
                instance = self.addr2instance(address)
                self.cache[target_name] = instance
                return instance

        # wrong name
        return None


class SchemaClass(SchemaCacheSystem):
    def __init__(self, class_binding: SchemaClassBinding) -> None:
        self.reader = read_class_binding_field(class_binding)

    def addr2instance(self, address: Address) -> int:
        return SchemaClassFieldData(address).offset

class SchemaTypeScope(SchemaCacheSystem):
    def __init__(self, type_scope: SchemaSystemTypeScope) -> None:
        self.reader = read_class_binding(type_scope)


    def addr2instance(self, address: Address) -> SchemaClass:
        return SchemaClass(SchemaClassBinding(address))


# @lambda cls: cls()
class Schema(SchemaCacheSystem):
    def __init__(self) -> None:
        schema_system = read_schema_system()
        self.reader = read_type_scope(schema_system)

    def addr2instance(self, address: Address) -> SchemaTypeScope:
        return SchemaTypeScope(SchemaSystemTypeScope(address))



if __name__ == '__main__':
    from libs.ak_memkit import Process
    Process.create_global_instance("cs2.exe", "meow")
    schema = Schema()
    print(schema.client_dll.CCSPlayerController.m_iPing)
    print(schema.client_dll.CompositeMaterial_t.m_vecGeneratedTextures)


    print(__import__("psutil").Process(__import__("os").getpid()).memory_info().rss / (1024**2))