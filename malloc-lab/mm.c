/*
 * mm-naive.c - 가장 빠르지만 메모리 효율은 가장 낮은 malloc 패키지.
 *
 * 이 단순 구현에서는 brk 포인터를 그저 증가시키는 방식으로만
 * 블록을 할당합니다. 각 블록은 순수 payload만 가지며,
 * 헤더와 푸터가 없습니다. 블록은 병합되지도 않고 재사용되지도 않습니다.
 * realloc 역시 mm_malloc과 mm_free를 직접 호출하는 방식으로 구현되어 있습니다.
 *
 * 학생 참고:
 * 이 머리말 주석은 나중에 자신의 구현 방식을 높은 수준에서 설명하는
 * 주석으로 바꾸면 됩니다.
 */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <unistd.h>
#include <string.h>

#include "mm.h"
#include "memlib.h"

/*********************************************************
 * 학생 참고:
 * 다른 작업을 하기 전에 아래 구조체에 팀 정보를 먼저 입력하세요.
 ********************************************************/
team_t team = {
    /* 팀 이름 */
    "ateam",
    /* 첫 번째 팀원의 이름 */
    "Harry Bovik",
    /* 첫 번째 팀원의 이메일 주소 */
    "bovik@cs.cmu.edu",
    /* 두 번째 팀원의 이름 (없으면 빈 문자열) */
    "",
    /* 두 번째 팀원의 이메일 주소 (없으면 빈 문자열) */
    ""};

// /* word(4바이트) 또는 double word(8바이트) 정렬 */
// #define ALIGNMENT 8

// /* 크기를 ALIGNMENT의 배수로 올림 */
// // 예를 들어 13이면 16, 20이면 24로 올림
// #define ALIGN(size) (((size) + (ALIGNMENT - 1)) & ~0x7)

// #define SIZE_T_SIZE (ALIGN(sizeof(size_t)))

#define WSIZE 4
#define DSIZE 8
#define CHUNKSIZE (1 << 12)

#define MAX(x, y) ((x) > (y) ? (x) : (y))
#define PACK(size, alloc) ((size) | (alloc))

#define GET(p) (*(unsigned int *)(p))
#define PUT(p, val) (*(unsigned int *)(p) = (val))

#define GET_SIZE(p) (GET(p) & ~0x7)
#define GET_ALLOC(p) (GET(p) & 0x1)

#define HDRP(bp) ((char *)(bp) - WSIZE)
#define FTRP(bp) ((char *)(bp) + GET_SIZE(HDRP(bp)) - DSIZE)

#define NEXT_BLKP(bp) ((char *)(bp) + GET_SIZE(((char *)(bp) - WSIZE)))
#define PREV_BLKP(bp) ((char *)(bp) - GET_SIZE(((char *)(bp) - DSIZE)))

static char *heap_listp;
static char *rover;

static void *extend_heap(size_t words);
static void *coalesce(void *bp);
static void *find_fit(size_t asize);
static void place(void *bp, size_t asize);
static size_t adjust_block_size(size_t size);
static int can_expand_into_next(void *bp, size_t asize);
static void expand_into_next(void *bp, size_t asize);

/*
 * mm_init - malloc 패키지를 초기화한다.
 */
int mm_init(void)
{
    // if (heap_listp = mem_sbrk(4 * WSIZE) == (void *)-1) {
    //     return -1;
    // }
    if ((heap_listp = mem_sbrk(4 * WSIZE)) == (void *)-1) {
        return -1;
    }

    PUT(heap_listp, 0); // 패딩넣어줌 생성 
    PUT(heap_listp + (1 * WSIZE), PACK(DSIZE, 1)); // 프롤로그 헤더 넣어줌
    PUT(heap_listp + (2 * WSIZE), PACK(DSIZE, 1)); // 프롤로그 푸터 넣어줌
    PUT(heap_listp + (3 * WSIZE), PACK(0,1)); // 에필로그 헤더 넣어줌
    heap_listp += (2 * WSIZE); // 페이로드 자리 옮겨줌 프롤로그 푸터 자리로 

    rover = heap_listp;

    if (extend_heap(CHUNKSIZE / WSIZE) == NULL) { // 청크 사이즈 4096로 늘리는데 null이면 리턴함 
        return -1; 
        
    }

    return 0;


}

static void *extend_heap(size_t words) {

    char * bp; // char타입인 이유는 char는 1바이트이기때문
    size_t size;
    
    size = (words % 2) ? (words + 1) * WSIZE : words * WSIZE;

    if ((long)(bp = mem_sbrk(size)) == -1 ) {
        return NULL;
    }
    

    PUT(HDRP(bp), PACK(size, 0));
    PUT(FTRP(bp), PACK(size, 0));
    PUT(HDRP(NEXT_BLKP(bp)), PACK(0,1));

    return coalesce(bp);


}

static void *coalesce (void* bp) {

size_t prev_alloc = GET_ALLOC(FTRP(PREV_BLKP(bp)));
size_t next_alloc = GET_ALLOC(HDRP(NEXT_BLKP(bp)));
size_t size = GET_SIZE(HDRP(bp));

if (prev_alloc && next_alloc) {
    return bp;
} else if (prev_alloc && !next_alloc) {
    size += GET_SIZE(HDRP(NEXT_BLKP(bp)));
    PUT(HDRP(bp), PACK(size,0));
    PUT(FTRP(bp), PACK(size,0));

} else if (!prev_alloc && next_alloc) {
    size += GET_SIZE(HDRP(PREV_BLKP(bp)));
    PUT(FTRP(bp), PACK(size, 0));
    PUT(HDRP(PREV_BLKP(bp)), PACK(size, 0));
    bp = PREV_BLKP(bp);
    
} else {
    size += GET_SIZE(HDRP(PREV_BLKP(bp))) 
          + GET_SIZE(HDRP(NEXT_BLKP(bp)));
    PUT(HDRP(PREV_BLKP(bp)), PACK(size, 0));
    PUT(FTRP(NEXT_BLKP(bp)), PACK(size, 0));
    bp = PREV_BLKP(bp);
}

if ((rover > (char *)bp) && (rover < NEXT_BLKP(bp))) {
    rover = bp;
}

return bp;
}


static void *find_fit(size_t asize)
{
    void *bp;

    for (bp = rover; GET_SIZE(HDRP(bp)) > 0; bp = NEXT_BLKP(bp)) {
        if (!GET_ALLOC(HDRP(bp)) && (asize <= GET_SIZE(HDRP(bp)))) {
            return bp;
        }
    }

    for (bp = heap_listp; bp != rover; bp = NEXT_BLKP(bp)) {
        if (!GET_ALLOC(HDRP(bp)) && (asize <= GET_SIZE(HDRP(bp)))) {
            return bp;
        }
    }
    return NULL;
}



/*
 * mm_malloc - brk 포인터를 증가시키는 방식으로 블록을 할당한다.
 * 항상 정렬 단위의 배수 크기를 갖는 블록을 할당한다.
 */
// void *mm_malloc(size_t size)
// {
//     int newsize = ALIGN(size + SIZE_T_SIZE);
//     void *p = mem_sbrk(newsize);
//     if (p == (void *)-1)
//         return NULL;
//     else
//     {
//         *(size_t *)p = size;
//         return (void *)((char *)p + SIZE_T_SIZE);
//     }
// }

void *mm_malloc(size_t size) // 
{   
    // 헤더 + 페이로드(size) + 푸터로 만든 공간 변수 선언
    size_t asize;

    // 힙을 확장한 크기 변수 선언
    // size_t extend_size;

    // 페이로드 주소 위치 선언 
    char *bp;

    // TODO 사용자가 요청한게 0 이면 그냥 NULL 리턴 
    if (size == 0) {
        return NULL;
    }

    asize = adjust_block_size(size);

    // TODO asize에 free 장소를 찾았다면(null 이아니면) 장소에다 위치하고 bp를 반환
    if ((bp = find_fit(asize)) != NULL) {
        place(bp, asize);
        return bp;
    }
    // TODO free장소를 찾이못했으면 사이즈를 늘려라 (asize, CHUNKSIZE)중 큰걸로 
    // TODO extend_heap 을 하는데 NULL이면 return NULL해라
    if ((bp = extend_heap(MAX(asize, CHUNKSIZE) / WSIZE)) == NULL) {
        return NULL;
    }
    // extend heap한거 위치하고 bp를 return 해라 
    place(bp, asize);
    return bp; 
}

static void place(void *bp, size_t asize) //
{
    size_t csize = GET_SIZE(HDRP(bp));

    
    if ((csize - asize) >= (2 * DSIZE)) {
        PUT(HDRP(bp), PACK(asize, 1));
        PUT(FTRP(bp), PACK(asize, 1));
        bp = NEXT_BLKP(bp);
        PUT(HDRP(bp), PACK(csize - asize, 0));
        PUT(FTRP(bp), PACK(csize - asize, 0));
        rover = bp;
    } else {
        PUT(HDRP(bp), PACK(csize, 1));
        PUT(FTRP(bp), PACK(csize, 1));
        rover = NEXT_BLKP(bp);
    }
}


/*
 * mm_free - 현재 구현에서는 블록을 해제해도 아무 일도 하지 않는다.
 */
void mm_free(void *ptr)
{
    size_t size = GET_SIZE(HDRP(ptr));

    PUT(HDRP(ptr), PACK(size, 0));
    PUT(FTRP(ptr), PACK(size, 0));
    coalesce(ptr);
}


/*
 * mm_realloc - mm_malloc과 mm_free를 이용해 단순하게 구현한다.
 */
void *mm_realloc(void *bp, size_t size)
{
    void *newptr;
    size_t copySize;

    if (bp == NULL) {
        return mm_malloc(size);
    }

    if (size == 0) {
        mm_free(bp);
        return NULL;
    }

    size_t oldsize = GET_SIZE(HDRP(bp));
    size_t asize = adjust_block_size(size);

    if (asize <= oldsize) {

        size_t remainder = oldsize - asize;

        if (remainder >= 2 * DSIZE) {
            
            PUT(HDRP(bp), PACK(asize, 1));
            PUT(FTRP(bp), PACK(asize, 1));

            void *split_bp = NEXT_BLKP(bp);
            PUT(HDRP(split_bp),  PACK(remainder, 0));
            PUT(FTRP(split_bp),  PACK(remainder, 0));

            if ((rover > (char *)bp) && (rover < NEXT_BLKP(split_bp))) {
                rover = split_bp;
            }

            coalesce(split_bp);
        }

        return bp;
    }

    if (can_expand_into_next(bp, asize)) {
        expand_into_next(bp, asize);
        return bp; 
    }

    newptr = mm_malloc(size);
    if (newptr == NULL) {
        return NULL;
    }

    copySize = GET_SIZE(HDRP(bp)) - DSIZE; // payload epdlxj qhrtk
    if (size < copySize) {
        copySize = size;
    }

    memcpy(newptr, bp, copySize); // 헤더와 푸터는 mm_malloc한 곳
    mm_free(bp);
    return newptr;
}

static size_t adjust_block_size(size_t size) {
    
        // TODO size 사용자가 요청 한 크기가 8바이트(한블럭의 최소크기)라면 asize는 최소크기 16바이트 [(헤더 4) + 페이로드 (8) + 푸터(4)]
    if (size <= DSIZE) {
        return 2 * DSIZE;
    }
    // TODO 아니면 size + 8의 배수로 보정한값 으로 asize 할당
    else {
        return DSIZE * ((size + DSIZE + (DSIZE - 1)) / DSIZE);
    }   
}

// 현재 블록 bp가 "다음 free 블록"을 흡수해서 asize를 만족할 수 있는지 검사
static int can_expand_into_next(void *bp, size_t asize)
{
    void *next_bp = NEXT_BLKP(bp);

    // epilogue면 불가능
    if (GET_SIZE(HDRP(next_bp)) == 0) {
        return 0;
    }

    // 다음 블록이 할당 중이면 불가능
    if (GET_ALLOC(HDRP(next_bp))) {
        return 0;
    }

    // 현재 블록 + 다음 free 블록 크기를 합쳐서 충분한지 확인
    if (GET_SIZE(HDRP(bp)) + GET_SIZE(HDRP(next_bp)) >= asize) {
        return 1;
    }

    return 0;
}

// bp가 다음 free 블록을 흡수해서 asize 이상이 되도록 확장
// 남는 공간이 최소 블록 크기 이상이면 split
static void expand_into_next(void *bp, size_t asize)
{
    void *next_bp = NEXT_BLKP(bp);
    size_t oldsize = GET_SIZE(HDRP(bp));
    size_t nextsize = GET_SIZE(HDRP(next_bp));
    size_t combined = oldsize + nextsize;
    char *merged_end = (char *)bp + combined;

    if (combined - asize >= 2 * DSIZE) {
        PUT(HDRP(bp), PACK(asize, 1));
        PUT(FTRP(bp), PACK(asize, 1));
        // 변경: 요청 크기만큼 현재 블록을 확장해서 allocated로 유지

        void *split_bp = NEXT_BLKP(bp);
        PUT(HDRP(split_bp), PACK(combined - asize, 0));
        PUT(FTRP(split_bp), PACK(combined - asize, 0));
        // 추가: 남는 공간이 충분하면 뒤를 다시 free block으로 남겨둠
        // 이유: utilization을 덜 해치기 위해

        if ((rover > (char *)bp) && (rover < merged_end)) {
            rover = split_bp;
        }
    }
    else {
        PUT(HDRP(bp), PACK(combined, 1));
        PUT(FTRP(bp), PACK(combined, 1));
        // 추가: 애매하게 남는 작은 조각은 split하지 않고 전부 현재 블록에 포함
        // 이유: 쓸모없는 작은 free block 생성을 막기 위해

        if ((rover > (char *)bp) && (rover < merged_end)) {
            rover = bp;
        }
    }
}
