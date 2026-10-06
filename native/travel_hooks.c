/* Version-locked hooks for Poker Quest v63/build 2021. No OS imports.
   The patch is applied only to a private executable copy. */
unsigned __int64 __readgsqword(unsigned long);
#pragma intrinsic(__readgsqword)
#include "travel_strings.h"
typedef unsigned long long U64;
typedef unsigned int U32;
typedef struct { int length, padding; const char *text; } String;
int _fltused=0;
#define P(o,n) (*(void **)((char *)(o)+(n)))
#define I(o,n) (*(int *)((char *)(o)+(n)))
#define B(o,n) (*(unsigned char *)((char *)(o)+(n)))
#define FN(r,t) ((t)(base()+(r)))
static U64 base(void) { return *(U64 *)(__readgsqword(0x60)+0x10); }
static String str(const char *s) { String x; int n=0; while(s[n])n++; x.length=n;x.padding=0;x.text=s;return x; }
static int travel(void *mod) { String *s; if(!mod)return 0;s=(String *)((char *)mod+0x28);return s->length>7 && s->text[0]=='T' && s->text[1]=='R' && s->text[2]=='A' && s->text[3]=='V' && s->text[4]=='E' && s->text[5]=='L' && s->text[6]==' '; }
static void push(void *array,void *item) { int n=I(array,0x10); if(n>=I(array,0x14))FN(0x1ba7170,void (*)(void *,int))(array,n+1); ((void **)P(array,0x18))[n]=item;I(array,0x10)=n+1; }
static int mode;
static void *header;
__declspec(dllexport) U64 tr_state[16];

__declspec(dllexport) void *tr_menu_array(void **out,const int *items,int count) {
    int next[5]={5,6,7,10,9};
    if(count==5 && items[0]==5 && items[1]==6 && items[2]==7 && items[3]==8 && items[4]==9) {
        return FN(0x30d520,void *(*)(void **,const int *,int))(out,next,5);
    }
    return FN(0x30d520,void *(*)(void **,const int *,int))(out,items,count);
}

static void *open_mode(void **out,void *controller,int selected) {
    mode=selected;
    return FN(0x17bb770,void *(*)(void **,void *))(out,controller);
}
static void *open_travel(void **out,void *controller) { return open_mode(out,controller,1); }
static void *open_challenge(void **out,void *controller) { return open_mode(out,controller,0); }
__declspec(dllexport) void tr_setting(void *screen,int id,String *label,String *tip,void **callback,unsigned char enabled) {
    void *controller=P(screen,0x240),*cb=0;
    typedef void (*Set)(void *,int,String *,String *,void **,unsigned char);
    typedef void *(*Bind)(void **,const char *,void *,void *);
    if(id==7) {
        FN(0x1bb8b60,Bind)(&cb,l_callback.text,controller,open_challenge);
        FN(0xf53040,Set)(screen,id,label,tip,&cb,enabled);
    } else if(id==8) {
        /* Replace Custom Run rather than retaining an extra menu entry. */
        String name=str(l_menu.text),description=str(l_tooltip.text);
        FN(0x1bb8b60,Bind)(&cb,l_callback.text,controller,open_travel);
        FN(0xf53040,Set)(screen,10,&name,&description,&cb,1);
        tr_state[0]=(U64)screen;tr_state[1]=(U64)controller;tr_state[2]=1;
    } else FN(0xf53040,Set)(screen,id,label,tip,callback,enabled);
}

__declspec(dllexport) void *tr_mods(void **out,void **arr) {
    int i;void *mod;
    FN(0x845f0,void *(*)(void **,void **))(out,arr);
    tr_state[3]=I(*out,0x10);
    for(i=0;i<TR_COUNT;i++) {
        String id=str(tr_ids[i].text);mod=0;
        FN(0x85e60,void *(*)(void **,String *))(&mod,&id);
        if(mod && travel(mod)) { push(*out,mod);tr_state[4]++; }
    }
    return out;
}
__declspec(dllexport) void *tr_entry(void **out,void *stack,void **mod,unsigned char canSelect,void **layout,void **stars) {
    return FN(0x1a96ee0,void *(*)(void **,void *,void **,unsigned char,void **,void **))(out,stack,mod,travel(*mod)?1:canSelect,layout,stars);
}
__declspec(dllexport) void *tr_header(void *layout,void **out,String *text,void *translate,void **reuse) {
    void *result=FN(0x2ffd30,void *(*)(void *,void **,String *,void *,void **))(layout,out,text,translate,reuse);
    header=*out;return result;
}
__declspec(dllexport) void tr_show(void *controller,void **screenRef) {
    void *screen=*screenRef,*entries=P(screen,0x298),*first=0,*chosen=P(screen,0x248);
    int i,n=I(entries,0x10),visible=0;
    struct { U64 isNull; double value; } padding={0,70};
    String title=str(mode?l_title_travel.text:l_title_challenge.text);
    String decorated={0},fullTitle={0};
    String *diamond=(String *)(base()+0x23c6ab8);
    for(i=0;i<n;i++) {
        void *entry=((void **)P(entries,0x18))[i],*mod=P(entry,0x2c0);
        int show=travel(mod)==mode;
        FN(0x58a0c0,unsigned char (*)(void *,unsigned char))(entry,(unsigned char)show);
        if(show) {
            FN(0x58a730,double (*)(void *,double))(entry,112.0*visible++);
            if(!first && B(entry,0x242))first=entry;
        } else FN(0x58a730,double (*)(void *,double))(entry,0.0);
    }
    if(chosen && travel(P(chosen,0x2c0))!=mode)chosen=0;
    if(!chosen)FN(0x8016b0,void (*)(void *,void **))(screen,&first);
    if(header) {
        FN(0x1bddf90,void *(*)(String *,String *,String *))(diamond,&decorated,&title);
        FN(0x1bddf90,void *(*)(String *,String *,String *))(&decorated,&fullTitle,diamond);
        FN(0x457c10,void (*)(void *,String *))(header,&fullTitle);
    }
    FN(0x17be520,void (*)(void *,void **))(controller,screenRef);
    FN(0x172f530,void (*)(void *))(P(screen,0x278));
    if(P(screen,0x248))FN(0x172d3e0,void (*)(void *,void **,void *))(P(screen,0x278),(void **)((char *)screen+0x248),&padding);
    tr_state[5]=mode;tr_state[6]=visible;tr_state[7]=(U64)screen;
}
/* Prefix only: the original concatenation supplies name and description. */
__declspec(dllexport) void *tr_footer(String *prefix,String *out,String *name) {
    String replacement=str(l_footer.text);
    return FN(0x1bddf90,void *(*)(String *,String *,String *))(mode?&replacement:prefix,out,name);
}
/* Enemy-only call site in RefillDeckAndDrawAction.onInit. The native calculator
   adds the temporary round bonus after its base-count clamp. A negative visible
   bonus would otherwise reduce the total below the unchanged hidden-card count.
   CardDrawInfo: actor +0x10, total +0x18, visible +0x1c, hidden +0x20. */
__declspec(dllexport) void tr_enemy_draw(void *drawInfo) {
    FN(0x9d5230,void (*)(void *))(drawInfo);
    if(P(drawInfo,0x10) && I(drawInfo,0x1c)<0) {
        I(drawInfo,0x1c)=0;
        I(drawInfo,0x18)=I(drawInfo,0x20);
    }
}
/* Only the p2 calculation in ModifierEvent.adjustStat is intercepted. The
   explicit Travel marker leaves all original numeric/formula amounts intact.
   Use the same seeded RNG entry as rollLightning0to100; keep the original stat
   update, maximum-life cap and healing listeners after calculating the amount. */
__declspec(dllexport) double tr_restoration_amount(void *event,String *amount) {
    int i,n;
    const char *marker=l_restoration_roll.text;
    for(i=0;marker[i];i++) {
        if(i>=amount->length || amount->text[i]!=marker[i])
            return FN(0x16ab600,double (*)(void *,String *))(event,amount);
    }
    if(i!=amount->length)
        return FN(0x16ab600,double (*)(void *,String *))(event,amount);
    /* Positive truncation gives seven integer buckets; clamp the RNG's possible
       1.0 endpoint so the inclusive range remains 1..7. */
    n=1+(int)(FN(0x16b5e20,double (*)(void *))(event)*7.0);
    if(n>7)n=7;
    if(n<1)n=1;
    return (double)n;
}
#ifdef TR_TEST
__declspec(dllexport) void tr_selftest(void *controller) {
    void *out=0,*screen,*selected,*hero;int i;
    FN(0x17bea90,void (*)(void *))(controller);
    tr_state[8]=1;
    for(i=0;i<4;i++) {
        open_mode(&out,controller,i%2);
        tr_state[8]=2+i;
    }
    screen=P(controller,0x48);selected=P(screen,0x248);
    tr_state[9]=(U64)selected;
    if(selected) {
        void *mod=P(selected,0x2c0);
        FN(0x17be6f0,void (*)(void *,String *))(controller,(String *)((char *)mod+0x28));
        hero=P(controller,0x40);tr_state[10]=(U64)hero;tr_state[8]=10;
    }
}
#endif
