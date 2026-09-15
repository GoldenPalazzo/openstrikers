#include "Game/GL/gluSkinMesh.h"
#include "types.h"
#include "NL/gl/glMatrix.h"
#include "NL/gl/glMemory.h"
#include "NL/gl/glModel.h"
#include "NL/gl/glState.h"
#include "NL/glx/glxDisplayList.h"
#include "NL/nlDLRing.h"
#include "NL/nlString.h"
#include "NL/platvmath.h"
#include "dolphin/PPCArch.h"
#include "dolphin/os/OSCache.h"


class TempMatrixCopier
{
public:
    /**
     * Offset/Address/Size: 0x4F0 | 0x801B6034 | size: 0x60
     */
    void CopyMatrix(const unsigned long& boneId, unsigned long* outValue)
    {
        SkinMatrix& matrix = (SkinMatrix&)m_Mesh->GetPoseMatrix(boneId);
        matrix.Get(m_TempMatrices[*outValue]);
    }

    /* 0x00 */ nlMatrix4* m_TempMatrices;
    /* 0x04 */ ShaderSkinMesh* m_Mesh;
}; // total size: 0x8

static inline int SkinIndexOf(const SkinPair& p)
{
    return p.vertexIndex;
}

/**
 * Offset/Address/Size: 0x550 | 0x801B6094 | size: 0xDC
 */
void ShaderSkinMesh::StitchModel()
{
    int packetIndex = 0;
    glModelPacket* pPacket = pModel->packets;
    for (; pPacket < pModel->packets + pModel->numPackets; packetIndex++, pPacket++)
    {
        if (glGetRasterState(pPacket->state.raster, GLS_SolidOffset) != 1)
            continue;
        DisplayList* dl = dlGetStruct(pPacket->indexBuffer);
        u8* pWrite = (u8*)dl->list;
        if (*(pWrite += 3) != 0xff)
            continue;
        for (int i = 0; i < pPacket->numVertices; i++)
        {
            *pWrite = (stitchArray[packetIndex][i] + 1) * 3;
            pWrite += (pPacket->numStreams - 1) * 2 + 1;
        }
    }
}

/**
 * Offset/Address/Size: 0x0 | 0x801B5B44 | size: 0x4F0
 */
void ShaderSkinMesh::AttachSkinData(unsigned long program, const nlMatrix4* pReflect)
{
    nlVector3* outVertices = NULL;
    nlVector3* outNormals = NULL;
    nlAVLTree<unsigned long, unsigned long, DefaultKeyCompare<unsigned long> >* boneMap = &nlRingGetStart<BoneMapList>(boneMaps)->boneMap;

    if (boneMap->m_NumElements != 0)
    {
        if (tempMatrices == NULL)
        {
            tempMatrices = (nlMatrix4*)nlMalloc(boneMap->m_NumElements * sizeof(nlMatrix4), 8, false);
        }

        outVertices = (nlVector3*)glFrameAlloc(numSoftwareVerts * sizeof(nlVector3), GLM_VertexData);
        outNormals = (nlVector3*)glFrameAlloc(numSoftwareVerts * sizeof(nlVector3), GLM_VertexData);

        nlZeroMemory(outVertices, numSoftwareVerts * sizeof(nlVector3));
        nlZeroMemory(outNormals, numSoftwareVerts * sizeof(nlVector3));

        float vertexWeight;

        TempMatrixCopier matCopier;
        matCopier.m_TempMatrices = tempMatrices;
        matCopier.m_Mesh = this;

        boneMap->Walk(&matCopier, &TempMatrixCopier::CopyMatrix);

        SkinPairList* curr = nlRingGetStart<SkinPairList>(skinPairs);
        int matrixOffset = 0;

        if (curr != NULL)
        {
            while (true)
            {
                const nlMatrix4* pMatrix = nullptr;
                if (curr->num != 0) {
                    pMatrix = &tempMatrices[matrixOffset];
                }

                for (int i = 0; i < (int)curr->num; i++)
                {
                    const SkinPair& pair = curr->pairs[i];
                    vertexWeight = (float)pair.vertexWeight / 65535.0f;
                    int index = SkinIndexOf(pair);

                    const nlVector3& inVertex = (morphBuffer != NULL) ? morphBuffer[index] : softwareVertices[index].position;

                    const signed char* packed = softwareVertices[index].packed_normal;
                    float invNormalScale = 0.015625f;
                    nlVector3 inNormal;
                    inNormal.x = (float)packed[0] * invNormalScale;
                    inNormal.y = (float)packed[1] * invNormalScale;
                    inNormal.z = (float)packed[2] * invNormalScale;

                    const nlVector3* pInN = &inNormal;
                    nlVector3& outVertex = outVertices[index];
                    nlVector3& outNormal = outNormals[index];

                    const float* pm = pMatrix->e;
                    outVertex.x += vertexWeight *
                        (pm[0] * inVertex.x + pm[4] * inVertex.y + pm[8]  * inVertex.z + pm[12]);
                    outVertex.y += vertexWeight *
                        (pm[1] * inVertex.x + pm[5] * inVertex.y + pm[9]  * inVertex.z + pm[13]);
                    outVertex.z += vertexWeight *
                        (pm[2] * inVertex.x + pm[6] * inVertex.y + pm[10] * inVertex.z + pm[14]);

                    outNormal.x += vertexWeight *
                        (pm[0] * inNormal.x + pm[4] * inNormal.y + pm[8]  * inNormal.z);
                    outNormal.y += vertexWeight *
                        (pm[1] * inNormal.x + pm[5] * inNormal.y + pm[9]  * inNormal.z);
                    outNormal.z += vertexWeight *
                        (pm[2] * inNormal.x + pm[6] * inNormal.y + pm[10] * inNormal.z);
                }

                if (nlRingIsEnd<SkinPairList>(skinPairs, curr))
                {
                    break;
                }

                curr = curr->m_next;
                matrixOffset++;
            }
        }

        DCFlushRangeNoSync(outVertices, numSoftwareVerts * sizeof(nlVector3));
        DCFlushRangeNoSync(outNormals, numSoftwareVerts * sizeof(nlVector3));
        PPCSync();
    }

    unsigned long matrix;
    if (pReflect == NULL)
    {
        matrix = glGetIdentityMatrix();
    }
    else
    {
        matrix = glAllocMatrix();
        if (matrix != -1)
        {
            glSetMatrix(matrix, *pReflect);
        }
    }

    BoneMapList* mapList = nlRingGetStart<BoneMapList>(boneMaps)->m_next;
    glModelPacket* pPacket = pModel->packets;

    while (pPacket < pModel->packets + pModel->numPackets)
    {
        pPacket->state.matrix = matrix;

        if (program != 0xFFFFFFFF)
        {
            pPacket->state.program = program;
        }

        if (glGetRasterState(pPacket->state.raster, GLS_SolidOffset) == 1)
        {
            glUserAttach(MakeUserData(&mapList->boneMap), pPacket, false);
        }
        else
        {
            pPacket->streams[0].address = (u32)outVertices;
            pPacket->streams[1].address = (u32)outNormals;
            pPacket->streams[1].stride = 0xC;
        }

        mapList = mapList->m_next;
        pPacket++;
    }
}
