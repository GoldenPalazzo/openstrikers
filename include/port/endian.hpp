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
    static constexpr uint32_t SELFREL_NULL = 0xFFFFFFFFu;

    // Reports a target that a 32-bit self-relative pointer cannot reach, and
    // aborts.
    [[noreturn]] void SelfRelPtr32OutOfRange(const void* field, const void* target, long long offset);
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

        be& operator&=(T v) noexcept {
            *this = static_cast<T>(*this) & v;
            return *this;
        }

        be& operator^=(T v) noexcept {
            *this = static_cast<T>(*this) ^ v;
            return *this;
        }

    };
    static_assert(sizeof(be<char>) == 1);

    enum class RelNull
    {
        Sentinel,
        SentinelOrZero
    };

    template <typename T, RelNull Nulls>
    struct RelPtr32 {
        be<int32_t> m_relativeOffset;

        static constexpr uint32_t NullEncoding =
            (Nulls == RelNull::SentinelOrZero) ? 0u : SELFREL_NULL;

        T* get() const noexcept {
            uint32_t raw = static_cast<uint32_t>(m_relativeOffset.val);
            if (raw == SELFREL_NULL) return nullptr;
            if constexpr (Nulls == RelNull::SentinelOrZero)
                if (raw == 0) return nullptr;

            uintptr_t base = reinterpret_cast<uintptr_t>(this);
            intptr_t offset = static_cast<int32_t>(m_relativeOffset);
            
            return reinterpret_cast<T*>(base + offset);
        }

        RelPtr32& operator=(T* target) noexcept {
            if (!target) {
                m_relativeOffset = static_cast<int32_t>(NullEncoding);
            } else {
                uintptr_t base = reinterpret_cast<uintptr_t>(this);
                uintptr_t dest = reinterpret_cast<uintptr_t>(target);
                intptr_t offset = dest-base;
                if (offset < INT32_MIN || offset > INT32_MAX) {
                    SelfRelPtr32OutOfRange(this, target, (long long)offset);
                }
                m_relativeOffset = static_cast<int32_t>(offset);
            }
            return *this;
        }

        RelPtr32& operator=(std::nullptr_t) noexcept {
            m_relativeOffset = static_cast<int32_t>(NullEncoding);
            return *this;
        }

        template <typename Integral>
        requires std::is_integral_v<Integral>
        RelPtr32& operator=(Integral /*val*/) noexcept {
            m_relativeOffset = SELFREL_NULL;
            return *this;
        }

        T* operator->() const noexcept { return get(); }
        operator T*() const noexcept { return get(); }
        template <typename DummyT = T>
            requires(!std::is_void_v<DummyT>)
        DummyT& operator*() const noexcept { return *get(); }

        // golden TODO: this is extermely dangerous and should be removed
        // after all major refactors are done
        template <typename U>
            requires(!std::is_same_v<std::remove_cv_t<T>, std::remove_cv_t<U>>)
        operator U*() const noexcept {
            return reinterpret_cast<U*>(get());
        }

        constexpr bool operator==(std::nullptr_t other) const noexcept {
            return get() == other;
        }
    };
    template <typename T> using SelfRelPtr32 = RelPtr32<T, RelNull::Sentinel>;
    template <typename T> using UnrelocatedRelPtr32 = RelPtr32<T, RelNull::SentinelOrZero>;
    static_assert(sizeof(RelPtr32<int, RelNull::Sentinel>) == 4);
    static_assert(sizeof(SelfRelPtr32<char>) == 4);
    static_assert(sizeof(UnrelocatedRelPtr32<void>) == 4);

}
