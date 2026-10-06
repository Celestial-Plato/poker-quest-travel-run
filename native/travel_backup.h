/* Injected code uses the game's resolved Win32 functions, never new imports.
   UI calls this synchronously before opening the Travel selection screen. */
typedef unsigned short TR_WCHAR;
typedef struct { unsigned short year,month,weekday,day,hour,minute,second,millis; } TR_TIME;
typedef struct {
    unsigned int attributes;
    unsigned int times[6],sizeHigh,sizeLow,reserved[2];
    TR_WCHAR name[260],alternate[14];
} TR_FIND_DATA;
typedef struct {
    int (*createDir)(const TR_WCHAR *,void *);
    unsigned int (*attributes)(const TR_WCHAR *);
    void (*time)(TR_TIME *);
    void *(*findFirst)(const TR_WCHAR *,TR_FIND_DATA *);
    int (*findNext)(void *,TR_FIND_DATA *);
    int (*findClose)(void *);
    int (*copy)(const TR_WCHAR *,const TR_WCHAR *,int);
    void *(*createFile)(const TR_WCHAR *,unsigned int,unsigned int,void *,unsigned int,unsigned int,void *);
    int (*close)(void *);
    unsigned int (*error)(void);
} TR_BACKUP_API;
static int tr_wcopy(TR_WCHAR *out,const TR_WCHAR *input,int n) {
    int i;for(i=0;input[i];i++){if(i>=n-1)return 0;out[i]=input[i];}out[i]=0;return 1;
}
static int tr_wappend(TR_WCHAR *out,const TR_WCHAR *input,int n) {
    int i=0;while(out[i])i++;return tr_wcopy(out+i,input,n-i);
}
static void tr_number(TR_WCHAR *out,unsigned int value,int digits) {
    int i;for(i=digits-1;i>=0;i--){out[i]=(TR_WCHAR)('0'+value%10);value/=10;}out[digits]=0;
}
static int tr_save_snapshot(const TR_WCHAR *root,TR_BACKUP_API *api) {
    static TR_WCHAR folder[2048],source[2048],destination[2048],pattern[2048];
    TR_WCHAR stamp[48],number[5];TR_TIME time;TR_FIND_DATA data;
    void *find,*marker;int attempt,ok=1;
    if(!tr_wcopy(folder,root,2048)||!tr_wappend(folder,(const TR_WCHAR *)L"TravelRun-backups",2048))return 0;
    if(!api->createDir(folder,0)&&(api->attributes(folder)==0xffffffff||!(api->attributes(folder)&0x10)))return 0;
    api->time(&time);
    tr_number(stamp,time.year,4);tr_number(stamp+4,time.month,2);tr_number(stamp+6,time.day,2);
    stamp[8]='-';tr_number(stamp+9,time.hour,2);tr_number(stamp+11,time.minute,2);tr_number(stamp+13,time.second,2);
    stamp[15]='-';tr_number(stamp+16,time.millis,3);stamp[19]='Z';stamp[20]=0;
    if(!tr_wappend(folder,(const TR_WCHAR *)L"\\",2048)||!tr_wappend(folder,stamp,2048))return 0;
    for(attempt=0;attempt<100;attempt++) {
        if(!tr_wcopy(destination,folder,2048))return 0;
        if(attempt){tr_number(number,attempt,2);if(!tr_wappend(destination,(const TR_WCHAR *)L"-",2048)||!tr_wappend(destination,number,2048))return 0;}
        if(api->createDir(destination,0))break;
        if(api->error()!=183)return 0;
    }
    if(attempt==100||!tr_wcopy(folder,destination,2048))return 0;
    if(!tr_wcopy(pattern,root,2048)||!tr_wappend(pattern,(const TR_WCHAR *)L"*.sol",2048))return 0;
    find=api->findFirst(pattern,&data);
    if(find==(void *)-1) {
        if(api->error()!=2)return 0;
    } else {
        do {
            if(data.attributes&0x10)continue;
            if(!tr_wcopy(source,root,2048)||!tr_wappend(source,data.name,2048)||
               !tr_wcopy(destination,folder,2048)||!tr_wappend(destination,(const TR_WCHAR *)L"\\",2048)||
               !tr_wappend(destination,data.name,2048)||!api->copy(source,destination,1)){ok=0;break;}
        } while(api->findNext(find,&data));
        if(ok&&api->error()!=18)ok=0;
        api->findClose(find);
    }
    if(!ok||!tr_wcopy(destination,folder,2048)||!tr_wappend(destination,(const TR_WCHAR *)L"\\.complete",2048))return 0;
    marker=api->createFile(destination,0x40000000,0,0,1,0x80,0);
    if(marker==(void *)-1)return 0;
    return api->close(marker);
}
