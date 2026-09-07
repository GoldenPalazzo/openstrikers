// compat_shims/endian.h
#ifdef __cplusplus
#pragma once
#include <cstdint>
#include <type_traits>

template <typename T>
constexpr T bswap(T val) noexcept
{
    static_assert(std::is_unsigned_v<T>, "nlByteSwap requires an unsigned type");
    if constexpr (sizeof(T) == 2)
        return __builtin_bswap16(val);
    else if constexpr (sizeof(T) == 4)
        return __builtin_bswap32(val);
    else if constexpr (sizeof(T) == 8)
        return __builtin_bswap64(val);
    else
        static_assert(sizeof(T) == 0, "unsupported dimension");
}
#endif

struct GXTextureHeader;
void SwapGXTextureHeader(GXTextureHeader* header);
