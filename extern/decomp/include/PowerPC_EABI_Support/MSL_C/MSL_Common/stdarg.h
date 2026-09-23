#ifndef _STDARG_H_
#define _STDARG_H_

#ifdef TARGET_PC
// stdarg.h is compiler-provided, not libc-provided, and Clang's resource-dir
// version sits earlier in the include search order than our -idirafter
// directory, so #include_next can't reach back to it from here. Use the
// compiler builtins directly instead (this is what the real header does).
typedef __builtin_va_list va_list;
#define va_start(ap, param) __builtin_va_start(ap, param)
#define va_arg(ap, type)    __builtin_va_arg(ap, type)
#define va_end(ap)          __builtin_va_end(ap)
#define va_copy(dst, src)   __builtin_va_copy(dst, src)
#else

#ifndef __VA_LIST_COMPAT_DEFINED
typedef struct __va_list_struct
{
    char gpr;
    char fpr;
    char reserved[2];
    char* input_arg_area;
    char* reg_save_area;
} __va_list[1];
typedef __va_list va_list;
#endif
extern void __builtin_va_info(void*);

void* __va_arg(va_list v_list, unsigned char type);

#ifndef __MWERKS__
#define _var_arg_typeof(e) 0
#endif

#define va_start(ap, fmt) ((void)fmt, __builtin_va_info(&ap))
#define va_arg(ap, t)     (*((t*)__va_arg(ap, _var_arg_typeof(t))))
#define va_end(ap)        (void)0

#endif // TARGET_PC

#endif
