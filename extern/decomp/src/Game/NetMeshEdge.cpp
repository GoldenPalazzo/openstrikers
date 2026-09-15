#include "Game/Physics/NetMeshEdge.h"

/**
 * Offset/Address/Size: 0x114 | 0x80130138 | size: 0x20
 * NetMeshModelLoader::NetMeshVertex::GetPosition() const
 */
const nlVector3* NetMeshModelLoader::NetMeshVertex::GetPosition() const
{
    u8* layout = *(u8**)((char*)mpPacket + 0x0C);
    u8 stride = *(u8*)(layout + 0x05);
    s8* base = *(s8**)(layout + 0x00);

    return (const nlVector3*)(base + stride * mIndex);
}

/**
 * Offset/Address/Size: 0x74 | 0x80130098 | size: 0xA0
 * NetMeshModelLoader::NetMeshVertex::GetNormal(nlVector3&) const
 */
void NetMeshModelLoader::NetMeshVertex::GetNormal(nlVector3& normal) const
{
    float f = 0.015625f;

    u8* layout = *(u8**)((u8*)mpPacket + 0x0C);
    u8 stride = *(u8*)(layout + 0x0B);
    s8* base = *(s8**)(layout + 0x06);

    s8 normalX = (base + stride * mIndex)[0];
    s8 normalY = (base + stride * mIndex)[1];
    s8 normalZ = (base + stride * mIndex)[2];

    normal.x = (float)normalX * f;
    normal.y = (float)normalY * f;
    normal.z = (float)normalZ * f;
}

/**
 * Offset/Address/Size: 0x0 | 0x80130024 | size: 0x74
 * NetMeshModelLoader::NetMeshVertex::GetTextureCoord(nlVector2&) const
 */
void NetMeshModelLoader::NetMeshVertex::GetTextureCoord(nlVector2& txtCoord) const
{
    u8* layout = *(u8**)((u8*)mpPacket + 0x0C);
    u8 stride = *(u8*)(layout + 0x17);
    s8* base = *(s8**)(layout + 0x12);

    s16* offset = (s16*)(base + stride * mIndex);

    s16 texCoordX = offset[0];
    s16 texCoordY = offset[1];

    float f = 0.0009765625f;

    txtCoord.x = (float)texCoordX * f;
    txtCoord.y = (float)texCoordY * f;
}
