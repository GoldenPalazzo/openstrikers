#include "NL/nlMath.h"
#include "endian.hpp"

struct FEScissorBox
{
    /* 0x0 */ port::be<u16> X;
    /* 0x2 */ port::be<u16> Y;
    /* 0x4 */ port::be<u16> Width;
    /* 0x6 */ port::be<u16> Height;

    operator nlFont::ScissorBox() const
    {
        nlFont::ScissorBox out;
        out.X = X;
        out.Y = Y;
        out.Width = Width;
        out.Height = Height;
        return out;
    }
};

class feVector2
{
public:
    /* 0x0 */ port::be<f32> x;
    /* 0x2 */ port::be<f32> y;

    feVector2& operator=(const nlVector2& v)
    {
        x = v.x;
        y = v.y;
        return *this;
    }

    operator nlVector2() const
    {
        nlVector2 out;
        out.x = x;
        out.y = y;
        return out;
    }
}; // total size: 0x8


