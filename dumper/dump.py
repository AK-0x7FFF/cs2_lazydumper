from collections import namedtuple
from itertools import count

from dumper.cs2_struct import *
from libs.ak_memkit import Pattern
from libs.ak_memkit import Process


# TypeScope = namedtuple("TypeScope", ("struct", "name", "classes",))
# ClassBinding = namedtuple("ClassBinding", ("struct", "name", "fields"))
ClassBindingFields = namedtuple("ClassBindingField", ("struct", "name", "value") )



def read_class_binding_field(binding: SchemaClassBinding) -> Generator[SchemaClassFieldData, None, None]:
    if not binding.field_count:
        return ()

    fields = binding.fields.address.new()
    for _ in range(binding.field_count):
        yield SchemaClassFieldData(fields)
        fields.offset(0x20)


def read_class_binding(type_scope: SchemaSystemTypeScope) -> Generator[SchemaClassBinding, None, None]:
    for binding_ptr in type_scope.class_bindings.elements():
        binding = SchemaClassBinding(binding_ptr)
        yield binding


def read_type_scope(schema_system: SchemaSystem) -> Generator[SchemaSystemTypeScope, None, None]:
    type_scopes = schema_system.type_scopes

    for i in range(type_scopes.count):
        type_scope = type_scopes.element(i)
        yield type_scope


def read_schema_system() -> SchemaSystem:
    schema_system_address = (
        Pattern(
            "4C 8D 35 ?? ?? ?? ?? 0F 28 45",
            schema_system_module := Process.get_global_instance().get_module("schemasystem.dll"),
            Process.get_global_instance().memory_read.read_memory(schema_system_module.base, schema_system_module.size)
        )
        .aob_scan()
        .rip(3, 7)
        .address
    )
    return SchemaSystem(schema_system_address)

def read_test():
    d = {}


    schema_system = read_schema_system()
    for type_scope in read_type_scope(schema_system):
        module_name = type_scope.name
        print(module_name)
        d.setdefault(module_name, {})

        for class_binding in read_class_binding(type_scope):
            class_name = class_binding.name
            print(f"    {class_name}")
            d.get(module_name).setdefault(class_name, {})

            for field_binding in read_class_binding_field(class_binding):
                field_name = field_binding.name
                field_offset = field_binding.offset

                print(f"        {field_name}: {field_offset}")
                d.get(module_name).get(class_name).setdefault(field_name, field_offset)
    # return d




if __name__ == '__main__':
    from libs.ak_memkit import Process
    Process.create_global_instance("cs2.exe", "meow")
    read_test()
    Address.clear_cache()
    print(__import__("psutil").Process(__import__("os").getpid()).memory_info().rss / (1024 ** 2))