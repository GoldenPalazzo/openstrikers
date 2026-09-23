#pragma once
#include "endian.hpp"

struct glModelStream;
struct glStateBundle;
struct glModelPacket;
struct glModel;

namespace port::disk {
#pragma pack(push, 1)
struct glModelStream
{
    /* 0x0 */ be<u32> address;
    /* 0x4 */ u8 id;
    /* 0x5 */ u8 stride;
}; // total size: 0x6

struct glStateBundle
{
    /* 0x00 */ be<u64> texturestate;
    /* 0x08 */ be<u32> materialstate;
    /* 0x0C */ be<u32> program;
    /* 0x10 */ be<u32> raster;
    /* 0x14 */ be<u32> matrix;
    /* 0x18 */ be<u32> texture[6];
    /* 0x30 */ u8 texconfig;
    /* 0x31 */ u8 pad;
    /* 0x32 */ be<u32> userStateKey;
}; // total size: 0x36

struct glModelPacket
{
    /* 0x00 */ be<u32> userData;
    /* 0x04 */ be<u32> indexBuffer;
    /* 0x08 */ be<u16> numVertices;
    /* 0x0A */ u8 primType;
    /* 0x0B */ u8 numStreams;
    /* 0x0C */ be<u32> streams;
    /* 0x10 */ glStateBundle state;
    /* 0x46 */ be<u32> materialset;
}; // total size: 0x4A

struct glModel
{
    /* 0x00 */ be<u32> numPackets;
    /* 0x04 */ be<u32> id;
    /* 0x08 */ be<u32> pad;
    /* 0x0C */ be<u32> packets;
}; // total size: 0x10
#pragma pack(pop)

static_assert(sizeof(glModelStream) == 0x6);
static_assert(sizeof(glStateBundle) == 0x36);
static_assert(sizeof(glModelPacket) == 0x4A);
static_assert(sizeof(glModel) == 0x10);

void convert(::glModelStream& out, const glModelStream& in);
void convert(::glStateBundle& out, const glStateBundle& in);
void convert(::glModelPacket& out, const glModelPacket& in);
void convert(::glModel& out, const glModel& in);

} // namespace port::disk
