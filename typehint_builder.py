from os import PathLike
from pathlib import Path

from dumper.dump import *
from libs.ak_memkit import Process



def build(file_location: str | PathLike, file_name: str) -> None:
    Process.create_global_instance("cs2.exe", "meow")
    schema_system = read_schema_system()

    with open(Path(file_location) / f"{file_name}.pyi", "w") as f:
        f.write("### Build From typehint_builder.py by AK32767 ###\n\n")
        f.write("class Schema:\n")

        for type_scope in read_type_scope(schema_system):
            f.write(f"    class {type_scope.name.replace(".", "_").replace(":", "_")}:\n")

            for class_binding in read_class_binding(type_scope):
                f.write(f"        class {class_binding.name.replace(".", "_").replace(":", "_")}:\n")

                for field in read_class_binding_field(class_binding):
                    f.write(f"            {field.name.replace(".", "_").replace(":", "_")}: int\n")

                f.write(f"            ...\n\n")
            f.write(f"        ...\n\n")


def main() -> None:
    build(".", "schema")


if __name__ == '__main__':
    main()