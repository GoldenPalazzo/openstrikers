#ifndef _SAVEFRAME_H_
#define _SAVEFRAME_H_

class SaveFrame
{
public:
    template <int N, typename T>
    void Replayable(T& current);

    template <int N, typename T>
    void Replayable(T& current, ReplayablePod);

    template <int N>
    void Replayable(bool& current, ReplayablePod);

    template <int N, typename T>
    void Replayable(T& current, NotReplayablePod);

    template <int N, typename T>
    void ReplayablePolymorphicPtr(T*& ptr);

    /* 0x0 */ int mInterval;
    /* 0x4 */ WriteByteStream mStream;
}; // total size: 0xC

template <int N, typename T>
inline void SaveFrame::Replayable(T& current)
{
    typename ReplayableCategory<T>::Type category = ReplayableCategoryOf(current);
    Replayable<N>(current, category);
}

template <int N, typename T>
inline void SaveFrame::Replayable(T& current, ReplayablePod)
{
    if (N == 0 || mInterval == N)
    {
        memcpy(mStream.mStorage, &current, sizeof(T));
        mStream.mStorage += sizeof(T);
    }
}

template <int N>
inline void SaveFrame::Replayable(bool& current, ReplayablePod)
{
    char value = current ? 1 : 0;
    memcpy(mStream.mStorage, &value, 1);
    mStream.mStorage += 1;
}

template <int N, typename T>
inline void SaveFrame::Replayable(T& current, NotReplayablePod)
{
    if (N == 0 || mInterval == N)
    {
        current.Replay(*this);
    }
}

template <int N, typename T>
inline void SaveFrame::ReplayablePolymorphicPtr(T*& ptr)
{
    T* current = ptr;
    if (N == 0 || mInterval == N)
    {
        unsigned char notNull = (current != 0);
        memcpy(mStream.mStorage, &notNull, 1);
        mStream.mStorage++;

        if (notNull)
        {
            char typeId = (char)current->GetType();
            if (typeId < 0 || typeId > 4)
                nlBreak();

            memcpy(mStream.mStorage, &typeId, 1);
            mStream.mStorage++;

            ::Replayable<N>(*this, typeId, current);
        }
    }
}
#endif
