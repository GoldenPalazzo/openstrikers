#include "NL/gl/glMatrix.h"
#include "NL/glx/glxMatrix.h"
#include "NL/glx/glxMemory.h"

#include "NL/platvmath.h"
#include <string.h>

static unsigned long gl_IdentityMatrix = 0xFFFFFFFF;

/**
 * Offset/Address/Size: 0x0 | 0x801D8A74 | size: 0x20
 */
void glMatrixLookAt(nlMatrix4& m, const nlVector3& peye, const nlVector3& pat, const nlVector3& vup)
{
    glplatMatrixLookAt(m, peye, pat, vup);
}

/**
 * Offset/Address/Size: 0x20 | 0x801D8A94 | size: 0x20
 */
void glMatrixPerspective(nlMatrix4& m, float fovRad, float aspect, float nearPlane, float farPlane)
{
    glplatMatrixPerspective(m, fovRad, aspect, nearPlane, farPlane);
}

/**
 * Offset/Address/Size: 0x40 | 0x801D8AB4 | size: 0x20
 */
void glMatrixOrthographicCentered(nlMatrix4& m, float width, float height, float nearPlane, float farPlane)
{
    glplatMatrixOrthographicCentered(m, width, height, nearPlane, farPlane);
}

/**
 * Offset/Address/Size: 0x60 | 0x801D8AD4 | size: 0x20
 */
void glMatrixOrthographic(nlMatrix4& m, float width, float height)
{
    glplatMatrixOrthographic(m, width, height);
}

/**
 * Offset/Address/Size: 0x80 | 0x801D8AF4 | size: 0x20
 */
void glSetMatrix(unsigned long matrix, const nlMatrix4& m)
{
    glplatSetMatrix(matrix, m);
}

/**
 * Offset/Address/Size: 0xA0 | 0x801D8B14 | size: 0x20
 */
void glGetMatrix(unsigned long matrix, nlMatrix4& m)
{
    glplatGetMatrix(matrix, m);
}

/**
 * Offset/Address/Size: 0xC0 | 0x801D8B34 | size: 0x34
 */
uintptr_t glAllocMatrix()
{
    uintptr_t p = (uintptr_t)glplatFrameAlloc(sizeof(nlMatrix4), GLM_Matrix);
    if (p == 0)
    {
        p = -1;
    }
    return p;
}

/**
 * Offset/Address/Size: 0xF4 | 0x801D8B68 | size: 0x8
 */
unsigned long glGetIdentityMatrix()
{
    return gl_IdentityMatrix;
}

/**
 * Offset/Address/Size: 0xFC | 0x801D8B70 | size: 0x3C
 */
void gl_MatrixStartup()
{
    nlMatrix4 m;
    m.SetIdentity();
    gl_IdentityMatrix = (unsigned long)glplatResourceAlloc(sizeof(nlMatrix4), GLM_Matrix);
    glplatSetMatrix(gl_IdentityMatrix, m);
}

/**
 * Offset/Address/Size: 0x138 | 0x801D8BAC | size: 0x24
 */
void GLMatrix::Set(const nlMatrix4& m)
{
    memcpy(&matrix, &m, sizeof(nlMatrix4));
}

/**
 * Offset/Address/Size: 0x15C | 0x801D8BD0 | size: 0x30
 */
void GLMatrix::Get(nlMatrix4& m) const
{
    memcpy(&m, &matrix, sizeof(nlMatrix4));
}
