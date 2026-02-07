from os.path import abspath
from pathlib import Path

from cs2_lazydumper.dumper.dump import *
from ak_memkit import Process



def build_pyi() -> None:
    Process.set_mode("meow").create("cs2.exe")
    schema_system = read_schema_system()

    with open("schema.pyi", "w") as f:
        f.write("### Build From typehint_builder.py ###\n\n")
        f.write(f"from dumper.cs2_struct import SchemaSystem\n\n\n")
        f.write("class Schema:\n")
        f.write("\n".join((
            "    @classmethod",
            "    def setup(cls, schema_system: SchemaSystem) -> None: ",
            "        ...",
            "",
            "    @classmethod",
            "    def load_all(cls) -> None:",
            "        ...",
            "\n",
        )))

        for type_scope in read_type_scope(schema_system):
            f.write(f"    class {type_scope.name.replace(".", "_").replace(":", "_")}:\n")

            for class_binding in read_class_binding(type_scope):
                f.write(f"        class {class_binding.name.replace(".", "_").replace(":", "_")}:\n")

                for field in read_class_binding_field(class_binding):
                    f.write(f"            {field.name.replace(".", "_").replace(":", "_")}: int\n")

                f.write(f"            ...\n\n")
            f.write(f"        ...\n\n")


def main() -> None:
    build_pyi("../..", "schema")


if __name__ == '__main__':
    main()