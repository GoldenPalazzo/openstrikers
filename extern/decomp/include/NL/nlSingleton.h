#ifndef NL_SINGLETON_H
#define NL_SINGLETON_H

template <class T>
class nlSingleton
{
protected:
    ~nlSingleton() {}

public:
    static T* Instance() { return s_pInstance; }
    static T* GetInstance() { return s_pInstance; }

    static void CreateInstance()
    {
        if (!s_pInstance)
            s_pInstance = new T();
    }

    static void DestroyInstance()
    {
        T* p = s_pInstance;
        if (p)
        {
            delete p;
            s_pInstance = 0;
        }
    }
#ifndef TARGET_PC
    static T* s_pInstance;
#else
    static inline T* s_pInstance = nullptr;
#endif
};

#endif // NL_SINGLETON_H
