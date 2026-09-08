// compat_shims/endian.h
#ifdef __cplusplus
#pragma once
#include <cstdint>
#include <bit>
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

namespace port
{
template <typename T>
struct be {
    static_assert(std::is_trivially_copyable_v<T>, "BE<T> requires a POD type");
    T val;
    operator T() const {
        if constexpr (std::endian::native == std::endian::big) {
            return val;
        } else {
            if constexpr (sizeof(T) == 1) return val;
            else if constexpr (sizeof(T) == 2) return static_cast<T>(__builtin_bswap16(static_cast<uint16_t>(val)));
            else if constexpr (sizeof(T) == 4) return static_cast<T>(__builtin_bswap32(static_cast<uint32_t>(val)));
            else if constexpr (sizeof(T) == 8) return static_cast<T>(__builtin_bswap64(static_cast<uint64_t>(val)));
        }
    }

    // overload operator= only if loading host-endian values that need to
    // be stored as big-endian
};
}

#endif
