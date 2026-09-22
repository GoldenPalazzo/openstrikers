#ifndef _MSL_COMMON_ALLOC_H
#define _MSL_COMMON_ALLOC_H


#ifdef __cplusplus
extern "C" {
#endif

#ifndef TARGET_PC
void free(void* ptr);
#endif

#ifdef __cplusplus
}
#endif

#endif /* _MSL_COMMON_ALLOC_H */
