#ifdef __cplusplus
#pragma once
#include <cstdint>
#include <bit>
#include <type_traits>
#include <cstring>
#include <cassert>

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

        static constexpr T swap(T v) noexcept {
            if constexpr (std::endian::native == std::endian::big) {
                return v; // Nessun effetto se la CPU è già Big-Endian
            } else {
                if constexpr (sizeof(T) == 1) {
                    return v;
                } else if constexpr (sizeof(T) == 2) {
                    auto raw = std::bit_cast<uint16_t>(v);
                    return std::bit_cast<T>(__builtin_bswap16(raw));
                } else if constexpr (sizeof(T) == 4) {
                    auto raw = std::bit_cast<uint32_t>(v);
                    return std::bit_cast<T>(__builtin_bswap32(raw));
                } else if constexpr (sizeof(T) == 8) {
                    auto raw = std::bit_cast<uint64_t>(v);
                    return std::bit_cast<T>(__builtin_bswap64(raw));
                }
            }
        }

        constexpr be() noexcept = default;
        constexpr be(T v) noexcept : val(swap(v)) {}

        constexpr operator T() const noexcept {
            return swap(val);
        }

        constexpr be& operator=(T v) noexcept {
            val = swap(v);
            return *this;
        }

        constexpr be& operator=(const be&) noexcept = default;

        be& operator+=(T v) noexcept {
            *this = static_cast<T>(*this) + v;
            return *this;
        }

        be& operator-=(T v) noexcept {
            *this = static_cast<T>(*this) - v;
            return *this;
        }

        be& operator*=(T v) noexcept {
            *this = static_cast<T>(*this) * v;
            return *this;
        }

        be& operator/=(T v) noexcept {
            *this = static_cast<T>(*this) / v;
            return *this;
        }

        be& operator|=(T v) noexcept {
            *this = static_cast<T>(*this) | v;
            return *this;
        }

    };
    static_assert(sizeof(be<char>) == 1);

    template <typename T>
    struct SelfRelPtr32 {
#define SELFREL_NULL 0xFFFFFFFFu
        be<int32_t> m_relativeOffset;

        T* get() const noexcept {
            uint32_t raw = static_cast<uint32_t>(m_relativeOffset.val);
            if (raw == SELFREL_NULL) return nullptr;

            uintptr_t base = reinterpret_cast<uintptr_t>(this);
            intptr_t offset = static_cast<int32_t>(m_relativeOffset);
            
            return reinterpret_cast<T*>(base + offset);
        }

        SelfRelPtr32& operator=(T* target) noexcept {
            if (!target) {
                m_relativeOffset = SELFREL_NULL;
            } else {
                uintptr_t base = reinterpret_cast<uintptr_t>(this);
                uintptr_t dest = reinterpret_cast<uintptr_t>(target);
                intptr_t offset = dest-base;
                assert(offset >= INT32_MIN && offset <= INT32_MAX && "SelfRelPtr32 offset overflow");
                int32_t diff = static_cast<int32_t>(offset);
                m_relativeOffset = diff;
            }
            return *this;
        }

        SelfRelPtr32& operator=(std::nullptr_t) noexcept {
            m_relativeOffset = SELFREL_NULL;
            return *this;
        }

        template <typename Integral>
        requires std::is_integral_v<Integral>
        SelfRelPtr32& operator=(Integral /*val*/) noexcept {
            m_relativeOffset = SELFREL_NULL;
            return *this;
        }

        T* operator->() const noexcept { return get(); }
        operator T*() const noexcept { return get(); }
        template <typename DummyT = T>
            requires(!std::is_void_v<DummyT>)
        DummyT& operator*() const noexcept { return *get(); }

        template <typename U>
        operator U*() const noexcept {
            return reinterpret_cast<U*>(get());
        }
    };
    static_assert(sizeof(SelfRelPtr32<char>) == 4);

}

#endif
