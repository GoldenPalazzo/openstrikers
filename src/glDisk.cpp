#include "port/glDisk.h"
#include "NL/gl/glUserData.h"
#include "NL/gl/glModel.h"

namespace port::disk {

void convert(::glModelStream& out, const glModelStream& in)
{
    out.address = static_cast<u32>(in.address);
    out.id = in.id;
    out.stride = in.stride;
    out.dataSize = 0;
    out.endianness = std::endian::big;
}

void convert(::glStateBundle& out, const glStateBundle& in)
{
    out.texturestate = static_cast<u64>(in.texturestate);
    out.materialstate = static_cast<u32>(in.materialstate);
    out.program = static_cast<u32>(in.program);
    out.raster = static_cast<u32>(in.raster);
    out.matrix = static_cast<u32>(in.matrix);          // resta offset grezzo, risolto nel fixup
    for (int i = 0; i < 6; i++)
        out.texture[i] = static_cast<u32>(in.texture[i]);
    out.texconfig = in.texconfig;
    out.pad = in.pad;
    out.userStateKey = static_cast<u32>(in.userStateKey);
}

void convert(::glModelPacket& out, const glModelPacket& in)
{
    out.userData = static_cast<u32>(in.userData);
    out.indexBuffer = static_cast<u32>(in.indexBuffer);   // offset grezzo, risolto nel fixup
    out.numVertices = static_cast<u16>(in.numVertices);
    out.primType = in.primType;
    out.numStreams = in.numStreams;
    out.streams = reinterpret_cast<::glModelStream*>(static_cast<uintptr_t>(static_cast<u32>(in.streams))); // offset grezzo
    convert(out.state, in.state);
    out.materialset = static_cast<u32>(in.materialset);
}

void convert(::glModel& out, const glModel& in)
{
    out.numPackets = static_cast<u32>(in.numPackets);
    out.id = static_cast<u32>(in.id);
    out.pad = 0;
    out.packets = reinterpret_cast<::glModelPacket*>(static_cast<uintptr_t>(static_cast<u32>(in.packets))); // offset grezzo
}

} // namespace port::disk
