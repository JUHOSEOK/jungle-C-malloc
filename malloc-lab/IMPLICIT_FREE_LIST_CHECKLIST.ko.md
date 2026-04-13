# Implicit Free List 구현 체크리스트

이 문서는 [/workspaces/malloc_lab_docker/malloc-lab/mm.c](/workspaces/malloc_lab_docker/malloc-lab/mm.c)에 `implicit free list` 기반 malloc allocator를 구현하기 위해 해야 할 일을 최대한 잘게 쪼갠 체크리스트입니다.

목표는 다음입니다.

- `naive allocator`를 버리고
- `implicit free list + boundary tag + first fit + split + immediate coalescing`
- 구조로 동작하는 첫 번째 allocator를 완성하는 것

이 문서는 "무엇을 구현해야 하는가"에만 집중합니다. 고득점 최적화보다는, **정확하게 동작하는 첫 구현**을 만드는 것이 우선입니다.

---

## 0. 최종 목표를 먼저 고정하기

구현 시작 전에 아래 설계를 먼저 고정합니다.

- free 블록 관리는 `implicit free list`로 한다
- 탐색 전략은 `first fit`으로 한다
- free 직후 바로 `coalesce`한다
- 적당한 free 블록을 찾았을 때 남는 공간이 충분하면 `split`한다
- `realloc`은 처음에는 단순 버전으로 구현한다

여기서 아직 하지 않을 것:

- explicit free list
- segregated free list
- 고급 `realloc` 최적화
- 공격적인 성능 튜닝

체크:

- [x] 이번 1차 구현은 `implicit free list`만 목표로 한다
- [x] `first fit`으로 구현하기로 결정했다
  - 힙의 시작점부터 탐색하여 메모리 크기가 맞는거 있으면 바로 할당하는 방식
- [x] `immediate coalescing`을 사용하기로 결정했다
  - free() 가 발생하면 조건을 살핀후 부합하면 즉시 합치는 방식 

---

## 1. 블록 구조를 종이에 먼저 확정하기

코드보다 먼저 블록 메모리 레이아웃을 확정해야 합니다.

기본 블록 구조:

```c
[ header | payload ... | footer ]
          ^
          bp
```

헤더와 푸터에 들어갈 정보:

- 블록 전체 크기
- 할당 여부 비트

보통 저장 형식:

```c
size | alloc_bit
```

예:

- `16 | 1` = 크기 16, 할당 상태
- `24 | 0` = 크기 24, free 상태

체크:

- [ ] `bp`는 payload 시작 주소라는 점을 이해했다
- [ ] header/footer에는 `size + alloc bit`가 저장된다는 점을 이해했다
- [ ] 블록 크기는 header/footer/payload를 모두 포함한 전체 크기라는 점을 이해했다
- [ ] 블록 크기는 정렬 단위의 배수여야 한다

---

## 2. 힙의 시작과 끝 구조 이해하기

`mm_init`에서 보통 다음 구조를 만듭니다.

```c
[ padding | prologue header | prologue footer | epilogue header ]
```

각 역할:

- `padding`
  - 정렬을 맞추기 위한 공간
- `prologue`
  - 힙 맨 앞 경계 처리를 쉽게 하기 위한 가짜 할당 블록
- `epilogue`
  - 힙 맨 끝 표시용 크기 0짜리 할당 블록

체크:

- [ ] prologue 블록이 왜 필요한지 설명할 수 있다
- [ ] epilogue header가 왜 필요한지 설명할 수 있다
- [ ] coalescing에서 경계 조건을 쉽게 처리하기 위한 장치라는 점을 이해했다

---

## 3. 먼저 정의해야 할 상수 정리

보통 아래 상수들이 필요합니다.

```c
#define WSIZE 4
#define DSIZE 8
#define CHUNKSIZE (1 << 12)
```

의미:

- `WSIZE`: 헤더/푸터 1개 크기
- `DSIZE`: 정렬 단위
- `CHUNKSIZE`: 힙을 기본으로 늘리는 단위

또 최소 블록 크기 감각도 잡아야 합니다.

예를 들어 header + footer + 최소 payload를 생각하면, 너무 작은 블록은 split하면 안 됩니다.

체크:

- [ ] `WSIZE`, `DSIZE`, `CHUNKSIZE`를 정의했다
- [ ] 최소 블록 크기를 어떻게 잡을지 결정했다
- [ ] split 시 남는 블록이 최소 블록 크기보다 작으면 나누지 않겠다고 정했다

---

## 4. 매크로 먼저 작성하기

구현 전에 매크로부터 안정적으로 만들어야 합니다.

필수 매크로 후보:

```c
#define PACK(size, alloc) ...
#define GET(p) ...
#define PUT(p, val) ...
#define GET_SIZE(p) ...
#define GET_ALLOC(p) ...
#define HDRP(bp) ...
#define FTRP(bp) ...
#define NEXT_BLKP(bp) ...
#define PREV_BLKP(bp) ...
```

이 매크로들이 하는 일:

- `PACK`
  - size와 alloc bit를 하나의 값으로 합침
- `GET`, `PUT`
  - 메모리 읽기/쓰기
- `GET_SIZE`, `GET_ALLOC`
  - 헤더/푸터 값에서 크기와 상태 추출
- `HDRP`, `FTRP`
  - payload 포인터에서 header/footer 위치 계산
- `NEXT_BLKP`, `PREV_BLKP`
  - 다음/이전 블록 위치 계산

체크:

- [ ] `PACK(size, alloc)`를 구현했다
- [ ] `GET`, `PUT`를 구현했다
- [ ] `GET_SIZE`, `GET_ALLOC`를 구현했다
- [ ] `HDRP(bp)`를 구현했다
- [ ] `FTRP(bp)`를 구현했다
- [ ] `NEXT_BLKP(bp)`를 구현했다
- [ ] `PREV_BLKP(bp)`를 구현했다
- [ ] 각 매크로가 정확히 무엇을 가리키는지 말로 설명할 수 있다

---

## 5. 전역 포인터 준비하기

보통 힙 리스트 시작점을 가리키는 전역 포인터가 필요합니다.

예:

```c
static char *heap_listp;
```

이 포인터는 보통 prologue의 payload 쪽을 가리키게 둡니다.

체크:

- [ ] 힙 시작 지점을 가리킬 전역 포인터를 선언했다
- [ ] 이 포인터가 정확히 어디를 가리키는지 정했다

---

## 6. `mm_init` 구현 체크리스트

`mm_init`의 역할:

- 초기 힙 영역 확보
- padding/prologue/epilogue 만들기
- heap 시작 포인터 설정
- 첫 free 블록 생성을 위해 `extend_heap` 호출

세부 단계:

1. `mem_sbrk`로 초기 공간 확보
2. padding word 기록
3. prologue header 기록
4. prologue footer 기록
5. epilogue header 기록
6. `heap_listp` 설정
7. `extend_heap` 호출

체크:

- [ ] `mem_sbrk` 실패 시 `-1`을 반환하도록 처리했다
- [ ] padding을 기록했다
- [ ] prologue header를 올바르게 기록했다
- [ ] prologue footer를 올바르게 기록했다
- [ ] epilogue header를 올바르게 기록했다
- [ ] `heap_listp`를 적절한 위치로 이동시켰다
- [ ] 초기 free 블록 생성을 위해 `extend_heap`를 호출했다
- [ ] `mm_init`가 성공 시 `0`을 반환하게 했다

---

## 7. `extend_heap` 구현 체크리스트

`extend_heap`의 역할:

- 힙이 부족할 때 새 메모리를 확보
- 새 free 블록 생성
- 새 epilogue 생성
- 인접 free 블록과 병합

세부 단계:

1. 요청 크기를 정렬 단위에 맞게 조정
2. `mem_sbrk(size)` 호출
3. 새 free 블록의 header 기록
4. 새 free 블록의 footer 기록
5. 새 epilogue header 기록
6. `coalesce(bp)` 호출

체크:

- [ ] 요청 크기를 짝수 word 기준으로 보정했다
- [ ] `mem_sbrk` 실패 처리했다
- [ ] 새 free 블록 header를 기록했다
- [ ] 새 free 블록 footer를 기록했다
- [ ] 새 epilogue header를 기록했다
- [ ] 반환 전에 `coalesce`를 호출했다

검증 질문:

- [ ] 왜 old epilogue 자리에 새 free block header가 들어가는지 설명할 수 있다
- [ ] 왜 `extend_heap` 직후 `coalesce`하는지 설명할 수 있다

---

## 8. `coalesce` 구현 체크리스트

`coalesce`는 free된 블록 주변 상황을 보고 인접 free 블록을 합칩니다.

반드시 처리할 4가지 경우:

1. 이전 alloc, 다음 alloc
2. 이전 alloc, 다음 free
3. 이전 free, 다음 alloc
4. 이전 free, 다음 free

각 경우에서 해야 할 일:

- 현재 블록 크기 계산
- 이웃 블록들의 alloc 상태 확인
- 합쳐진 새 크기 계산
- header/footer 갱신
- 필요하면 `bp`를 이전 블록 시작점으로 이동

체크:

- [ ] 이전 블록 alloc 여부를 읽는 코드를 작성했다
- [ ] 다음 블록 alloc 여부를 읽는 코드를 작성했다
- [ ] case 1을 구현했다
- [ ] case 2를 구현했다
- [ ] case 3를 구현했다
- [ ] case 4를 구현했다
- [ ] 병합 후 올바른 `bp`를 반환한다

디버깅 체크:

- [ ] 병합 후 header와 footer 크기가 일치하는지 확인했다
- [ ] 이전 블록과 합친 경우 반환 포인터가 이전 블록을 가리키는지 확인했다

---

## 9. `find_fit` 구현 체크리스트

`find_fit`의 역할:

- 힙을 처음부터 순회하며
- `free` 상태이고
- 요청 크기 이상인
- 첫 번째 블록을 찾기

암묵적 리스트에서는 free 블록만 따로 저장하지 않으므로 전체 블록을 다 볼 수 있어야 합니다.

세부 단계:

1. 시작 블록부터 순회 시작
2. epilogue를 만날 때까지 반복
3. 현재 블록이 free인지 검사
4. 크기가 충분한지 검사
5. 맞으면 바로 반환
6. 끝까지 없으면 `NULL`

체크:

- [ ] 순회 시작 위치를 올바르게 잡았다
- [ ] epilogue에서 순회를 멈추게 했다
- [ ] `GET_ALLOC`로 free 여부를 검사한다
- [ ] `GET_SIZE`로 크기를 비교한다
- [ ] first fit 정책으로 첫 적합 블록을 반환한다
- [ ] 못 찾으면 `NULL`을 반환한다

---

## 10. `place` 구현 체크리스트

`place`의 역할:

- 찾은 free 블록에 실제 할당을 기록
- 남는 공간이 충분하면 split

세부 단계:

1. 현재 free 블록 크기 확인
2. 요청 크기와의 차이 계산
3. 남는 공간이 충분히 크면
   - 앞부분을 allocated block으로 기록
   - 뒷부분을 free block으로 기록
4. 남는 공간이 너무 작으면
   - 전체 블록을 allocated로 기록

체크:

- [ ] 현재 블록 크기를 읽는다
- [ ] 남는 공간 크기를 계산한다
- [ ] split 가능한 최소 크기 기준을 정했다
- [ ] split 가능한 경우 앞 블록 allocated 처리했다
- [ ] split 가능한 경우 뒤 블록 free 처리했다
- [ ] split 불가능하면 전체 블록 allocated 처리했다

디버깅 체크:

- [ ] split 후 뒤에 남은 free 블록의 header/footer가 정확한지 확인했다
- [ ] split 후 두 블록 크기 합이 원래 블록 크기와 같은지 확인했다

---

## 11. `mm_malloc` 구현 체크리스트

`mm_malloc`의 역할:

- 요청 크기를 보정해서 실제 필요한 블록 크기 계산
- 적당한 free 블록 탐색
- 있으면 배치
- 없으면 힙 확장 후 배치

세부 단계:

1. `size == 0` 처리
2. 정렬과 오버헤드를 포함한 `asize` 계산
3. `find_fit(asize)` 호출
4. 찾으면 `place(bp, asize)` 호출 후 반환
5. 못 찾으면 `extend_heap` 호출
6. 새 블록에 `place` 후 반환

체크:

- [ ] `size == 0`이면 `NULL` 반환 처리했다
- [ ] 최소 블록 크기를 반영해 `asize`를 계산한다
- [ ] 정렬 규칙이 `asize` 계산에 반영됐다
- [ ] `find_fit`를 호출한다
- [ ] 찾은 경우 `place`를 호출한다
- [ ] 못 찾은 경우 `extend_heap`를 호출한다
- [ ] `extend_heap` 실패 시 `NULL` 반환 처리했다

검증 질문:

- [ ] 사용자가 요청한 크기와 실제 블록 크기 `asize`가 왜 다른지 설명할 수 있다
- [ ] 왜 header/footer 오버헤드를 포함해서 계산해야 하는지 설명할 수 있다

---

## 12. `mm_free` 구현 체크리스트

`mm_free`의 역할:

- 블록을 free 상태로 바꿈
- 바로 `coalesce`

세부 단계:

1. 현재 블록 크기 읽기
2. header를 free로 기록
3. footer를 free로 기록
4. `coalesce(bp)` 호출

체크:

- [ ] `mm_free`에서 현재 블록 크기를 읽는다
- [ ] header를 free 상태로 바꾼다
- [ ] footer를 free 상태로 바꾼다
- [ ] `coalesce`를 호출한다

주의:

- allocated 블록과 함부로 합치지 않는다
- header/footer를 동시에 갱신한다

---

## 13. `mm_realloc` 구현 체크리스트

첫 구현에서는 단순 버전으로 충분합니다.

단순 구현 흐름:

1. 새 블록 `mm_malloc(size)`
2. 기존 데이터 복사
3. 기존 블록 `mm_free(ptr)`
4. 새 포인터 반환

추가 처리:

- `ptr == NULL`이면 `mm_malloc(size)`와 같게 처리
- `size == 0`이면 `mm_free(ptr)` 후 `NULL` 반환

체크:

- [ ] `ptr == NULL` 처리했다
- [ ] `size == 0` 처리했다
- [ ] 새 블록 할당 실패 처리했다
- [ ] 기존 블록 크기와 요청 크기 중 작은 쪽만 복사한다
- [ ] 복사 후 기존 블록을 free한다

주의:

- 처음에는 in-place 확장 최적화를 넣지 않는다
- 먼저 정답성을 확보한다

---

## 14. 구현 순서 체크리스트

아래 순서를 그대로 따르는 것을 추천합니다.

1. 상수 정의
2. 매크로 작성
3. 전역 포인터 선언
4. `mm_init`
5. `extend_heap`
6. `coalesce`
7. `find_fit`
8. `place`
9. `mm_malloc`
10. `mm_free`
11. `mm_realloc`

체크:

- [ ] 매크로부터 먼저 구현했다
- [ ] `mm_init`와 `extend_heap`이 먼저 동작한다
- [ ] `coalesce`를 단독으로 검증했다
- [ ] `find_fit`와 `place`를 분리해서 작성했다
- [ ] 마지막에 `mm_malloc`, `mm_free`, `mm_realloc`를 연결했다

---

## 15. 최소 디버깅 도구 체크리스트

가능하면 `mm_checkheap` 또는 디버깅 출력 함수를 직접 추가하는 것이 좋습니다.

최소한 아래를 검사할 수 있으면 좋습니다.

- 모든 블록이 정렬되어 있는가
- header와 footer 값이 일치하는가
- epilogue가 정상인가
- 연속 free 블록이 병합되지 않고 남아 있지 않은가
- 순회 중 힙 범위를 벗어나지 않는가

체크:

- [ ] 블록 순회 출력용 디버깅 함수가 있다
- [ ] header/footer 일치 여부를 검사할 수 있다
- [ ] 연속 free 블록이 남아 있는지 검사할 수 있다
- [ ] 필요할 때만 켜는 디버그 출력 방식이 있다

---

## 16. 테스트 순서 체크리스트

처음부터 전체 trace를 돌리지 말고 작은 것부터 갑니다.

추천 순서:

1. `short1-bal.rep`
2. `short2-bal.rep`
3. `coalescing-bal.rep`
4. 기본 trace 전체

예시:

```bash
cd /workspaces/malloc_lab_docker/malloc-lab
make
./mdriver -V -f short1-bal.rep
./mdriver -V -f short2-bal.rep
./mdriver -V -f traces/coalescing-bal.rep
./mdriver -v
```

체크:

- [ ] `short1-bal.rep`을 통과했다
- [ ] `short2-bal.rep`을 통과했다
- [ ] `coalescing-bal.rep`을 통과했다
- [ ] 전체 trace에서 비정상 종료 없이 동작한다

---

## 17. 자주 틀리는 포인트 체크리스트

아래는 매우 자주 발생하는 실수입니다.

- [ ] `bp`가 payload 포인터라는 점을 잊지 않았다
- [ ] header/footer 크기를 블록 전체 크기로 기록한다
- [ ] `size == 0` 요청을 처리했다
- [ ] `extend_heap` 후 epilogue를 다시 쓴다
- [ ] split 후 남은 블록이 너무 작으면 분할하지 않는다
- [ ] `coalesce` 후 반환 포인터를 잘못 넘기지 않는다
- [ ] `PREV_BLKP` 계산에서 이전 footer를 기준으로 본다는 점을 놓치지 않았다
- [ ] `find_fit` 순회 종료 조건을 epilogue로 잡았다
- [ ] 정렬 보정 계산이 틀리지 않았다
- [ ] `realloc`에서 복사 크기를 잘못 계산하지 않았다

---

## 18. 구현 완료 판단 기준

아래가 되면 1차 구현은 완료로 봐도 좋습니다.

- [ ] `mm_init`가 안정적으로 힙을 초기화한다
- [ ] `mm_malloc`이 free 블록을 찾아 재사용한다
- [ ] `mm_free` 후 같은 영역이 다시 사용될 수 있다
- [ ] 인접 free 블록이 병합된다
- [ ] 큰 free 블록은 split된다
- [ ] `short1`, `short2`, `coalescing` trace가 통과한다
- [ ] 전체 trace에서 최소한 정답성 오류 없이 돈다

---

## 19. 1차 구현이 끝난 뒤 다음 단계

첫 구현이 끝나면 다음 순서로 발전시키면 됩니다.

1. heap checker 강화
2. `realloc` 개선
3. first fit 성능 관찰
4. explicit free list로 전환 고려
5. segregated free list 검토

하지만 이 문서의 범위는 여기까지입니다.

지금 당장의 목표는:

- 포인터 산술이 맞고
- coalescing이 정확하고
- split이 정확하게 동작하는
- 첫 implicit free list allocator 완성

입니다.

---

## 20. 가장 짧은 실전 TODO

정말 최소 TODO만 다시 압축하면 다음입니다.

- [ ] 매크로 작성
- [ ] `mm_init`
- [ ] `extend_heap`
- [ ] `coalesce`
- [ ] `find_fit`
- [ ] `place`
- [ ] `mm_malloc`
- [ ] `mm_free`
- [ ] `mm_realloc`
- [ ] 작은 trace부터 통과

원하면 다음 단계로 이 체크리스트를 바탕으로 [/workspaces/malloc_lab_docker/malloc-lab/mm.c](/workspaces/malloc_lab_docker/malloc-lab/mm.c)의 함수 골격을 바로 같이 만들어갈 수 있습니다.
