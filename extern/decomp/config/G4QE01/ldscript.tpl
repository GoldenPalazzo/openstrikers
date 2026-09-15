MEMORY
{
    text : origin = $ORIGIN
}

SECTIONS
{
    GROUP:
    {
        $SECTIONS
        .stack ALIGN(0x100):{}
    } > text

    _stack_end = $LAST_SECTION_SYMBOL + SIZEOF($LAST_SECTION_NAME);
    // The stack region begins at the 0x100-aligned boundary after the last data
    // section (matching the `.stack ALIGN(0x100)` above); align _stack_end up to
    // 0x100 before reserving STACKSIZE so _stack_addr/__ArenaLo land on the same
    // addresses the original linker produced (0x80388000 / 0x8038A000). Without
    // this alignment the formula computes 0x28 too low, breaking any TU (e.g. OS.c)
    // that references _stack_addr/__ArenaLo by relocation.
    _stack_addr = (((_stack_end + 0xFF) & ~0xFF) + $STACKSIZE + 0x7) & ~0x7;
    _db_stack_addr = (_stack_addr + 0x2000);
    _db_stack_end = _stack_addr;
    __ArenaLo = _db_stack_addr;
    __ArenaHi = $ARENAHI;
}

FORCEACTIVE
{
    _MetroTRK_Has_Framing
    $FORCEACTIVE
}
