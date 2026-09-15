#ifndef _AUDIOSTREAMVIRTUALS_H_
#define _AUDIOSTREAMVIRTUALS_H_

#include "Game/Sys/GCStream.h"

namespace GCAudioStreaming
{

inline bool StereoAudioStream::SafeToPurge()
{
    bool result = false;
    if (m_State <= SS_Initd && !nlAsyncReadsPending(m_pFile))
    {
        result = true;
    }
    return result;
}

inline MonoAudioStream::~MonoAudioStream()
{
    Destructor();
}

inline bool MonoAudioStream::SafeToPurge()
{
    bool result = false;
    if (m_State <= SS_Initd && !nlAsyncReadsPending(m_pFile))
    {
        result = true;
    }
    return result;
}

inline void MonoAudioStream::Purge()
{
    m_State = SS_New;
    nlClose(m_pFile);
}

inline void StereoAudioStream::Purge()
{
    m_State = SS_New;
    nlClose(m_pFile);
}

} // namespace GCAudioStreaming

#endif // _AUDIOSTREAMVIRTUALS_H_
