from typing import Generator

from ak_memkit import Address
from .cstruct import CStruct, CField, CData



class SchemaClassFieldData(CStruct):
    name = CField[CData.CPointer(CData.CString(128))](0x0)
    # type = CField[CData.CPointer(SchemaType)](0x8)
    offset = CField[CData.i32](0x10)
    metadata_count = CField[CData.i32](0x14)
    # metadata = CField[CData.CPointer(SchemaMetadataEntryData)](0x10)


class SchemaBaseClass(CStruct):
    name = CField[CData.CPointer(CData.CString(128))](0x10)


class SchemaBaseClassInfoData(CStruct):
    cls: SchemaBaseClass = CField[CData.CPointer(SchemaBaseClass)](0x18)


class SchemaClassBinding(CStruct):
    base = CField[CData.CPointer()](0x0)
    name = CField[CData.CPointer(CData.CString(128))](0x8)
    module_name = CField[CData.CPointer(CData.CString(128))](0x10)
    size = CField[CData.i32](0x18)
    field_count = CField[CData.i16](0x1C)
    static_metadata_count = CField[CData.i16](0x1E)
    alignment = CField[CData.u8](0x22)
    has_base_class = CField[CData.u8](0x23)
    total_class_size = CField[CData.i16](0x24)
    derived_class_size = CField[CData.i16](0x26)
    fields: SchemaClassFieldData = CField[CData.CPointer(SchemaClassFieldData)](0x28)
    base_classes: SchemaBaseClassInfoData = CField[CData.CPointer(SchemaBaseClassInfoData)](0x38)
    # static_metadata = CField[CData.CPointer(SchemaMetadataEntryData)](0x40)
    # type_scope = CField[CData.CPointer(SchemaSystemTypeScope)](0x50)


class UtlTsHashAllocatedBlob(CStruct):
    next = CField[CData.CPointer()](0x0)
    data = CField[CData.CPointer()](0x10)


class TsListHead(CStruct):
    next = CField[CData.CPointer()](0x0)


class TsListBase(CStruct):
    head: TsListHead = CField[TsListHead](0x0)


class UtlMemoryPool(CStruct):
    block_size = CField[CData.i32](0x0)
    blocks_per_blob = CField[CData.i32](0x4)
    # grow_mode = CField[MemoryPoolGrowType](0x8)
    blocks_allocated = CField[CData.i32](0xC)
    peak_allocated = CField[CData.i32](0x10)
    alignment = CField[CData.u16](0x14)
    blob_count = CField[CData.u16](0x16)
    free_blocks: TsListBase = CField[TsListBase](0x20)
    # blob_head = CField[CData.CPointer(UtlMemoryPoolBlob)](0x48)
    total_size = CField[CData.i32](0x50)


class UtlTsHashFixedData(CStruct):
    ui_key = CField[CData.u64](0x0)
    next = CField[CData.CPointer()](0x8)
    data = CField[CData.CPointer()](0x10)


class UtlTsHashBucket(CStruct):
    add_lock = CField[CData.u64](0x0)
    first: UtlTsHashFixedData = CField[CData.CPointer(UtlTsHashFixedData)](0x8)
    first_uncommitted: UtlTsHashFixedData = CField[CData.CPointer(UtlTsHashFixedData)](0x10)


class UtlTsHash(CStruct):
    entry_mem: UtlMemoryPool = CField[UtlMemoryPool](0x0)
    buckets = CField[UtlTsHashBucket](0x60)
    needs_commit = CField[CData.bool](0x1860)
    contention_check = CField[CData.i32](0x1864)

    def elements(self) -> Generator[Address, None, None]:
        yield from self.allocated_elements()
        yield from self.unallocated_elements()

    def bucket(self, index: int) -> UtlTsHashBucket:
        return UtlTsHashBucket(self.buckets.address.new().offset(0x18 * index))

    def allocated_elements(self) -> Generator[Address, None, None]:
        used_count = self.entry_mem.blocks_allocated

        element_counter = 0
        for bucket in range(256):
            bucket = self.bucket(bucket)
            note_ptr = bucket.first_uncommitted
            # print(note_ptr)

            while note_ptr.address and element_counter < used_count:
                if data := note_ptr.data:
                    yield data
                    # print(hex(data.address))
                    element_counter += 1

                note_ptr = UtlTsHashFixedData(note_ptr.next)

    def unallocated_elements(self) -> Generator[Address, None, None]:
        free_count = self.entry_mem.peak_allocated
        element_counter = 0

        blob_ptr = UtlTsHashAllocatedBlob(self.entry_mem.free_blocks.head.next)

        while blob_ptr.address and element_counter < free_count:
            if (data := blob_ptr.data) and data.address < (1 << 47) - 1:
                yield data
                # print(hex(data.address))
                element_counter += 1

            blob_ptr = UtlTsHashAllocatedBlob(blob_ptr.next)


class SchemaSystemTypeScope(CStruct):
    name = CField[CData.CString(0x100)](0x8)
    global_scope = CField(0x0108)  # !!!
    class_bindings: UtlTsHash = CField[UtlTsHash](0x0560)
    enum_bindings: UtlTsHash = CField[UtlTsHash](0x1DD0)


class UtlVector(CStruct):
    count = CField[CData.i32](0x0)
    data = CField[CData.CPointer()](0x8)

    def element(self, index: int) -> SchemaSystemTypeScope:
        if index > self.count:
            raise ValueError()

        return SchemaSystemTypeScope(self.data.new().pointer(index * 0x8))


class SchemaSystem(CStruct):
    type_scopes: UtlVector = CField[UtlVector](0x190)
    registration_count = CField[CData.u32](0x280)