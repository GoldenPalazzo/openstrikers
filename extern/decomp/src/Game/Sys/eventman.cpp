#include "Game/Sys/eventman.h"

#include "NL/nlString.h"
#include "NL/nlDLRing.h"
#include "NL/nlMemory.h"

EventManager* g_pEventManager = 0;

/**
 * Offset/Address/Size: 0x488 | 0x801FAE08 | size: 0x94
 */
EventManager::~EventManager()
{
    if (m_pool)
    {
        delete (u32*)m_pool;
    }

    if (m_dest)
    {
        delete[] m_dest;
        m_dest = 0;
    }

    if (m_handlers)
    {
        nlDeleteDLRing(&m_handlers);
    }
}

void EventManager::AllocateEvents(unsigned long uEventCount, unsigned long uEventSize)
{
    m_count = uEventCount;
    m_size = uEventSize;

    u32 total = m_size * m_count;
    m_pool = (char*)nlMalloc(total, 8, false);

    nlPrintf("Event Manager: Allocating %d events of size %d. Total = %d bytes\n",
        m_count,
        m_size,
        total);

    for (u32 i = 0; i < uEventCount; i++)
    {
        Event* e = new (m_pool + m_size * i) Event();
        nlDLRingAddEnd(&m_free, e);
    }
}

EventManager::EventManager(unsigned long uEventCount, unsigned long uEventSize)
    : m_dispatching(false)
    , m_handlers(NULL)
    , m_free(NULL)
    , m_keep(NULL)
    , m_queue(NULL)
    , m_deferred(NULL)
    , m_dest(NULL)
    , m_pool(NULL)
{
    AllocateEvents(uEventCount, uEventSize);
    SetupDestArray();
}

void EventManager::FlushEventQueue()
{
    Event* pEvent;
    while (m_keep != NULL && m_keep->m_next->m_nReferenceCount == 0)
    {
        pEvent = m_keep->m_next;
        nlDLRingRemove<Event>(&m_keep, pEvent);
        nlDLRingAddEnd<Event>(&m_free, pEvent);
    }
}

/**
 * Offset/Address/Size: 0x370 | 0x801FACF0 | size: 0x118
 */
void EventManager::Create(unsigned long uEventCount, unsigned long uEventSize)
{
    EventManager* m = new (nlMalloc(sizeof(EventManager), 8, false)) EventManager(uEventCount, uEventSize);
    g_pEventManager = m;
}

/**
 * Offset/Address/Size: 0x30C | 0x801FAC8C | size: 0x64
 */
#pragma push
#pragma optimization_level 1
#pragma optimize_for_size on
#pragma scheduling off
EventHandler* EventManager::AddEventHandler(EventCallback pEventHandlerFunc, void* pParam, unsigned long uDestinationMask)
{
    EventHandler* eventHandler = (EventHandler*)nlMalloc(sizeof(EventHandler), 8, 0);
    EventHandler** head = &m_handlers;

    eventHandler->m_pCBFunction = pEventHandlerFunc;
    EventHandler* element = eventHandler;
    eventHandler->m_uDestinationMask = uDestinationMask;
    eventHandler->m_pCBParam = pParam;
    nlDLRingAddEnd<EventHandler>(head, element);
    return eventHandler;
}
#pragma pop

/**
 * Offset/Address/Size: 0x2D4 | 0x801FAC54 | size: 0x38
 */
void EventManager::RemoveEventHandler(EventHandler* h)
{
    nlDLRingRemove<EventHandler>(&m_handlers, h);
    delete h;
}

/**
 * Offset/Address/Size: 0x1C4 | 0x801FAB44 | size: 0x110
 */
void EventManager::AllocateDestArray(unsigned long count, unsigned long maskDefault)
{
    m_dest = (u32*)nlMalloc(count * sizeof(u32), 8, false);
    for (u32 i = 0; i < count; ++i)
    {
        m_dest[i] = maskDefault;
    }
}

/**
 * Offset/Address/Size: 0xF4 | 0x801FAA74 | size: 0xD0
 */
Event* EventManager::CreateValidEvent(unsigned long eventID, unsigned long uSize)
{
    if (uSize > m_size)
    {
        nlPrintf("Event Manager: Size mismatch on event creation (%d vs %d)!\n", m_size, uSize); // @326
        return NULL;
    }

    Event* e = GetFreeEvent();

    if (!e)
    {
        return NULL;
    }

    e->m_uEventID = eventID; // stw at +0x08

    return e;
}

Event* EventManager::GetFreeEvent()
{
    Event* e;
    if (!m_free)
    {
        nlPrintf("Event Manager: There are no more free events in the free event list!\n"); // @293
        e = NULL;
    }
    else
    {
        e = nlDLRingRemoveStart(&m_free);
        if (m_dispatching)
        {
            nlDLRingAddEnd(&m_deferred, e);
        }
        else
        {
            nlDLRingAddEnd(&m_queue, e);
        }
    }
    return e;
}

/**
 * Offset/Address/Size: 0x0 | 0x801FA980 | size: 0xF4
 */
void EventManager::DispatchEvents()
{
    m_dispatching = 1; // stb 1 at +0
    while (m_queue != 0)
    {
        Event* e = nlDLRingRemoveStart(&m_queue); // free->queue ring
        if (m_handlers != 0)
        {
            EventHandler* it = nlDLRingGetStart(m_handlers);
            do
            {
                u32 mask = m_dest[e->m_uEventID]; // dest[type]
                if ((it->m_uDestinationMask & mask) != 0)
                {
                    void (*fn)(Event*, void*) = it->m_pCBFunction;
                    void* ud = it->m_pCBParam;
                    (*fn)(e, ud); // bctrl
                }

                if (it == m_handlers)
                    break;

                it = it->m_next;
            } while (1);
        }
        if (e->m_nReferenceCount != 0)
        {
            nlDLRingAddEnd(&m_keep, e);
        }
        else
        {
            nlDLRingAddEnd(&m_free, e);
        }
    }

    m_dispatching = 0;
    m_queue = m_deferred;
    m_deferred = NULL;
}
